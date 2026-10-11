"""Final semantic-first ActionRef simulation validation.

This additive validation preserves the scenario definitions, sample sizes,
Monte Carlo replicates, and random seeds from
``simulation_ablation_threshold_governance_v2_structural_refinement.ipynb``
while replacing its self-contained Module 2 implementation with the frozen
``universal_cutoff`` package implementation.

The script writes a new, non-overwriting, versioned output bundle. It does not
modify the historical notebooks, package source, clinical data, or prior
outputs.
"""

from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT
PACKAGE_SRC = PACKAGE_ROOT / "src"
sys.path.insert(0, str(PACKAGE_SRC))

from universal_cutoff.bootstrap import bootstrap_module2  # noqa: E402
from universal_cutoff.config import BootstrapConfig, Module2Config  # noqa: E402
from universal_cutoff.module2 import fit_behavior_thresholds  # noqa: E402
from universal_cutoff.module3b import audit_cost_governance  # noqa: E402
from universal_cutoff.threshold_table import build_threshold_table  # noqa: E402


RANDOM_STATE = 20260802
N_REPLICATES = 25
CP_BOOTSTRAP_REPS_MAIN = 10
N_SELECTED_SAMPLE_BOOTSTRAP = 40
CP_BOOTSTRAP_REPS_SELECTED = 5
ORACLE_N = 200_000
ORACLE_GRID = np.linspace(0, 100, 2001)
SIM_R_VALUES = [5.0, 14.05, 15.0, 20.0]
PRIMARY_R = 14.05
HISTORICAL_AUXILIARY_R = 15.0
CP_RECOVERY_TOLERANCE_BINS = 2.0

MODULE2_CONFIG = Module2Config()

READINESS_CRITERIA = {
    "flat_null_threshold_availability_max": 0.10,
    "flat_null_false_cp_rate_max": 0.10,
    "piecewise_cp_recall_min_legacy_provisional": 0.70,
    "low_ceiling_attainability_accuracy_min": 0.90,
    "validated_vs_point_mid_mae_margin": 0.50,
    "inclusive_governance_accuracy_min": 0.75,
    "cp_movement_rate_required": 0.0,
}


SCENARIOS = {
    "aligned_sigmoid": {
        "description": "Smooth high-ceiling response and outcome risk rise in a similar region.",
        "response_kind": "sigmoid", "response_center": 45.0, "response_scale": 8.0,
        "response_floor": 0.04, "response_ceiling": 0.92,
        "outcome_center": 40.0, "outcome_scale": 9.0,
        "outcome_floor": 0.01, "outcome_ceiling": 0.28,
        "true_cps": [], "governance_scope": "evaluable",
    },
    "one_changepoint": {
        "description": "Continuous monotone response with one true slope change near the Mid anchor.",
        "response_kind": "piecewise", "response_knots": [0.0, 45.0, 100.0],
        "response_values": [0.02, 0.55, 0.95],
        "outcome_center": 44.0, "outcome_scale": 9.0,
        "outcome_floor": 0.01, "outcome_ceiling": 0.28,
        "true_cps": [45.0], "governance_scope": "evaluable",
    },
    "two_changepoints": {
        "description": "Continuous monotone response with two true slope changes.",
        "response_kind": "piecewise", "response_knots": [0.0, 30.0, 50.0, 100.0],
        "response_values": [0.03, 0.12, 0.58, 0.92],
        "outcome_center": 46.0, "outcome_scale": 10.0,
        "outcome_floor": 0.01, "outcome_ceiling": 0.30,
        # Preserved exactly from the v2 scenario registry, including 55 rather than 50.
        "true_cps": [30.0, 55.0], "governance_scope": "evaluable",
    },
    "low_ceiling": {
        "description": "Response ceiling below 50%; absolute T50/T80 must be unreachable.",
        "response_kind": "sigmoid", "response_center": 50.0, "response_scale": 9.0,
        "response_floor": 0.03, "response_ceiling": 0.28,
        "outcome_center": 45.0, "outcome_scale": 9.0,
        "outcome_floor": 0.01, "outcome_ceiling": 0.28,
        "true_cps": [], "governance_scope": "evaluable",
    },
    "flat_behavior_null": {
        "description": "Response is unrelated to score while outcome risk still rises.",
        "response_kind": "flat", "response_level": 0.18,
        "outcome_center": 45.0, "outcome_scale": 9.0,
        "outcome_floor": 0.01, "outcome_ceiling": 0.28,
        "true_cps": [], "governance_scope": "abstain",
    },
    "behavior_too_inclusive": {
        "description": "Clinician response rises early while outcome risk rises later.",
        "response_kind": "sigmoid", "response_center": 40.0, "response_scale": 8.0,
        "response_floor": 0.04, "response_ceiling": 0.88,
        "outcome_center": 60.0, "outcome_scale": 8.0,
        "outcome_floor": 0.01, "outcome_ceiling": 0.30,
        "true_cps": [], "governance_scope": "evaluable",
    },
    "behavior_too_conservative": {
        "description": "Clinician response rises late while outcome risk rises earlier.",
        "response_kind": "sigmoid", "response_center": 58.0, "response_scale": 8.0,
        "response_floor": 0.04, "response_ceiling": 0.92,
        "outcome_center": 31.0, "outcome_scale": 8.0,
        "outcome_floor": 0.01, "outcome_ceiling": 0.30,
        "true_cps": [], "governance_scope": "one-sided limitation",
    },
    "high_noise_monotone": {
        "description": "Smooth monotone high-ceiling response under stronger noise stress.",
        "response_kind": "sigmoid", "response_center": 48.0, "response_scale": 11.0,
        "response_floor": 0.05, "response_ceiling": 0.88,
        "outcome_center": 43.0, "outcome_scale": 10.0,
        "outcome_floor": 0.01, "outcome_ceiling": 0.28,
        "true_cps": [], "governance_scope": "evaluable",
    },
}


