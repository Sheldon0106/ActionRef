"""Publication-oriented patient-disjoint validation for secondary diseases.

This module orchestrates the frozen package. It does not reimplement Module 1,
Module 2, Module 3A, Module 3B, or the package bootstrap.
"""
import argparse
import dataclasses
import hashlib
import importlib.metadata
import json
import logging
import os
import platform
import re
import shutil
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import sklearn
import yaml

from universal_cutoff import (
    BootstrapConfig,
    CapacityConfig,
    Module2Config,
    apply_capacity,
    audit_cost_governance,
    bootstrap_module2,
    build_simple_r_guidance,
    build_threshold_table,
    evaluate_frozen_thresholds,
    evaluate_score,
    fit_behavior_thresholds,
    minimax_regret_cost_audit,
)


LEVELS = ["Low", "Mid", "High"]


def deterministic_patient_split(subject_ids, learning_fraction=0.70, seed=2026):
    """Return a reproducible patient assignment after deterministic sorting."""
    values = pd.Series(subject_ids).dropna().drop_duplicates().sort_values(kind="mergesort")
    ordered = values.to_numpy()
    if not len(ordered):
        raise ValueError("no nonmissing patient identifiers")
    rng = np.random.RandomState(int(seed))
    permuted = ordered[rng.permutation(len(ordered))]
    n_learning = int(np.floor(float(learning_fraction) * len(permuted)))
    learning = set(permuted[:n_learning].tolist())
    return {value: ("learning" if value in learning else "heldout") for value in ordered}


def fixed_threshold_patient_bootstrap(data, score_col, response_col, outcome_col,
                                      group_col, frozen_thresholds,
                                      n_bootstrap=200, seed=42):
    """Resample held-out patients while keeping learning-derived thresholds fixed."""
    base = data[[group_col, score_col, response_col, outcome_col]].dropna(subset=[group_col, score_col])
    groups = pd.Index(pd.unique(base[group_col]))
    if not len(groups):
        raise ValueError("held-out operating bootstrap has no patients")
    rng = np.random.RandomState(int(seed))
    rows = []
    for level, threshold in frozen_thresholds.items():
        if threshold is None or not np.isfinite(float(threshold)):
            continue
        frame = base.copy()
        frame["_alert"] = frame[score_col].astype(float) >= float(threshold)
        frame["_n"] = 1
        frame["_outcome_pos"] = frame[outcome_col].eq(1).astype(int)
        frame["_outcome_neg"] = frame[outcome_col].eq(0).astype(int)
        frame["_alert_response"] = (frame["_alert"] & frame[response_col].eq(1)).astype(int)
        frame["_alert_outcome_pos"] = (frame["_alert"] & frame[outcome_col].eq(1)).astype(int)
        frame["_alert_outcome_neg"] = (frame["_alert"] & frame[outcome_col].eq(0)).astype(int)
        frame["_alert_response_observed"] = (frame["_alert"] & frame[response_col].notna()).astype(int)
        agg = frame.groupby(group_col, sort=False)[[
            "_n", "_outcome_pos", "_outcome_neg", "_alert", "_alert_response",
            "_alert_outcome_pos", "_alert_outcome_neg", "_alert_response_observed",
        ]].sum().reindex(groups, fill_value=0).to_numpy(float)
        for replicate in range(int(n_bootstrap)):
            multiplicity = np.bincount(
                rng.randint(0, len(groups), size=len(groups)), minlength=len(groups)
            ).astype(float)
            totals = multiplicity @ agg
            n, outcome_pos, outcome_neg, alerts, responses, tp, fp, response_observed = totals
            fn = outcome_pos - tp
            tn = outcome_neg - fp
            rows.append({
                "replicate": replicate,
                "level": level,
                "frozen_threshold": float(threshold),
                "alert_count": alerts,
                "alert_fraction": _ratio(alerts, n),
                "response_positive_count": responses,
                "response_rate_among_alerts": _ratio(responses, response_observed),
                "outcome_positive_count_among_alerts": tp,
                "recall": _ratio(tp, outcome_pos),
                "FNR": _ratio(fn, outcome_pos),
                "specificity": _ratio(tn, outcome_neg),
                "FPR": _ratio(fp, outcome_neg),
                "PPV": _ratio(tp, tp + fp),
                "NPV": _ratio(tn, tn + fn),
                "missed_cases": fn,
            })
    return pd.DataFrame(rows)


