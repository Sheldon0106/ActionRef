"""Replay reported AERT aggregates without patient records or identifiers.

Recomputes research/default reference decisions and operating counts from score
bins. Reported patient-bootstrap intervals are assembled from saved summaries.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from aert_reference_policy import fit_both, V2

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results/aert"


def read_json(source, name):
    return json.loads((source / name).read_text(encoding="utf-8"))


def verify(source=SOURCE):
    manifest = read_json(source, "manifest.json")
    for name, item in manifest["files"].items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("AERT source checksum mismatch: " + name)
    config = manifest["config"]
    if hashlib.sha256((ROOT / config["path"]).read_bytes()).hexdigest() != config["sha256"]:
        raise ValueError("AERT configuration checksum mismatch")


def calculate(source=SOURCE):
    verify(source)
    models = read_json(source, "models_frozen.json")
    bins = pd.DataFrame(read_json(source, "score_response_distribution.json"))
    operating = pd.DataFrame(read_json(source, "test_operating_point.json"))
    references = []
    for identity, model in models.items():
        analysis, scale = identity.split("|")
        shift = int(scale == "fill1")
        development = bins.loc[bins.analysis.eq(analysis) & bins.split.eq("development")]
        size = 11 if shift else 9
        n = np.bincount(development.native_score.to_numpy(int) + shift,
                        weights=development.N, minlength=size).astype(int)
        k = np.bincount(development.native_score.to_numpy(int) + shift,
                        weights=development.response1, minlength=size).astype(int)
        output, tail = fit_both(n, k)
        for policy, saved in model["policies"].items():
            decision = output[0][policy]
            current = {
                row.level: float(row.selected_threshold)
                for row in output[2].itertuples()
                if decision["any_anchor"] and row.operational_representative
                and pd.notna(row.selected_threshold)
            }
            if current != saved["references"]:
                raise ValueError("Reference replay differs: " + identity + " / " + policy)
            for name in ("eligible", "gate_passed", "any_anchor", "unique_anchors"):
                if decision[name] != saved[name]:
                    raise ValueError("Policy replay differs: " + identity + " / " + name)
            references.append(dict(analysis=analysis, scale=scale, policy=policy,
                                   references=current, **decision,
                                   tail_veto=tail["v2_shape_veto"]))

    # Aggregate score bins contain encounter counts, outcome counts and action counts.
    # No individual-level reconstruction or identifier export is used.
    for row in operating.itertuples():
        test = bins.loc[bins.analysis.eq(row.analysis) & bins.split.eq("test")]
        shift = int(row.scale == "fill1")
        flagged = test.native_score.add(shift).ge(row.threshold)
        total = int(test.N.sum())
        positive = int(test.events.sum())
        alerts = int(test.loc[flagged, "N"].sum())
        tp = int(test.loc[flagged, "events"].sum())
        captured = int(test.loc[flagged, "response1"].sum())
        expected = {"N": total, "alert_count": alerts, "TP": tp, "FP": alerts - tp,
                    "FN": positive - tp, "TN": total - positive - alerts + tp,
                    "response_positive": int(test.response1.sum()),
                    "response_captured": captured}
        for name, value in expected.items():
            if int(getattr(row, name)) != value:
                raise ValueError("Operating count differs: " + row.analysis + " / " + name)

    points = pd.DataFrame(read_json(source, "action_calibration_points.json"))
    action_models = {r["analysis"]: r for r in read_json(source, "action_models_evaluated.json")}
    for row in points.itertuples():
        test = bins.loc[bins.analysis.eq(row.analysis) & bins.split.eq("test")].copy()
        model = action_models[row.analysis]
        x = np.asarray(model["score"], float)
        curve = np.asarray(model["action_probability"], float)
        if row.scope == "exact_supported_scores":
            test = test.loc[test.native_score.isin(x)]
        elif row.scope == "within_supported_range":
            test = test.loc[test.native_score.between(x.min(), x.max())]
        elif row.scope != "all_test":
            raise ValueError("Unknown action-evaluation scope: " + row.scope)
        p = np.interp(test.native_score, x, curve)
        n = test.N.to_numpy(float)
        k = test.response1.to_numpy(float)
        q = float(model["development_action_rate"])
        expected = {
            "N": n.sum(), "action_rate": k.sum() / n.sum(),
            "mean_predicted": np.sum(n * p) / n.sum(),
            "action_Brier": np.sum(k * (1-p)**2 + (n-k) * p**2) / n.sum(),
            "constant_development_rate_Brier":
                np.sum(k * (1-q)**2 + (n-k) * q**2) / n.sum(),
        }
        for name, value in expected.items():
            np.testing.assert_allclose(getattr(row, name), value, atol=1e-12, rtol=0,
                                       err_msg=row.analysis + " / " + row.scope + " / " + name)

    config = json.loads((ROOT / "configs/aert.json").read_text(encoding="utf-8"))
    main = config["primary_analysis"]
    native_main = operating.loc[operating.analysis.eq(main) & operating.scale.eq("native")
                                & operating.policy.eq(V2)]
    assert len(models) == 32 and len(action_models) == 16
    assert len(operating.loc[operating.scale.eq("native")]) == 55
    assert dict(zip(native_main.level, native_main.threshold)) == {"Mid": 3.0, "High": 6.0}
    return {
        "table4_aert": native_main,
        "etable32_populations": pd.DataFrame(read_json(source, "population_registry.json")),
        "etable33_reference_replay": pd.DataFrame(references),
        "etable33_anchor_uncertainty": pd.DataFrame(read_json(source, "development_anchor_summary.json")),
        "etable33_dictionary_stability": pd.DataFrame(read_json(source, "development_stability_summary.json")),
        "etable34_operating_intervals": pd.DataFrame(read_json(source, "test_operating_intervals.json")),
        "etable38_action_probability": points.loc[points.analysis.isin([main, config["source_primary_analysis"]])
                                                  & points.scope.eq("all_test")],
        "supplementary_data1_operating": operating,
        "supplementary_data2_action_probability": points,
        "supplementary_data2_action_intervals": pd.DataFrame(read_json(source, "action_calibration_intervals.json")),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output/aert")
    args = parser.parse_args()
    tables = calculate(args.source)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(args.out_dir / (name + ".csv"), index=False)
    print("PASS: 32 score/setting reference replays, 110 operating points and 48 action summaries.")
    print("Intervals assembled from saved patient-bootstrap summaries; no clinical records read.")


if __name__ == "__main__":
    main()
