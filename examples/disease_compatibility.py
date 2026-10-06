"""Apply the frozen package to a non-sepsis disease and emit an aggregate summary.

Package-level validation that the implementation carries no disease-specific
assumptions. Module 2 and evidence-gate parameters stay at frozen defaults and no
disease-specific override is passed. An evidence-gate abstention is retained as a
valid finding and written to the summary.

Patient-level data remains outside the repository. The dataset path is a
command-line argument and every file written here is aggregate.

Usage:
  python examples/disease_compatibility.py --config configs/copd_autoscore.yaml \
      --data PATH --out-dir results/copd
"""
import argparse
import json
import os

import numpy as np
import pandas as pd
import yaml

from universal_cutoff import (CapacityConfig, apply_capacity, build_threshold_table,
                              evaluate_score, fit_behavior_thresholds)


def load_config(path):
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def run(config_path, data_path, out_dir):
    config = load_config(config_path)
    columns = config["columns"]
    score_col, outcome_col, response_col = columns["score"], columns["outcome"], columns["response"]

    if config.get("module2", {}).get("overrides"):
        raise SystemExit(
            "config supplies Module 2 overrides; the compatibility run must use frozen defaults"
        )

    wanted = [score_col, outcome_col, response_col]
    for optional in ("response_sensitivity", "subject_id", "encounter_id"):
        name = columns.get(optional)
        if name:
            wanted.append(name)
    available = set(pd.read_csv(data_path, nrows=1, low_memory=False).columns)
    missing = [c for c in wanted if c not in available]
    if missing:
        raise SystemExit("dataset is missing required columns: {}".format(missing))
    data = pd.read_csv(data_path, usecols=[c for c in wanted if c in available], low_memory=False)

    report = {
        "disease": config["disease"],
        "dataset": config["dataset"],
        "source_notebook": config["source_notebook"],
        "columns": {"score": score_col, "outcome": outcome_col, "response": response_col},
        "rows_loaded": int(len(data)),
        "module2_overrides_used": False,
        "module3b": {"status": "unavailable", "reason": config["module3b"]["reason"].strip()},
        "bootstrap": {"enabled": False, "reason": config["bootstrap"]["reason"].strip()},
    }
    if "circularity_note" in config:
        report["circularity_note"] = config["circularity_note"].strip()

    module1, _calibrator = evaluate_score(data, score_col, outcome_col)
    report["module1"] = {k: (float(v) if isinstance(v, (int, float, np.floating)) else v)
                         for k, v in module1.items() if not isinstance(v, pd.DataFrame)}

    bundles = {"primary": response_col}
    if columns.get("response_sensitivity"):
        bundles["sensitivity"] = columns["response_sensitivity"]

    report["module2"] = {}
    report["module3a"] = {}
    os.makedirs(out_dir, exist_ok=True)

    for label, bundle_col in bundles.items():
        result = fit_behavior_thresholds(data, score_col, bundle_col)
        gate = result.evidence_gate
        anchors = result.anchors
        report["module2"][label] = {
            "response_column": bundle_col,
            "N_complete": int(result.input_summary["N_complete"]),
            "response_prevalence": float(result.input_summary["response_prevalence"]),
            "bin_width": float(result.binning["bin_width"]),
            "valid_bins": int(len(result.response_curve)),
            "evidence_gate_passed": bool(gate["passed"]),
            "evidence_gate_reason": gate.get("reason"),
            "isotonic_dynamic_range": _maybe_float(gate.get("isotonic_dynamic_range")),
            "supported_changepoints": int(len(result.supported_changepoints)),
            "thresholds": {
                str(row["level"]): _maybe_float(row.get("selected_threshold"))
                for _, row in anchors.iterrows()
            },
            "selected_types": {
                str(row["level"]): row.get("selected_type") for _, row in anchors.iterrows()
            },
        }
        anchors.to_csv(os.path.join(out_dir, "module2_anchors_{}.csv".format(label)), index=False)
        result.response_curve.to_csv(
            os.path.join(out_dir, "module2_response_curve_{}.csv".format(label)), index=False)

        if label != "primary":
            continue
        usable = anchors["selected_threshold"].notna().any()
        if not usable:
            report["module3a"] = {
                "status": "not_run",
                "reason": "Module 2 produced no available threshold, so there is nothing to adjust",
            }
            continue
        table = build_threshold_table(data, score_col, response_col=bundle_col, outcome_col=outcome_col)
        rows = []
        for fraction in config["module3a"]["capacity_fractions"]:
            k = int(np.floor(float(fraction) * table.policy_N))
            capacity = apply_capacity(table, anchors, CapacityConfig(K=k, period="analysis cohort"))
            frame = capacity.table.copy()
            frame.insert(0, "K_fraction_requested", fraction)
            rows.append(frame)
        capacity_table = pd.concat(rows, ignore_index=True)
        capacity_table.to_csv(os.path.join(out_dir, "module3a_capacity.csv"), index=False)
        report["module3a"] = {
            "status": "run",
            "policy_N": int(table.policy_N),
            "capacity_fractions": list(config["module3a"]["capacity_fractions"]),
        }

    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, default=str)
    print(json.dumps(report, indent=2, default=str))
    return report


def _maybe_float(value):
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return None if not np.isfinite(out) else out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    run(args.config, args.data, args.out_dir)