def summarize_bootstrap(frame):
    metrics = [
        "alert_count", "alert_fraction", "response_positive_count",
        "response_rate_among_alerts", "outcome_positive_count_among_alerts",
        "recall", "FNR", "specificity", "FPR", "PPV", "NPV", "missed_cases",
    ]
    rows = []
    for level, group in frame.groupby("level", sort=False):
        for metric in metrics:
            values = pd.to_numeric(group[metric], errors="coerce").dropna()
            rows.append({
                "level": level,
                "metric": metric,
                "replicates": int(len(values)),
                "median": float(values.median()) if len(values) else np.nan,
                "CI_2_5": float(values.quantile(0.025)) if len(values) else np.nan,
                "CI_97_5": float(values.quantile(0.975)) if len(values) else np.nan,
            })
    return pd.DataFrame(rows)


def build_region_summary(data, score_col, response_col, outcome_col, components, anchors):
    available = anchors.loc[anchors.selected_threshold.notna(), ["level", "selected_threshold"]]
    mapping = dict(zip(available.level, available.selected_threshold.astype(float)))
    ordered = [(level, mapping[level]) for level in LEVELS if level in mapping]
    if not ordered:
        return pd.DataFrame()
    score = pd.to_numeric(data[score_col], errors="coerce")
    regions = []
    first_level, first_value = ordered[0]
    regions.append(("below {}".format(first_level), score < first_value))
    for index, (level, value) in enumerate(ordered):
        if index + 1 < len(ordered):
            next_level, next_value = ordered[index + 1]
            label = "{} to below {}".format(level, next_level)
            mask = (score >= value) & (score < next_value)
        else:
            label = "at or above {}".format(level)
            mask = score >= value
        regions.append((label, mask))
    rows = []
    total = int(score.notna().sum())
    for order, (label, mask) in enumerate(regions):
        group = data.loc[mask]
        row = {
            "region_order": order,
            "region": label,
            "encounters": int(len(group)),
            "encounter_fraction": _ratio(len(group), total),
            "outcome_events": int(group[outcome_col].eq(1).sum()),
            "outcome_prevalence": _mean_binary(group[outcome_col]),
            "response_events": int(group[response_col].eq(1).sum()),
            "response_rate": _mean_binary(group[response_col]),
            "workload_interpretation": "descriptive region volume; not a causal treatment effect",
        }
        for name, column in components.items():
            row["{}_rate".format(name)] = _mean_binary(group[column])
        rows.append(row)
    return pd.DataFrame(rows)


def local_curve_rows(curve, anchors):
    rows = []
    for anchor in anchors.itertuples(index=False):
        threshold = getattr(anchor, "selected_threshold")
        if pd.isna(threshold) or curve.empty:
            continue
        nearest = int(np.abs(curve.score.astype(float).to_numpy() - float(threshold)).argmin())
        for index in range(max(0, nearest - 1), min(len(curve), nearest + 2)):
            row = curve.iloc[index].to_dict()
            row.update(level=anchor.level, selected_threshold=float(threshold),
                       relative_bin_position=index - nearest)
            rows.append(row)
    return pd.DataFrame(rows)


def _ratio(numerator, denominator):
    return float(numerator / denominator) if denominator else np.nan


def _mean_binary(series):
    numeric = pd.to_numeric(series, errors="coerce")
    return float(numeric.mean()) if numeric.notna().any() else np.nan


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _is_relative_to(path, parent):
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _json_value(value):
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    raise TypeError("not JSON serializable: {!r}".format(type(value)))


def _clean_json(value):
    if dataclasses.is_dataclass(value):
        value = dataclasses.asdict(value)
    if isinstance(value, dict):
        return {str(key): _clean_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean_json(item) for item in value]
    if isinstance(value, np.ndarray):
        return [_clean_json(item) for item in value.tolist()]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def _write_json(path, value):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(_clean_json(value), handle, indent=2, default=_json_value, allow_nan=False)