SIMULATION_CONDITIONS = {
    "baseline": {"n": 6000, "score_round_to": None, "response_flip": 0.00, "outcome_flip": 0.00},
    "low_sample": {"n": 2000, "score_round_to": None, "response_flip": 0.00, "outcome_flip": 0.00},
    "tied_scores": {"n": 6000, "score_round_to": 5.0, "response_flip": 0.00, "outcome_flip": 0.00},
    "label_noise": {"n": 6000, "score_round_to": None, "response_flip": 0.12, "outcome_flip": 0.04},
}


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(chunk_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def jsonable(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, Path):
        return str(value)
    raise TypeError(type(value).__name__)


def expit_stable(x):
    x = np.asarray(x, dtype=float)
    out = np.empty_like(x)
    positive = x >= 0
    out[positive] = 1 / (1 + np.exp(-x[positive]))
    exp_x = np.exp(x[~positive])
    out[~positive] = exp_x / (1 + exp_x)
    return out


def response_probability(score, scenario):
    cfg = SCENARIOS[scenario]
    x = np.asarray(score, dtype=float)
    if cfg["response_kind"] == "sigmoid":
        base = expit_stable((x - cfg["response_center"]) / cfg["response_scale"])
        return cfg["response_floor"] + (cfg["response_ceiling"] - cfg["response_floor"]) * base
    if cfg["response_kind"] == "piecewise":
        return np.interp(x, cfg["response_knots"], cfg["response_values"])
    if cfg["response_kind"] == "flat":
        return np.full_like(x, float(cfg["response_level"]), dtype=float)
    raise ValueError(cfg["response_kind"])


def outcome_probability(score, scenario):
    cfg = SCENARIOS[scenario]
    x = np.asarray(score, dtype=float)
    base = expit_stable((x - cfg["outcome_center"]) / cfg["outcome_scale"])
    return cfg["outcome_floor"] + (cfg["outcome_ceiling"] - cfg["outcome_floor"]) * base


def apply_symmetric_label_noise(probability, flip_probability):
    probability = np.asarray(probability, dtype=float)
    q = float(flip_probability)
    return q + (1 - 2 * q) * probability


def draw_scores(rng, n, round_to=None):
    mixture = rng.binomial(1, 0.90, size=n)
    score = 100 * np.where(
        mixture == 1,
        rng.beta(2.2, 3.5, size=n),
        rng.beta(4.0, 2.2, size=n),
    )
    if round_to is not None:
        score = np.round(score / float(round_to)) * float(round_to)
    return np.clip(score, 0, 100)


def simulate_dataset(scenario, condition, seed):
    rng = np.random.default_rng(int(seed))
    cfg = SIMULATION_CONDITIONS[condition]
    score = draw_scores(rng, int(cfg["n"]), cfg["score_round_to"])
    response_p = apply_symmetric_label_noise(
        response_probability(score, scenario), cfg["response_flip"]
    )
    outcome_p = apply_symmetric_label_noise(
        outcome_probability(score, scenario), cfg["outcome_flip"]
    )
    return pd.DataFrame({
        "subject_id": np.arange(len(score), dtype=int),
        "score": score,
        "response": rng.binomial(1, response_p).astype(int),
        "outcome": rng.binomial(1, outcome_p).astype(int),
        "true_response_probability": response_p,
        "true_outcome_probability": outcome_p,
    })


def first_crossing(score_grid, probabilities, target):
    eligible = np.flatnonzero(np.asarray(probabilities) >= float(target) - 1e-12)
    return float(score_grid[eligible[0]]) if len(eligible) else np.nan


def operationalize(raw_threshold, observed_scores):
    if not np.isfinite(raw_threshold):
        return np.nan
    observed = np.sort(np.unique(np.asarray(observed_scores, dtype=float)))
    candidates = observed[observed >= raw_threshold - 1e-12]
    return float(candidates[0]) if len(candidates) else np.nan


def enforce_final_order_and_representatives(rows):
    table = pd.DataFrame(rows)
    values = table.set_index("level")["threshold"].to_dict()
    low = values.get("Low", np.nan)
    mid = values.get("Mid", np.nan)
    high = values.get("High", np.nan)
    if np.isfinite(low) and np.isfinite(mid) and mid < low - 1e-12:
        table.loc[table.level == "Mid", "threshold"] = np.nan
    mid = table.loc[table.level == "Mid", "threshold"].iloc[0]
    reference = mid if np.isfinite(mid) else low
    if np.isfinite(reference) and np.isfinite(high) and high < reference - 1e-12:
        table.loc[table.level == "High", "threshold"] = np.nan
    table["operational_representative"] = False
    used = []
    priority = {"Mid": 1, "Low": 2, "High": 3}
    for idx in table.sort_values("level", key=lambda x: x.map(priority)).index:
        threshold = table.loc[idx, "threshold"]
        if np.isfinite(threshold) and not any(np.isclose(threshold, old) for old in used):
            table.loc[idx, "operational_representative"] = True
            used.append(float(threshold))
    return table


def oracle_semantic_truth(scenario, condition, score_sample):
    cfg = SIMULATION_CONDITIONS[condition]
    grid_p = apply_symmetric_label_noise(
        response_probability(ORACLE_GRID, scenario), cfg["response_flip"]
    )
    sample_p = apply_symmetric_label_noise(
        response_probability(score_sample, scenario), cfg["response_flip"]
    )
    p_min, p_max = float(grid_p.min()), float(grid_p.max())
    overall = float(sample_p.mean())
    if scenario == "flat_behavior_null":
        return pd.DataFrame([
            {"level": level, "threshold": np.nan, "anchor_family": "abstention",
             "absolute_attainable": False, "operational_representative": False}
            for level in ["Low", "Mid", "High"]
        ]), grid_p
    rows = []
    for level, absolute, fraction in [
        ("Low", overall, None), ("Mid", 0.50, 0.50), ("High", 0.80, 0.80)
    ]:
        attainable = p_min - 1e-12 <= absolute <= p_max + 1e-12
        if not attainable and level == "Low":
            rows.append({"level": level, "threshold": np.nan,
                         "anchor_family": "absolute", "absolute_attainable": False})
            continue
        if attainable:
            target, family = absolute, "absolute"
        else:
            target, family = p_min + fraction * (p_max - p_min), "relative"
        raw = first_crossing(ORACLE_GRID, grid_p, target)
        rows.append({
            "level": level,
            "threshold": operationalize(raw, score_sample),
            "anchor_family": family,
            "absolute_attainable": bool(attainable),
        })
    return enforce_final_order_and_representatives(rows), grid_p


def cp_recovery_metrics(estimated_cps, true_cps, tolerance):
    estimated = [float(x) for x in estimated_cps if np.isfinite(x)]
    truth = [float(x) for x in true_cps if np.isfinite(x)]
    if truth:
        matched_errors = []
        for target in truth:
            distances = [abs(value - target) for value in estimated]
            if distances and min(distances) <= tolerance + 1e-12:
                matched_errors.append(min(distances))
        recall = len(matched_errors) / len(truth)
        mean_error = float(np.mean(matched_errors)) if matched_errors else np.nan
        false_any = bool(any(min(abs(value - target) for target in truth) > tolerance for value in estimated))
    else:
        recall = np.nan
        mean_error = np.nan
        false_any = bool(estimated)
    return recall, mean_error, false_any


def anchor_values(anchors):
    indexed = anchors.set_index("level")
    return {level: float(indexed.loc[level, "selected_threshold"])
            if level in indexed.index and pd.notna(indexed.loc[level, "selected_threshold"])
            else np.nan for level in ["Low", "Mid", "High"]}


def classify_anchor_set(anchors):
    values = anchor_values(anchors)
    available = [values[level] for level in ["Low", "Mid", "High"] if np.isfinite(values[level])]
    collision = len(available) != len({round(value, 12) for value in available})
    complete = all(np.isfinite(values[level]) for level in ["Low", "Mid", "High"])
    strict = bool(complete and values["Low"] < values["Mid"] < values["High"])
    return values, complete, strict, collision


def governance_audit(table_result, behavior_threshold, r_value):
    if not np.isfinite(behavior_threshold):
        return None
    return audit_cost_governance(table_result, float(behavior_threshold), float(r_value), None)


def summarize_threshold(group):
    errors = group.absolute_error.dropna()
    return pd.Series({
        "replicates": group.replicate.nunique(),
        "estimated_availability_rate": group.estimated_available.mean(),
        "availability_accuracy": group.availability_correct.mean(),
        "MAE": errors.mean() if len(errors) else np.nan,
        "median_absolute_error": errors.median() if len(errors) else np.nan,
        "within_one_bin_rate": group.within_one_bin.dropna().mean()
        if group.within_one_bin.notna().any() else np.nan,
    })


def summarize_governance(group):
    oracle_class = group.oracle_classification.dropna()
    return pd.Series({
        "replicates": group.replicate.nunique(),
        "oracle_classification": oracle_class.mode().iloc[0] if len(oracle_class) else None,
        "oracle_reference_classification_accuracy": group.oracle_reference_classification_correct.mean(),
        "end_to_end_classification_accuracy": group.end_to_end_classification_correct.mean(),
        "correct_abstention_rate": group.correct_abstention.mean(),
        "oracle_comparator_MAE": np.nanmean(np.abs(group.sample_oracle_comparator - group.oracle_comparator))
        if group.oracle_comparator.notna().any() else np.nan,
        "end_to_end_comparator_MAE": np.nanmean(np.abs(group.end_to_end_comparator - group.oracle_comparator))
        if group.oracle_comparator.notna().any() else np.nan,
        "oracle_excess_FAE_per_1000": group.oracle_excess_FAE_per_1000.mean(),
        "mean_end_to_end_excess_FAE_per_1000": group.end_to_end_excess_FAE_per_1000.mean(),
    })


def main():
    source_paths = [
        Path(__file__).resolve(),
        ROOT / "simulations" / "eight_scenarios" / "config.json",
        PACKAGE_SRC / "universal_cutoff" / "config.py",
        PACKAGE_SRC / "universal_cutoff" / "module2.py",
        PACKAGE_SRC / "universal_cutoff" / "bootstrap.py",
        PACKAGE_SRC / "universal_cutoff" / "module3b.py",
        PACKAGE_SRC / "universal_cutoff" / "threshold_table.py",
    ]
    source_registry = [
        {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}
        for path in source_paths
    ]
    config = {
        "analysis": "final semantic-first ActionRef simulation validation",
        "historical_design_source": str(source_paths[1]),
        "random_state": RANDOM_STATE,
        "monte_carlo_replicates_per_scenario_condition": N_REPLICATES,
        "main_cp_bootstrap_replicates": CP_BOOTSTRAP_REPS_MAIN,
        "selected_sample_bootstrap_replicates": N_SELECTED_SAMPLE_BOOTSTRAP,
        "selected_sample_inner_cp_bootstrap_replicates": CP_BOOTSTRAP_REPS_SELECTED,
        "oracle_n": ORACLE_N,
        "R_values": SIM_R_VALUES,
        "primary_R": PRIMARY_R,
        "historical_auxiliary_R": HISTORICAL_AUXILIARY_R,
        "module2": asdict(MODULE2_CONFIG),
        "readiness_criteria": READINESS_CRITERIA,
    }
    config_hash = hashlib.sha256(
        json.dumps(config, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:12]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output_root = ROOT / "output" / "simulations" / "eight-scenarios"
    run_dir = output_root / f"run_{timestamp}_{config_hash}"
    table_dir = run_dir / "tables"
    figure_dir = run_dir / "figures"
    table_dir.mkdir(parents=True, exist_ok=False)
    figure_dir.mkdir(parents=True, exist_ok=False)

    compatibility = pd.DataFrame([
        {
            "feature": "implementation source",
            "historical_v2": "self-contained notebook implementation",
            "frozen_final": "universal_cutoff package",
            "compatible": False,
            "consequence": "historical v2 cannot establish final-package behavior",
        },
        {
            "feature": "evidence gate",
            "historical_v2": "dynamic range + positive slope + BIC improvement",
            "frozen_final": "same configured gate",
            "compatible": True,
            "consequence": "parameter definitions match",
        },
        {
            "feature": "absolute and relative targets",
            "historical_v2": "Low prevalence; 0.50/0.80 absolute with Mid/High relative fallback",
            "frozen_final": "same targets; level renamed Primary to Mid",
            "compatible": True,
            "consequence": "semantic targets are comparable",
        },
        {
            "feature": "changepoint role",
            "historical_v2": "supported CP could replace/move the semantic threshold within one bin",
            "frozen_final": "CP can corroborate only and never changes selected_threshold",
            "compatible": False,
            "consequence": "historical threshold-recovery and CP-alignment claims are superseded",
        },
        {
            "feature": "partial output",
            "historical_v2": "unavailable Low forced whole-set abstention",
            "frozen_final": "each level can abstain independently subject to ordering",
            "compatible": False,
            "consequence": "historical partial-output behavior is superseded",
        },
        {
            "feature": "ordering and collisions",
            "historical_v2": "nondecreasing checks; equal thresholds not explicitly de-duplicated",
            "frozen_final": "inversion abstains; equal thresholds share one operational representative",
            "compatible": False,
            "consequence": "historical collision behavior is superseded",
        },
        {
            "feature": "no fallback",
            "historical_v2": "no structural fallback; Low absence forced global abstention",
            "frozen_final": "no structural fallback; Low has no relative fallback; independent partial output",
            "compatible": False,
            "consequence": "principle matches but final behavior differs",
        },
        {
            "feature": "behavior-too-inclusive evaluation",
            "historical_v2": "response center 40 vs outcome center 60; governance classification recovery",
            "frozen_final": "same data-generating definition and classification-recovery estimand",
            "compatible": True,
            "consequence": "rerun uses primary R=14.05; R=15 retained only as auxiliary stress",
        },
        {
            "feature": "flat-null evaluation",
            "historical_v2": "threshold availability and false supported-CP rate",
            "frozen_final": "same explicit null targets",
            "compatible": True,
            "consequence": "rerun evaluates true abstention, not threshold accuracy",
        },
    ])

    scenario_table = pd.DataFrame([
        {
            "scenario": name,
            "description": cfg["description"],
            "response_kind": cfg["response_kind"],
            "true_changepoints": json.dumps(cfg["true_cps"]),
            "governance_scope": cfg["governance_scope"],
        }
        for name, cfg in SCENARIOS.items()
    ])
    condition_table = pd.DataFrame([
        {"condition": name, **cfg} for name, cfg in SIMULATION_CONDITIONS.items()
    ])

    oracle_truth = {}
    oracle_rows = []
    oracle_audits = {}
    for s_idx, scenario in enumerate(SCENARIOS):
        for c_idx, condition in enumerate(SIMULATION_CONDITIONS):
            rng = np.random.default_rng(RANDOM_STATE + 900_000 + s_idx * 10_000 + c_idx * 1000)
            cfg = SIMULATION_CONDITIONS[condition]
            score = draw_scores(rng, ORACLE_N, cfg["score_round_to"])
            semantic, _ = oracle_semantic_truth(scenario, condition, score)
            outcome_p = apply_symmetric_label_noise(
                outcome_probability(score, scenario), cfg["outcome_flip"]
            )
            outcome = rng.binomial(1, outcome_p).astype(int)
            values = {row.level: row.threshold for row in semantic.itertuples(index=False)}
            truth = {"score": score, "outcome": outcome, "anchors": semantic,
                     "values": values, "true_cps": tuple(SCENARIOS[scenario]["true_cps"])}
            oracle_truth[(scenario, condition)] = truth
            for row in semantic.itertuples(index=False):
                oracle_rows.append({
                    "scenario": scenario, "condition": condition, "level": row.level,
                    "true_threshold": row.threshold,
                    "true_available": bool(np.isfinite(row.threshold)),
                    "anchor_family": row.anchor_family,
                    "absolute_attainable": row.absolute_attainable,
                    "operational_representative": row.operational_representative,
                    "changepoint_may_move_threshold": False,
                })
            threshold_table = build_threshold_table(
                pd.DataFrame({"score": score, "outcome": outcome}), "score", None, "outcome"
            )
            for r_value in SIM_R_VALUES:
                oracle_audits[(scenario, condition, r_value)] = governance_audit(
                    threshold_table, values.get("Mid", np.nan), r_value
                )

    threshold_rows = []
    structural_rows = []
    governance_rows = []
    failures = []
    representative = {}

    for s_idx, scenario in enumerate(SCENARIOS):
        print(f"Running {scenario} ({s_idx + 1}/{len(SCENARIOS)})", flush=True)
        for c_idx, condition in enumerate(SIMULATION_CONDITIONS):
            truth = oracle_truth[(scenario, condition)]
            for replicate in range(N_REPLICATES):
                seed = RANDOM_STATE + s_idx * 100_000 + c_idx * 10_000 + replicate
                data = simulate_dataset(scenario, condition, seed)
                try:
                    point = fit_behavior_thresholds(data, "score", "response", MODULE2_CONFIG)
                    boot = bootstrap_module2(
                        data, "score", "response", MODULE2_CONFIG,
                        BootstrapConfig(enabled=True, n_bootstrap=CP_BOOTSTRAP_REPS_MAIN,
                                        random_state=seed + 777, n_jobs=1),
                        point,
                    )
                    validated = boot.validated_full_anchors
                except Exception as exc:
                    failures.append({
                        "scenario": scenario, "condition": condition,
                        "replicate": replicate, "error": repr(exc),
                    })
                    continue

                if condition == "baseline" and replicate == 0:
                    representative[scenario] = {"data": data.copy(), "point": point, "bootstrap": boot}

                point_values, point_complete, point_strict, point_collision = classify_anchor_set(point.anchors)
                final_values, final_complete, final_strict, final_collision = classify_anchor_set(validated)
                for method, estimates in [("point_semantic", point_values),
                                          ("bootstrap_validated", final_values)]:
                    for level in ["Low", "Mid", "High"]:
                        estimate = estimates[level]
                        true = truth["values"].get(level, np.nan)
                        estimated_available = bool(np.isfinite(estimate))
                        true_available = bool(np.isfinite(true))
                        error = abs(estimate - true) if estimated_available and true_available else np.nan
                        threshold_rows.append({
                            "scenario": scenario, "condition": condition,
                            "replicate": replicate, "method": method, "level": level,
                            "true_threshold": true, "estimated_threshold": estimate,
                            "true_available": true_available,
                            "estimated_available": estimated_available,
                            "availability_correct": estimated_available == true_available,
                            "absolute_error": error,
                            "bin_width": point.binning["bin_width"],
                            "within_one_bin": bool(error <= point.binning["bin_width"] + 1e-12)
                            if np.isfinite(error) else np.nan,
                        })

                supported = boot.changepoint_support
                cps = supported.loc[supported.status.eq("supported"), "cp"].tolist() \
                    if supported is not None and not supported.empty else []
                tolerance = max(
                    CP_RECOVERY_TOLERANCE_BINS * float(point.binning["bin_width"]), 3.0
                )
                cp_recall, mean_cp_error, false_cp_any = cp_recovery_metrics(
                    cps, truth["true_cps"], tolerance
                )
                indexed = validated.set_index("level")
                truth_indexed = truth["anchors"].set_index("level")
                movement = []
                for level in ["Low", "Mid", "High"]:
                    raw = indexed.loc[level, "semantic_threshold_operational"]
                    selected = indexed.loc[level, "selected_threshold"]
                    if pd.notna(raw) and pd.notna(selected):
                        movement.append(not np.isclose(float(raw), float(selected)))
                structural_rows.append({
                    "scenario": scenario, "condition": condition, "replicate": replicate,
                    "gate_supported": bool(point.evidence_gate["passed"]),
                    "gate_dynamic_range": point.evidence_gate.get("isotonic_dynamic_range", np.nan),
                    "gate_logistic_bic_improvement": point.evidence_gate.get("logistic_bic_improvement", np.nan),
                    "point_candidate_cp_count": int(len(point.supported_changepoints)),
                    "supported_cp_count": int(len(cps)),
                    "mean_supported_cp_bootstrap_support": float(
                        supported.loc[supported.status.eq("supported"), "bootstrap_support"].mean()
                    ) if cps else np.nan,
                    "cp_recall": cp_recall,
                    "mean_true_cp_error": mean_cp_error,
                    "false_cp_any": false_cp_any,
                    "T50_attainability_correct": bool(
                        (indexed.loc["Mid", "anchor_family"] == "absolute")
                        == bool(truth_indexed.loc["Mid", "absolute_attainable"])
                    ),
                    "T80_attainability_correct": bool(
                        (indexed.loc["High", "anchor_family"] == "absolute")
                        == bool(truth_indexed.loc["High", "absolute_attainable"])
                    ),
                    "any_threshold_available": bool(any(np.isfinite(v) for v in final_values.values())),
                    "partial_output": bool(any(np.isfinite(v) for v in final_values.values()) and not final_complete),
                    "complete_three_tier": final_complete,
                    "strict_three_tier_ordering": final_strict,
                    "adjacent_or_any_collision": final_collision,
                    "point_complete_three_tier": point_complete,
                    "point_strict_three_tier_ordering": point_strict,
                    "point_collision": point_collision,
                    "cp_moved_semantic_threshold": bool(any(movement)),
                    "all_available_thresholds_have_representative_flag": bool(
                        indexed.loc[indexed.selected_threshold.notna(), "operational_representative"].any()
                    ) if indexed.selected_threshold.notna().any() else True,
                })

                sample_threshold_table = build_threshold_table(data, "score", "response", "outcome")
                oracle_threshold = truth["values"].get("Mid", np.nan)
                estimated_mid = final_values["Mid"]
                for r_value in SIM_R_VALUES:
                    oracle_audit = oracle_audits[(scenario, condition, r_value)]
                    sample_oracle = governance_audit(sample_threshold_table, oracle_threshold, r_value)
                    end_to_end = governance_audit(sample_threshold_table, estimated_mid, r_value)
                    scope = SCENARIOS[scenario]["governance_scope"]
                    governance_rows.append({
                        "scenario": scenario, "condition": condition,
                        "replicate": replicate, "R": r_value, "scope": scope,
                        "oracle_classification": oracle_audit.summary["audit_classification"]
                        if oracle_audit else None,
                        "sample_oracle_classification": sample_oracle.summary["audit_classification"]
                        if sample_oracle else None,
                        "end_to_end_classification": end_to_end.summary["audit_classification"]
                        if end_to_end else None,
                        "oracle_comparator": oracle_audit.summary["same_or_lower_workload_threshold"]
                        if oracle_audit else np.nan,
                        "sample_oracle_comparator": sample_oracle.summary["same_or_lower_workload_threshold"]
                        if sample_oracle else np.nan,
                        "end_to_end_comparator": end_to_end.summary["same_or_lower_workload_threshold"]
                        if end_to_end else np.nan,
                        "oracle_excess_FAE_per_1000": (
                            oracle_audit.summary["behavior_excess_FAE"] / threshold_table.policy_N * 1000
                        ) if oracle_audit else np.nan,
                        "end_to_end_excess_FAE_per_1000": (
                            end_to_end.summary["behavior_excess_FAE"] / sample_threshold_table.policy_N * 1000
                        ) if end_to_end else np.nan,
                        "oracle_reference_classification_correct": bool(
                            sample_oracle and oracle_audit and
                            sample_oracle.summary["audit_classification"]
                            == oracle_audit.summary["audit_classification"]
                        ),
                        "end_to_end_classification_correct": bool(
                            end_to_end and oracle_audit and
                            end_to_end.summary["audit_classification"]
                            == oracle_audit.summary["audit_classification"]
                        ),
                        "correct_abstention": bool(scope == "abstain" and end_to_end is None),
                    })

    threshold_replicates = pd.DataFrame(threshold_rows)
    structural_replicates = pd.DataFrame(structural_rows)
    governance_replicates = pd.DataFrame(governance_rows)
    failure_table = pd.DataFrame(failures)

    threshold_summary = (
        threshold_replicates
        .groupby(["scenario", "condition", "method", "level"], dropna=False)
        .apply(summarize_threshold, include_groups=False)
        .reset_index()
    )
    structural_summary = (
        structural_replicates.groupby(["scenario", "condition"], dropna=False)
        .agg(
            replicates=("replicate", "nunique"),
            gate_support_rate=("gate_supported", "mean"),
            threshold_availability_rate=("any_threshold_available", "mean"),
            partial_output_rate=("partial_output", "mean"),
            complete_three_tier_rate=("complete_three_tier", "mean"),
            strict_three_tier_ordering_rate=("strict_three_tier_ordering", "mean"),
            collision_rate=("adjacent_or_any_collision", "mean"),
            mean_candidate_cp_count=("point_candidate_cp_count", "mean"),
            mean_supported_cp_count=("supported_cp_count", "mean"),
            mean_cp_bootstrap_support=("mean_supported_cp_bootstrap_support", "mean"),
            mean_cp_recall=("cp_recall", "mean"),
            false_cp_any_rate=("false_cp_any", "mean"),
            mean_true_cp_error=("mean_true_cp_error", "mean"),
            T50_attainability_accuracy=("T50_attainability_correct", "mean"),
            T80_attainability_accuracy=("T80_attainability_correct", "mean"),
            cp_movement_rate=("cp_moved_semantic_threshold", "mean"),
        ).reset_index()
    )
    governance_summary = (
        governance_replicates
        .groupby(["scenario", "condition", "R", "scope"], dropna=False)
        .apply(summarize_governance, include_groups=False)
        .reset_index()
    )

    representative_cp_rows = []
    for scenario, result in representative.items():
        cp_table = result["bootstrap"].changepoint_support
        if cp_table is None or cp_table.empty:
            representative_cp_rows.append({
                "scenario": scenario, "cp": np.nan, "bootstrap_support": np.nan,
                "status": "none", "selected_threshold_changed": False,
            })
        else:
            for row in cp_table.itertuples(index=False):
                representative_cp_rows.append({
                    "scenario": scenario, "cp": row.cp,
                    "bootstrap_support": row.bootstrap_support, "status": row.status,
                    "selected_threshold_changed": False,
                })
    representative_cp_support = pd.DataFrame(representative_cp_rows)

    selected_scenarios = [
        "aligned_sigmoid", "one_changepoint", "two_changepoints",
        "low_ceiling", "flat_behavior_null", "behavior_too_inclusive",
    ]
    selected_bootstrap_rows = []
    for selected_idx, scenario in enumerate(selected_scenarios):
        base = representative[scenario]["data"]
        rng = np.random.default_rng(RANDOM_STATE + 500_000 + selected_idx * 10_000)
        for bootstrap_index in range(N_SELECTED_SAMPLE_BOOTSTRAP):
            sampled_index = rng.integers(0, len(base), len(base))
            sample = base.iloc[sampled_index].reset_index(drop=True)
            try:
                point = fit_behavior_thresholds(sample, "score", "response", MODULE2_CONFIG)
                boot = bootstrap_module2(
                    sample, "score", "response", MODULE2_CONFIG,
                    BootstrapConfig(
                        enabled=True, n_bootstrap=CP_BOOTSTRAP_REPS_SELECTED,
                        random_state=RANDOM_STATE + 600_000 + selected_idx * 10_000 + bootstrap_index,
                        n_jobs=1,
                    ), point,
                )
                anchors = boot.validated_full_anchors
                values = anchor_values(anchors)
                supported_count = int(
                    boot.changepoint_support.status.eq("supported").sum()
                ) if boot.changepoint_support is not None and not boot.changepoint_support.empty else 0
                for level, estimate in values.items():
                    selected_bootstrap_rows.append({
                        "scenario": scenario, "bootstrap": bootstrap_index,
                        "level": level, "estimate": estimate,
                        "available": bool(np.isfinite(estimate)),
                        "gate_supported": bool(point.evidence_gate["passed"]),
                        "supported_cp_count": supported_count,
                    })
            except Exception as exc:
                selected_bootstrap_rows.append({
                    "scenario": scenario, "bootstrap": bootstrap_index,
                    "level": "FIT_FAILURE", "estimate": np.nan,
                    "available": False, "gate_supported": False,
                    "supported_cp_count": np.nan, "error": repr(exc),
                })
    selected_bootstrap = pd.DataFrame(selected_bootstrap_rows)
    selected_summary_rows = []
    for (scenario, level), group in selected_bootstrap[
        selected_bootstrap.level != "FIT_FAILURE"
    ].groupby(["scenario", "level"]):
        values = group.estimate.dropna()
        selected_summary_rows.append({
            "scenario": scenario, "level": level,
            "n_bootstrap": group.bootstrap.nunique(),
            "availability_rate": group.available.mean(),
            "median_estimate": values.median() if len(values) else np.nan,
            "percentile_low": values.quantile(.025) if len(values) else np.nan,
            "percentile_high": values.quantile(.975) if len(values) else np.nan,
            "gate_support_rate": group.gate_supported.mean(),
            "mean_supported_cp_count": group.supported_cp_count.mean(),
        })
    selected_summary = pd.DataFrame(selected_summary_rows)

    baseline_structural = structural_summary[structural_summary.condition == "baseline"]
    flat = baseline_structural[baseline_structural.scenario == "flat_behavior_null"].iloc[0]
    piecewise = baseline_structural[
        baseline_structural.scenario.isin(["one_changepoint", "two_changepoints"])
    ]
    low_ceiling = baseline_structural[baseline_structural.scenario == "low_ceiling"].iloc[0]
    baseline_governance = governance_summary[
        (governance_summary.condition == "baseline")
        & np.isclose(governance_summary.R, PRIMARY_R)
    ]
    inclusive = baseline_governance[
        baseline_governance.scenario == "behavior_too_inclusive"
    ].iloc[0]
    mid_summary = threshold_summary[
        (threshold_summary.condition == "baseline") & (threshold_summary.level == "Mid")
    ]
    mid_wide = mid_summary.pivot(index="scenario", columns="method", values="MAE")
    mid_difference = float((mid_wide.bootstrap_validated - mid_wide.point_semantic).median())
    cp_movement_rate = float(structural_replicates.cp_moved_semantic_threshold.mean())
    mean_piecewise_recall = float(piecewise.mean_cp_recall.mean())
    invariant_rows = [
        {
            "criterion": "historical implementation compatible with final semantic-first implementation",
            "observed": False, "target": True, "passed": False,
            "blocking_for_new_bundle": False,
            "interpretation": "trigger for this replacement run; historical v2 remains provenance only",
        },
        {
            "criterion": "fit failures",
            "observed": len(failure_table), "target": 0, "passed": len(failure_table) == 0,
            "blocking_for_new_bundle": True,
            "interpretation": "all requested scenario-condition-replicate fits must complete",
        },
        {
            "criterion": "flat-null threshold availability",
            "observed": flat.threshold_availability_rate,
            "target": "<=0.10", "passed": flat.threshold_availability_rate <= 0.10,
            "blocking_for_new_bundle": True,
            "interpretation": "flat null is evaluated by correct abstention",
        },
        {
            "criterion": "flat-null false supported-CP rate",
            "observed": flat.false_cp_any_rate,
            "target": "<=0.10", "passed": flat.false_cp_any_rate <= 0.10,
            "blocking_for_new_bundle": True,
            "interpretation": "false structural corroboration under the null",
        },
        {
            "criterion": "mean CP recall in piecewise scenarios (legacy provisional target)",
            "observed": mean_piecewise_recall,
            "target": ">=0.70", "passed": mean_piecewise_recall >= 0.70,
            "blocking_for_new_bundle": False,
            "interpretation": "descriptive only because CPs cannot generate, move, or rescue references",
        },
        {
            "criterion": "low-ceiling Mid/High attainability accuracy",
            "observed": min(low_ceiling.T50_attainability_accuracy,
                            low_ceiling.T80_attainability_accuracy),
            "target": ">=0.90",
            "passed": min(low_ceiling.T50_attainability_accuracy,
                          low_ceiling.T80_attainability_accuracy) >= 0.90,
            "blocking_for_new_bundle": True,
            "interpretation": "absolute unattainability must invoke only permitted relative targets",
        },
        {
            "criterion": "median validated-minus-point Mid MAE",
            "observed": mid_difference, "target": "<=0.50",
            "passed": mid_difference <= 0.50,
            "blocking_for_new_bundle": True,
            "interpretation": "CP corroboration may not move the semantic reference",
        },
        {
            "criterion": "CP movement rate",
            "observed": cp_movement_rate, "target": 0.0,
            "passed": np.isclose(cp_movement_rate, 0.0),
            "blocking_for_new_bundle": True,
            "interpretation": "changepoints corroborate only",
        },
        {
            "criterion": "behavior-too-inclusive governance accuracy at R=14.05",
            "observed": inclusive.end_to_end_classification_accuracy,
            "target": ">=0.75",
            "passed": inclusive.end_to_end_classification_accuracy >= 0.75,
            "blocking_for_new_bundle": True,
            "interpretation": "classification recovery, not causal utility or savings",
        },
    ]
    invariant_audit = pd.DataFrame(invariant_rows)

    tables = {
        "compatibility_audit.csv": compatibility,
        "simulation_scenarios.csv": scenario_table,
        "simulation_conditions.csv": condition_table,
        "oracle_truth.csv": pd.DataFrame(oracle_rows),
        "threshold_replicates.csv": threshold_replicates,
        "threshold_recovery_summary.csv": threshold_summary,
        "structural_replicates.csv": structural_replicates,
        "structural_abstention_summary.csv": structural_summary,
        "governance_replicates.csv": governance_replicates,
        "governance_summary.csv": governance_summary,
        "representative_cp_support.csv": representative_cp_support,
        "selected_sample_bootstrap_replicates.csv": selected_bootstrap,
        "selected_sample_bootstrap_summary.csv": selected_summary,
        "fit_failures.csv": failure_table,
        "final_invariant_audit.csv": invariant_audit,
    }
    for filename, table in tables.items():
        table.to_csv(table_dir / filename, index=False)

    baseline_plot = threshold_summary[
        (threshold_summary.condition == "baseline")
        & (threshold_summary.method == "bootstrap_validated")
    ].copy()
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), sharey=False)
    for axis, level in zip(axes, ["Low", "Mid", "High"]):
        view = baseline_plot[baseline_plot.level == level]
        axis.barh(view.scenario, view.MAE, color="#4C78A8")
        axis.set_title(level)
        axis.set_xlabel("Mean absolute error")
        axis.grid(axis="x", alpha=.2)
    fig.suptitle("Final-package semantic-reference recovery: baseline scenarios")
    fig.tight_layout()
    fig.savefig(figure_dir / "baseline_threshold_recovery.png", dpi=300, bbox_inches="tight")
    fig.savefig(figure_dir / "baseline_threshold_recovery.pdf", bbox_inches="tight")
    plt.close(fig)

    governance_plot = baseline_governance.copy()
    fig, axis = plt.subplots(figsize=(8.5, 5.0))
    axis.barh(governance_plot.scenario, governance_plot.end_to_end_classification_accuracy,
              color="#54A24B")
    axis.axvline(.75, color="#E45756", linestyle="--", linewidth=1.3,
                 label="pre-specified 0.75 target")
    axis.set_xlim(0, 1.02)
    axis.set_xlabel("Governance-classification recovery")
    axis.set_title("Final-package governance recovery at R=14.05 (baseline)")
    axis.grid(axis="x", alpha=.2)
    axis.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(figure_dir / "baseline_governance_R14_05.png", dpi=300, bbox_inches="tight")
    fig.savefig(figure_dir / "baseline_governance_R14_05.pdf", bbox_inches="tight")
    plt.close(fig)

    blocking_pass = bool(
        invariant_audit.loc[invariant_audit.blocking_for_new_bundle, "passed"].all()
    )
    legacy_cp_pass = bool(
        invariant_audit.loc[
            invariant_audit.criterion.str.contains("legacy provisional"), "passed"
        ].iloc[0]
    )
    summary_lines = [
        "# Final semantic-first ActionRef simulation validation",
        "",
        f"Run bundle: `{run_dir}`  ",
        f"Config hash: `{config_hash}`  ",
        f"Status: `{'PASS' if blocking_pass else 'FAIL'}`",
        "",
        "## Why a new run was required",
        "",
        "The historical v2 simulation was not implementation-compatible with the frozen package: "
        "it could move a semantic threshold to a nearby supported changepoint, forced global "
        "abstention when Low was unavailable, and did not explicitly de-duplicate threshold "
        "collisions. The new run uses the frozen package and supersedes historical v2 for all "
        "final-method performance claims.",
        "",
        "## Preserved design",
        "",
        f"Eight scenarios, four stress conditions, {N_REPLICATES} Monte Carlo replicates per "
        f"scenario-condition, main inner bootstrap n={CP_BOOTSTRAP_REPS_MAIN}, representative "
        f"outer bootstrap n={N_SELECTED_SAMPLE_BOOTSTRAP} with inner n={CP_BOOTSTRAP_REPS_SELECTED}, "
        f"and random seed {RANDOM_STATE} were preserved. R=14.05 is the primary governance "
        "worked value; R=15 is retained only as a historical auxiliary stress value.",
        "",
        "## Headline checks",
        "",
        invariant_audit.to_markdown(index=False),
        "",
        "The legacy provisional changepoint-recall criterion is reported transparently as "
        f"`{'passed' if legacy_cp_pass else 'not passed'}`, but it is non-blocking for the "
        "semantic-first implementation because changepoints cannot create, move, or rescue any "
        "reference.",
        "",
        "## Claim guard",
        "",
        "Simulation results validate behavior of the specified algorithm under synthetic "
        "conditions. They do not establish clinical benefit, causal treatment effects, monetary "
        "savings, or transport performance.",
    ]
    (run_dir / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    output_inventory = []
    for path in sorted(run_dir.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            output_inventory.append({
                "relative_path": path.relative_to(run_dir).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            })
    manifest = {
        "analysis_version": "final semantic-first ActionRef simulation validation",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "run_directory": str(run_dir),
        "config_hash": config_hash,
        "config": config,
        "historical_compatibility": "incompatible; replacement run required",
        "source_registry": source_registry,
        "source_hashes_unchanged": all(sha256_file(path) == row["sha256"]
                                       for path, row in zip(source_paths, source_registry)),
        "blocking_invariants_passed": blocking_pass,
        "legacy_provisional_cp_recall_passed": legacy_cp_pass,
        "outputs": output_inventory,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
        },
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, default=jsonable) + "\n",
        encoding="utf-8",
    )
    (run_dir / "COMPLETED").write_text(
        f"blocking_invariants_passed={blocking_pass}\n", encoding="utf-8"
    )
    print(json.dumps({
        "run_directory": str(run_dir),
        "config_hash": config_hash,
        "blocking_invariants_passed": blocking_pass,
        "legacy_provisional_cp_recall_passed": legacy_cp_pass,
        "fit_failures": len(failure_table),
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
