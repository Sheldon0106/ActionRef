"""Module 2 resampling wrappers. Point estimation never calls this module."""
from dataclasses import asdict
from typing import Optional

import numpy as np
import pandas as pd

from .config import BootstrapConfig, Module2Config
from .exceptions import InputValidationError
from .module2 import derive_semantic_anchors, fit_behavior_thresholds
from .results import BootstrapResult, Module2Result


def _empty_result(status, config, failures=None):
    return BootstrapResult(
        status=status,
        anchors=pd.DataFrame(),
        validated_full_anchors=pd.DataFrame(),
        stability_summary=pd.DataFrame(),
        threshold_frequencies=pd.DataFrame(),
        joint_tier_audit=pd.DataFrame(),
        joint_summary={},
        adjacent_gap_summary=pd.DataFrame(),
        provenance_frequencies=pd.DataFrame(),
        binning_stability=pd.DataFrame(),
        changepoint_support=pd.DataFrame(),
        failures=pd.DataFrame() if failures is None else failures,
        config=asdict(config),
    )


def _resample(data, group_col, rng):
    if group_col is None:
        return data.iloc[rng.randint(0, len(data), len(data))].copy()
    if group_col not in data.columns:
        raise InputValidationError("bootstrap group_col is missing: {}".format(group_col))
    base = data[data[group_col].notna()].copy()
    groups = pd.unique(base[group_col])
    if not len(groups):
        raise InputValidationError("bootstrap has no nonmissing groups")
    draws = pd.DataFrame({group_col: rng.choice(groups, size=len(groups), replace=True),
                          "_bootstrap_draw": np.arange(len(groups))})
    return draws.merge(base, on=group_col, how="left", sort=False)