def _package_version(root):
    try:
        return importlib.metadata.version("universal-cutoff")
    except importlib.metadata.PackageNotFoundError:
        text = (root / "pyproject.toml").read_text(encoding="utf-8")
        match = re.search(r'^version\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
        return match.group(1) if match else "unresolved"


def _cohort_rows(data, disease, partition, outcome_col, responses):
    rows = []
    patient_n = int(data.subject_id.nunique())
    encounter_n = int(len(data))
    for response_name, response_col in responses.items():
        rows.append({
            "disease": disease,
            "partition": partition,
            "response_definition": response_name,
            "patients": patient_n,
            "encounters": encounter_n,
            "outcome_events": int(data[outcome_col].eq(1).sum()),
            "outcome_prevalence": _mean_binary(data[outcome_col]),
            "response_events": int(data[response_col].eq(1).sum()),
            "response_prevalence": _mean_binary(data[response_col]),
            "missing_score": int(data._score_missing.sum()),
            "missing_outcome": int(data[outcome_col].isna().sum()),
            "missing_response": int(data[response_col].isna().sum()),
        })
    return rows


def _component_rows(data, disease, partition, components):
    return [{
        "disease": disease,
        "partition": partition,
        "component": name,
        "column": column,
        "positive_encounters": int(data[column].eq(1).sum()),
        "rate": _mean_binary(data[column]),
        "missing": int(data[column].isna().sum()),
    } for name, column in components.items()]


def _plot_curve(path, disease, response_name, result, anchors):
    curve = result.response_curve
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    ax.plot(curve.score, curve.observed_rate, marker="o", linewidth=1.2,
            color="#4678a8", label="Observed")
    ax.plot(curve.score, curve.isotonic_rate, linewidth=2.0,
            color="#c44e52", label="Isotonic")
    colors = {"Low": "#55a868", "Mid": "#8172b2", "High": "#dd8452"}
    for row in anchors.itertuples(index=False):
        if pd.notna(row.selected_threshold):
            ax.axvline(float(row.selected_threshold), color=colors[row.level],
                       linestyle="--", linewidth=1.2, label=row.level)
    ax.set(title="{}: {} learning response curve".format(disease, response_name),
           xlabel="Score", ylabel="Response rate")
    ax.set_ylim(0, 1)
    ax.legend(frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _prepare_data(path, spec):
    components = spec["components"]
    wanted = {"subject_id", spec["encounter_id"], spec["score"], spec["outcome"]}
    wanted.update(components.values())
    for response in spec["responses"].values():
        if response.get("stored_column"):
            wanted.add(response["stored_column"])
    available = set(pd.read_csv(path, nrows=0).columns)
    required = {"subject_id", spec["encounter_id"], spec["score"], spec["outcome"]}
    required.update(components.values())
    missing = sorted(required - available)
    if missing:
        raise ValueError("{} missing required columns: {}".format(path, missing))
    data = pd.read_csv(path, usecols=sorted(wanted & available), low_memory=False)
    if data.subject_id.isna().any():
        raise ValueError("patient identifier contains missing values")
    if data[spec["encounter_id"]].duplicated().any():
        raise ValueError("encounter identifier is not unique")
    for column in components.values():
        numeric = pd.to_numeric(data[column], errors="coerce").fillna(0).astype(int)
        if not numeric.isin([0, 1]).all():
            raise ValueError("component is not binary: {}".format(column))
        data[column] = numeric
    response_columns = {}
    response_checks = []
    for name, response in spec["responses"].items():
        derived_name = "_response_{}".format(name)
        source_columns = [components[key] for key in response["any_of"]]
        data[derived_name] = data[source_columns].eq(1).any(axis=1).astype(int)
        stored = response.get("stored_column")
        mismatches = None
        if stored and stored in data.columns:
            stored_values = pd.to_numeric(data[stored], errors="coerce").fillna(0).astype(int)
            mismatches = int((stored_values != data[derived_name]).sum())
            if mismatches:
                raise ValueError("stored response does not reproduce {}: {} mismatches".format(
                    name, mismatches))
        response_columns[name] = derived_name
        response_checks.append({
            "response_definition": name,
            "stored_column": stored,
            "derived_column": derived_name,
            "stored_column_present": bool(stored and stored in data.columns),
            "mismatches": mismatches,
            "definition": response["definition"],
            "role": response["role"],
            "limitation": response.get("limitation"),
        })
    data[spec["score"]] = pd.to_numeric(data[spec["score"]], errors="coerce")
    data[spec["outcome"]] = pd.to_numeric(data[spec["outcome"]], errors="coerce")
    data["_score_missing"] = data[spec["score"]].isna()
    return data, response_columns, response_checks


def _save_bootstrap(directory, result):
    frames = {
        "replicate_anchors.csv": result.anchors,
        "validated_full_anchors.csv": result.validated_full_anchors,
        "stability_summary.csv": result.stability_summary,
        "threshold_frequencies.csv": result.threshold_frequencies,
        "joint_tier_audit.csv": result.joint_tier_audit,
        "adjacent_gap_summary.csv": result.adjacent_gap_summary,
        "provenance_frequencies.csv": result.provenance_frequencies,
        "binning_stability.csv": result.binning_stability,
        "changepoint_support.csv": result.changepoint_support,
        "failures.csv": result.failures,
    }
    empty_schemas = {
        "changepoint_support.csv": [
            "cp", "bootstrap_support", "matching_replicates", "evaluated_replicates",
            "isotonic_rate_at_cp", "status",
        ],
        "failures.csv": ["replicate", "reason"],
    }
    for name, frame in frames.items():
        if frame.empty and not len(frame.columns) and name in empty_schemas:
            frame = pd.DataFrame(columns=empty_schemas[name])
        frame.to_csv(directory / name, index=False)
    _write_json(directory / "joint_summary.json", result.joint_summary)
    _write_json(directory / "bootstrap_config.json", result.config)


def run_analysis(args):
    root = Path(__file__).resolve().parents[1]
    config_path = Path(args.config).resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    result_root = Path(args.results_root).resolve()
    version = config["analysis_id"]
    disease_dirs = {name: result_root / name / "validation_v1" for name in config["diseases"]}
    combined_dir = result_root / version
    for path in list(disease_dirs.values()) + [combined_dir]:
        if path.exists() and any(path.iterdir()):
            raise SystemExit("refusing to overwrite nonempty validation output: {}".format(path))
    for path in list(disease_dirs.values()) + [combined_dir]:
        path.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(combined_dir / "run.log", encoding="utf-8"),
                  logging.StreamHandler(sys.stdout)],
    )
    log = logging.getLogger("publication_validation")
    command = " ".join(sys.argv)
    data_paths = {
        "aki": Path(args.aki_data).resolve(),
        "copd": Path(args.copd_data).resolve(),
        "pneumonia": Path(args.pneumonia_data).resolve(),
    }
    before_hashes = {name: _sha256(path) for name, path in data_paths.items()}
    loaded = {}
    for name, spec in config["diseases"].items():
        log.info("loading %s", name)
        loaded[name] = _prepare_data(data_paths[name], spec)

    subject_sets = {name: set(item[0].subject_id.unique().tolist()) for name, item in loaded.items()}
    reference = subject_sets["aki"]
    unequal = {name: len(values.symmetric_difference(reference))
               for name, values in subject_sets.items()}
    if any(unequal.values()):
        raise ValueError("disease patient universes differ: {}".format(unequal))
    assignment = deterministic_patient_split(
        sorted(reference), config["split"]["learning_fraction"], config["split"]["seed"])

    combined_cohorts = []
    combined_module1 = []
    combined_thresholds = []
    combined_operating = []
    combined_bootstrap = []
    combined_m3a = []
    combined_m3b = []
    disease_summaries = {}
    module2_config = Module2Config()
    bootstrap_config = BootstrapConfig(
        enabled=True,
        n_bootstrap=config["bootstrap"]["n_bootstrap"],
        group_col=config["bootstrap"]["group_column"],
        random_state=config["bootstrap"]["seed"],
        n_jobs=config["bootstrap"]["n_jobs"],
    )

    for disease, spec in config["diseases"].items():
        out_dir = disease_dirs[disease]
        data, responses, response_checks = loaded[disease]
        data["partition"] = data.subject_id.map(assignment)
        learning = data[data.partition.eq("learning")].copy()
        heldout = data[data.partition.eq("heldout")].copy()
        overlap = len(set(learning.subject_id).intersection(set(heldout.subject_id)))
        if overlap:
            raise RuntimeError("patient overlap detected for {}".format(disease))
        score_col, outcome_col = spec["score"], spec["outcome"]
        module1_rows = []
        calibrators = {}
        for partition, frame in (("learning", learning), ("heldout", heldout)):
            metrics, calibrator = evaluate_score(frame, score_col, outcome_col)
            metrics.update(disease=disease, partition=partition)
            module1_rows.append(metrics)
            calibrators[partition] = calibrator
            combined_cohorts.extend(_cohort_rows(
                frame, disease, partition, outcome_col, responses))
        module1_frame = pd.DataFrame(module1_rows)
        module1_frame.to_csv(out_dir / "module1_learning_heldout.csv", index=False)
        combined_module1.extend(module1_rows)
        components = spec["components"]
        component_frame = pd.DataFrame(
            _component_rows(learning, disease, "learning", components)
            + _component_rows(heldout, disease, "heldout", components)
        )
        component_frame.to_csv(out_dir / "component_summary.csv", index=False)
        pd.DataFrame(response_checks).to_csv(out_dir / "response_definition_checks.csv", index=False)
        bundle_summaries = {}

        for response_name, response_col in responses.items():
            log.info("%s/%s: fitting frozen Module 2", disease, response_name)
            bundle_dir = out_dir / response_name
            bundle_dir.mkdir(parents=True, exist_ok=True)
            behavior = fit_behavior_thresholds(
                learning, score_col, response_col, module2_config)
            behavior.anchors.to_csv(bundle_dir / "module2_point_anchors.csv", index=False)
            behavior.response_curve.to_csv(bundle_dir / "module2_response_curve.csv", index=False)
            behavior.structural_candidates.to_csv(
                bundle_dir / "module2_structural_candidates.csv", index=False)
            behavior.supported_changepoints.to_csv(
                bundle_dir / "module2_point_changepoints.csv", index=False)
            _write_json(bundle_dir / "module2_evidence_gate.json", behavior.evidence_gate)
            _write_json(bundle_dir / "module2_config.json", behavior.config)

            log.info("%s/%s: running %s grouped Module 2 bootstraps",
                     disease, response_name, bootstrap_config.n_bootstrap)
            boot = bootstrap_module2(
                learning, score_col, response_col, module2_config,
                bootstrap_config, behavior)
            bootstrap_dir = bundle_dir / "bootstrap"
            bootstrap_dir.mkdir(parents=True, exist_ok=True)
            _save_bootstrap(bootstrap_dir, boot)
            anchors = boot.validated_full_anchors.copy()
            anchors.to_csv(bundle_dir / "module2_frozen_anchors.csv", index=False)
            finite = anchors.loc[anchors.selected_threshold.notna()]
            frozen = dict(zip(finite.level, finite.selected_threshold.astype(float)))

            if frozen:
                held = evaluate_frozen_thresholds(
                    heldout, score_col, frozen,
                    response_col=response_col, outcome_col=outcome_col)
                operating = held.table.copy()
                operating["FNR"] = 1 - pd.to_numeric(operating["recall"], errors="coerce")
                operating["FPR"] = 1 - pd.to_numeric(operating["specificity"], errors="coerce")
                operating["threshold_provenance"] = operating.level.map(
                    anchors.set_index("level").provenance_label)
                operating["threshold_selected_type"] = operating.level.map(
                    anchors.set_index("level").selected_type)
                operating.to_csv(bundle_dir / "heldout_operating_metrics.csv", index=False)
                operating_boot = fixed_threshold_patient_bootstrap(
                    heldout, score_col, response_col, outcome_col, "subject_id", frozen,
                    config["heldout_operating_bootstrap"]["n_bootstrap"],
                    config["heldout_operating_bootstrap"]["seed"])
                operating_boot.to_csv(
                    bundle_dir / "heldout_operating_bootstrap_replicates.csv", index=False)
                operating_boot_summary = summarize_bootstrap(operating_boot)
                operating_boot_summary.to_csv(
                    bundle_dir / "heldout_operating_bootstrap_summary.csv", index=False)
                regions = build_region_summary(
                    heldout, score_col, response_col, outcome_col, components, anchors)
                regions.to_csv(bundle_dir / "heldout_regions.csv", index=False)
                local_curve_rows(behavior.response_curve, anchors).to_csv(
                    bundle_dir / "local_threshold_behavior.csv", index=False)
            else:
                operating = pd.DataFrame()
                operating_boot_summary = pd.DataFrame()
                pd.DataFrame([{
                    "status": "unavailable",
                    "reason": "frozen Module 2 produced no available reference",
                }]).to_csv(bundle_dir / "heldout_operating_metrics.csv", index=False)
                pd.DataFrame().to_csv(bundle_dir / "heldout_operating_bootstrap_replicates.csv", index=False)
                pd.DataFrame().to_csv(bundle_dir / "heldout_operating_bootstrap_summary.csv", index=False)
                pd.DataFrame().to_csv(bundle_dir / "heldout_regions.csv", index=False)
                pd.DataFrame().to_csv(bundle_dir / "local_threshold_behavior.csv", index=False)

            threshold_table = build_threshold_table(
                heldout, score_col, response_col=response_col, outcome_col=outcome_col)
            capacity_rows = []
            for fraction in config["module3a"]["capacity_fractions"]:
                k = int(np.floor(float(fraction) * threshold_table.policy_N))
                capacity = apply_capacity(
                    threshold_table, anchors,
                    CapacityConfig(K=k, period="held-out analysis cohort"))
                part = capacity.table.copy()
                part.insert(0, "K_fraction_requested", float(fraction))
                capacity_rows.append(part)
            capacity_frame = (pd.concat(capacity_rows, ignore_index=True, sort=False)
                              if capacity_rows else pd.DataFrame())
            capacity_frame.to_csv(bundle_dir / "module3a_capacity.csv", index=False)

            r_spec = config["module3b"]["scenario"]
            guidance = build_simple_r_guidance(
                disease=spec["display_name"],
                population=config["population"],
                intended_user="emergency-department clinical team",
                intended_use=spec["intended_use"],
                outcome=outcome_col,
                triggered_action=spec["triggered_action"],
                capacity_K=int(np.floor(0.10 * threshold_table.policy_N)),
                capacity_period="held-out analysis cohort",
                primary_R=float(r_spec["primary_R"]),
                plausible_range=tuple(r_spec["plausible_range"]),
                sensitivity_grid=list(r_spec["sensitivity_grid"]),
                stakeholder_perspective="prespecified analytical scenario",
                time_horizon=spec["outcome_horizon"],
                false_negative_consequences=["missed outcome-positive encounter"],
                false_positive_burdens=["additional alert and clinical review"],
                intervention_risks=["overtesting", "opportunity cost"],
                notes=r_spec["provenance"],
            )
            _write_json(bundle_dir / "module3b_r_guidance.json", guidance)
            m3b_rows, minimax_rows, strategy_rows, regret_rows = [], [], [], []
            for level, threshold in frozen.items():
                for r_value in guidance.recommended_R_grid:
                    audit = audit_cost_governance(
                        threshold_table, threshold, r_value, calibrators["learning"])
                    row = dict(audit.summary)
                    row.update(level=level,
                               threshold_provenance=anchors.set_index("level").loc[level, "provenance_label"],
                               lambda_FAE=audit.lambda_result.value,
                               lambda_boundary_risk=audit.lambda_result.boundary_risk,
                               lambda_status=audit.lambda_result.status,
                               lambda_reason=audit.lambda_result.reason)
                    m3b_rows.append(row)
                alert_count = int(operating.loc[operating.level.eq(level), "alert_count"].iloc[0])
                minimax = minimax_regret_cost_audit(
                    threshold_table, guidance.recommended_R_grid,
                    max_alert_count=alert_count)
                minimax_rows.append({
                    "level": level,
                    "behavior_threshold": float(threshold),
                    "max_alert_count": alert_count,
                    "selected_threshold": minimax.selected_threshold,
                    "selected_alert_count": minimax.selected_alert_count,
                    "maximum_regret_FAE": minimax.maximum_regret_FAE,
                    "maximum_regret_FAE_per_1000": minimax.maximum_regret_FAE_per_1000,
                    "status": minimax.status,
                    "interpretation_guard": minimax.interpretation_guard,
                })
                strategy = minimax.strategy_summary.copy()
                strategy.insert(0, "level", level)
                strategy_rows.append(strategy)
                regret = minimax.regret_matrix.copy()
                regret.insert(0, "level", level)
                regret_rows.append(regret)
            m3b_frame = pd.DataFrame(m3b_rows)
            m3b_frame.to_csv(bundle_dir / "module3b_scenario_audits.csv", index=False)
            pd.DataFrame(minimax_rows).to_csv(
                bundle_dir / "module3b_minimax_summary.csv", index=False)
            (pd.concat(strategy_rows, ignore_index=True) if strategy_rows else pd.DataFrame()).to_csv(
                bundle_dir / "module3b_minimax_strategies.csv", index=False)
            (pd.concat(regret_rows, ignore_index=True) if regret_rows else pd.DataFrame()).to_csv(
                bundle_dir / "module3b_minimax_regret_matrix.csv", index=False)
            _plot_curve(bundle_dir / "response_curve.png", spec["display_name"],
                        response_name, behavior, anchors)

            response_spec = spec["responses"][response_name]
            bundle_summary = {
                "role": response_spec["role"],
                "definition": response_spec["definition"],
                "limitation": response_spec.get("limitation"),
                "learning_response_prevalence": behavior.input_summary["response_prevalence"],
                "evidence_gate": behavior.evidence_gate,
                "thresholds": anchors.to_dict(orient="records"),
                "bootstrap_status": boot.status,
                "bootstrap_joint_summary": boot.joint_summary,
                "heldout_patients": int(heldout.subject_id.nunique()),
                "heldout_encounters": int(len(heldout)),
                "module3b_status": guidance.status,
                "module3b_confidence": guidance.confidence,
                "module3b_R_grid": guidance.recommended_R_grid,
            }
            bundle_summaries[response_name] = bundle_summary
            for row in anchors.to_dict(orient="records"):
                row.update(disease=disease, response_definition=response_name)
                combined_thresholds.append(row)
            for row in operating.to_dict(orient="records"):
                row.update(disease=disease, response_definition=response_name)
                combined_operating.append(row)
            for row in boot.stability_summary.to_dict(orient="records"):
                row.update(disease=disease, response_definition=response_name,
                           gate_pass_frequency=(float(boot.anchors.groupby("replicate").gate_passed.first().mean())
                                                if not boot.anchors.empty else np.nan),
                           complete_three_tier_probability=boot.joint_summary.get(
                               "complete_three_tier_probability"),
                           strict_ordering_probability=boot.joint_summary.get(
                               "strict_ordering_probability"),
                           adjacent_tier_collision_probability=boot.joint_summary.get(
                               "adjacent_tier_collision_probability"))
                combined_bootstrap.append(row)
            for row in capacity_frame.to_dict(orient="records"):
                row.update(disease=disease, response_definition=response_name)
                combined_m3a.append(row)
            for row in m3b_frame.to_dict(orient="records"):
                row.update(disease=disease, response_definition=response_name)
                combined_m3b.append(row)

        cohort_frame = pd.DataFrame(
            [row for row in combined_cohorts if row["disease"] == disease])
        cohort_frame["patient_overlap"] = overlap
        cohort_frame.to_csv(out_dir / "cohort_summary.csv", index=False)
        _write_json(out_dir / "summary.json", {
            "disease": disease,
            "display_name": spec["display_name"],
            "source_data": str(data_paths[disease]),
            "source_sha256": before_hashes[disease],
            "score": score_col,
            "outcome": outcome_col,
            "split": config["split"],
            "patient_overlap": overlap,
            "response_definition_checks": response_checks,
            "analyses": bundle_summaries,
            "interpretation": (
                "Patient-disjoint threshold-level validation within one MIMIC-IV-ED population; "
                "not external validation of the underlying score."
            ),
        })
        disease_summaries[disease] = bundle_summaries

    tables = {
        "cohort_summary.csv": pd.DataFrame(combined_cohorts),
        "module1_summary.csv": pd.DataFrame(combined_module1),
        "threshold_summary.csv": pd.DataFrame(combined_thresholds),
        "heldout_operating_summary.csv": pd.DataFrame(combined_operating),
        "module2_bootstrap_summary.csv": pd.DataFrame(combined_bootstrap),
        "module3a_summary.csv": pd.DataFrame(combined_m3a),
        "module3b_scenario_summary.csv": pd.DataFrame(combined_m3b),
    }
    for filename, frame in tables.items():
        frame.to_csv(combined_dir / filename, index=False)
    shutil.copyfile(config_path, combined_dir / "config_snapshot.yaml")

    after_hashes = {name: _sha256(path) for name, path in data_paths.items()}
    unchanged = {name: before_hashes[name] == after_hashes[name] for name in before_hashes}
    if not all(unchanged.values()):
        raise RuntimeError("a source data hash changed during execution: {}".format(unchanged))

    manifest = {
        "analysis_id": version,
        "command": command,
        "package": {
            "name": "universal-cutoff",
            "version": _package_version(root),
            "contract": "frozen v0.3/V7",
            "source_root": str(root),
            "git_commit": None,
            "git_note": "package directory is not a Git worktree",
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
            "pyyaml": yaml.__version__,
            "matplotlib": matplotlib.__version__,
        },
        "inputs": {
            name: {
                "path": str(path),
                "sha256_before": before_hashes[name],
                "sha256_after": after_hashes[name],
                "unchanged": unchanged[name],
                "bytes": path.stat().st_size,
                "modified": pd.Timestamp(path.stat().st_mtime, unit="s").isoformat(),
            } for name, path in data_paths.items()
        },
        "split": config["split"],
        "module2_config": module2_config.snapshot(),
        "module2_bootstrap": dataclasses.asdict(bootstrap_config),
        "heldout_operating_bootstrap": config["heldout_operating_bootstrap"],
        "module3a": config["module3a"],
        "module3b": config["module3b"],
        "patient_universe_symmetric_difference_vs_aki": unequal,
        "patient_membership_exported": False,
        "claims_guard": (
            "Supports procedural portability and patient-disjoint threshold-level validation; "
            "does not establish external score validation, causal benefit, universal thresholds, "
            "monetary savings, or clinical effectiveness."
        ),
    }
    combined_summary = {
        "analysis_id": version,
        "diseases": disease_summaries,
        "source_hashes_unchanged": unchanged,
        "patient_overlap_within_each_disease": 0,
        "patient_universe_symmetric_difference_vs_aki": unequal,
        "interpretation": manifest["claims_guard"],
    }
    _write_json(combined_dir / "summary.json", combined_summary)
    log.info("validation completed successfully")
    for handler in logging.getLogger().handlers:
        handler.flush()

    output_hashes = {}
    for path in sorted(result_root.rglob("*")):
        if path.is_file() and (
                _is_relative_to(path, combined_dir)
                or any(_is_relative_to(path, directory) for directory in disease_dirs.values())):
            if path.name != "manifest.json":
                output_hashes[str(path.relative_to(result_root))] = _sha256(path)
    manifest["output_sha256"] = output_hashes
    _write_json(combined_dir / "manifest.json", manifest)
    return disease_summaries


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--aki-data", required=True)
    parser.add_argument("--copd-data", required=True)
    parser.add_argument("--pneumonia-data", required=True)
    parser.add_argument("--results-root", default="results")
    run_analysis(parser.parse_args())