def bootstrap_module2(data: pd.DataFrame, score_col: str, response_col: str,
                      module2: Optional[Module2Config] = None,
                      bootstrap: Optional[BootstrapConfig] = None,
                      full_result: Optional[Module2Result] = None) -> BootstrapResult:
    module2 = module2 or Module2Config()
    bootstrap = bootstrap or BootstrapConfig()
    if not bootstrap.enabled:
        return _empty_result("disabled", bootstrap)
    if bootstrap.n_jobs != 1:
        execution_note = "n_jobs is recorded; bootstrap executes sequentially in this release"
    else:
        execution_note = "sequential"
    full_result = full_result or fit_behavior_thresholds(data, score_col, response_col, module2)
    rng = np.random.RandomState(bootstrap.random_state)
    anchor_rows, cp_rows, joint_rows, failure_rows = [], [], [], []
    for replicate in range(int(bootstrap.n_bootstrap)):
        try:
            sampled = _resample(data, bootstrap.group_col, rng)
            result = fit_behavior_thresholds(sampled, score_col, response_col, module2)
            anchors = result.anchors.copy()
            anchors.insert(0, "replicate", replicate)
            anchors["bin_width"] = result.binning["bin_width"]
            anchors["valid_bin_count"] = len(result.response_curve)
            anchors["gate_passed"] = result.evidence_gate["passed"]
            anchor_rows.append(anchors)
            cps = result.supported_changepoints.copy()
            if not cps.empty:
                cps.insert(0, "replicate", replicate)
                cp_rows.append(cps)
            values = anchors.set_index("level").selected_threshold
            low, mid, high = (values.get("Low", np.nan), values.get("Mid", np.nan), values.get("High", np.nan))
            complete = bool(np.isfinite(low) and np.isfinite(mid) and np.isfinite(high))
            joint_rows.append({
                "replicate": replicate,
                "complete_three_tier": complete,
                "strict_ordering": bool(complete and low < mid < high),
                "adjacent_tier_collision": bool(complete and (np.isclose(low, mid) or np.isclose(mid, high))),
                "low_mid_gap": float(mid - low) if complete else np.nan,
                "mid_high_gap": float(high - mid) if complete else np.nan,
            })
        except Exception as exc:
            failure_rows.append({"replicate": replicate, "reason": repr(exc)})
    anchors = pd.concat(anchor_rows, ignore_index=True, sort=False) if anchor_rows else pd.DataFrame()
    replicate_cps = pd.concat(cp_rows, ignore_index=True, sort=False) if cp_rows else pd.DataFrame()
    failures = pd.DataFrame(failure_rows)
    summary_rows, frequency_rows = [], []
    for level in ["Low", "Mid", "High"]:
        source = anchors[anchors.level == level] if not anchors.empty else pd.DataFrame()
        values = pd.to_numeric(source.get("selected_threshold", pd.Series(dtype=float)), errors="coerce").dropna()
        full = full_result.anchors[full_result.anchors.level == level].iloc[0]
        full_threshold = full.selected_threshold
        total = int(bootstrap.n_bootstrap)
        summary_rows.append({
            "level": level,
            "full_data_threshold": full_threshold,
            "requested_replicates": total,
            "available_replicates": int(len(values)),
            "failed_replicates": int(len(failures)),
            "availability_probability": float(len(values) / total),
            "median": float(values.median()) if len(values) else np.nan,
            "CI_2_5": float(values.quantile(.025)) if len(values) else np.nan,
            "CI_97_5": float(values.quantile(.975)) if len(values) else np.nan,
            "exact_match_probability": float(np.isclose(values, full_threshold).mean()) if len(values) and np.isfinite(full_threshold) else np.nan,
            "within_one_bin_probability": (
                float((np.abs(values - float(full_threshold)) <= full_result.binning["bin_width"] + 1e-12).mean())
                if len(values) and np.isfinite(full_threshold) else np.nan
            ),
        })
        if len(values):
            for threshold, count in values.value_counts().sort_index().items():
                frequency_rows.append({"level": level, "threshold": float(threshold),
                                       "count": int(count), "probability": float(count / total)})
    audit = pd.DataFrame(joint_rows)
    requested = int(bootstrap.n_bootstrap)
    if len(audit):
        joint_summary = {
            "requested_replicates": requested,
            "evaluated_replicates": int(len(audit)),
            "failed_replicates": int(len(failures)),
            "complete_three_tier_probability": float(audit.complete_three_tier.mean()),
            "strict_ordering_probability": float(audit.strict_ordering.mean()),
            "adjacent_tier_collision_probability": float(audit.adjacent_tier_collision.mean()),
        }
    else:
        joint_summary = {
            "requested_replicates": requested,
            "evaluated_replicates": 0,
            "failed_replicates": int(len(failures)),
            "complete_three_tier_probability": np.nan,
            "strict_ordering_probability": np.nan,
            "adjacent_tier_collision_probability": np.nan,
        }
    gap_rows = []
    for name in ["low_mid_gap", "mid_high_gap"]:
        values = pd.to_numeric(audit.get(name, pd.Series(dtype=float)), errors="coerce").dropna()
        gap_rows.append({
            "gap": name,
            "available_replicates": int(len(values)),
            "median": float(values.median()) if len(values) else np.nan,
            "CI_2_5": float(values.quantile(.025)) if len(values) else np.nan,
            "CI_97_5": float(values.quantile(.975)) if len(values) else np.nan,
            "nonpositive_probability": float((values <= 0).mean()) if len(values) else np.nan,
        })
    provenance_rows = []
    provenance_columns = ["level", "provenance_tier", "selected_type", "structural_status"]
    if not anchors.empty and set(provenance_columns).issubset(anchors.columns):
        counts = anchors.groupby(provenance_columns, dropna=False).size().reset_index(name="count")
        for row in counts.itertuples(index=False):
            provenance_rows.append({
                "level": row.level,
                "provenance_tier": row.provenance_tier,
                "selected_type": row.selected_type,
                "structural_status": row.structural_status,
                "count": int(row.count),
                "probability": float(row.count / requested),
            })
    binning_rows = []
    if not anchors.empty and {"replicate", "bin_width", "valid_bin_count"}.issubset(anchors.columns):
        replicate_binning = anchors[["replicate", "bin_width", "valid_bin_count"]].drop_duplicates("replicate")
        counts = replicate_binning.groupby(["bin_width", "valid_bin_count"], dropna=False).size()
        for (bin_width, valid_bin_count), count in counts.items():
            binning_rows.append({
                "bin_width": float(bin_width),
                "valid_bin_count": int(valid_bin_count),
                "count": int(count),
                "probability": float(count / requested),
            })
    cp_support_rows = []
    full_cps = full_result.supported_changepoints
    evaluated_replicates = int(len(audit))
    if full_cps is not None and not full_cps.empty:
        tolerance = module2.cp_support_tolerance_bins * full_result.binning["bin_width"]
        for row in full_cps.itertuples(index=False):
            if replicate_cps.empty or evaluated_replicates == 0:
                matching_replicates = 0
            else:
                matching_replicates = int(replicate_cps.loc[
                    np.abs(pd.to_numeric(replicate_cps.cp, errors="coerce") - float(row.cp))
                    <= tolerance + 1e-12,
                    "replicate",
                ].nunique())
            support = (float(matching_replicates / evaluated_replicates)
                       if evaluated_replicates else np.nan)
            cp_support_rows.append({
                "cp": float(row.cp),
                "bootstrap_support": support,
                "matching_replicates": matching_replicates,
                "evaluated_replicates": evaluated_replicates,
                "isotonic_rate_at_cp": float(row.isotonic_rate_at_cp),
                "status": ("supported" if np.isfinite(support)
                           and support >= module2.min_cp_bootstrap_support
                           else "unsupported_bootstrap"),
            })
    cp_support = pd.DataFrame(cp_support_rows)
    validated_anchors = derive_semantic_anchors(
        full_result.response_curve,
        data[score_col],
        full_result.input_summary["response_prevalence"],
        cp_support,
        full_result.binning["bin_width"],
        full_result.evidence_gate,
        module2,
    )
    return BootstrapResult(
        status="completed",
        anchors=anchors,
        validated_full_anchors=validated_anchors,
        stability_summary=pd.DataFrame(summary_rows),
        threshold_frequencies=pd.DataFrame(frequency_rows),
        joint_tier_audit=audit,
        joint_summary=joint_summary,
        adjacent_gap_summary=pd.DataFrame(gap_rows),
        provenance_frequencies=pd.DataFrame(provenance_rows),
        binning_stability=pd.DataFrame(binning_rows),
        changepoint_support=cp_support,
        failures=failures,
        config=dict(asdict(bootstrap), execution_note=execution_note,
                    estimated_module2_fits=int(bootstrap.n_bootstrap) + 1),
    )
