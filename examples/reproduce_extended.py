"""Assemble extended summaries and check manuscript counts from public aggregates.

No patient data, model fitting, bootstrap or simulation runs are required.
Run from the repository root: python examples/reproduce_extended.py
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = ROOT / "results/sepsis_primary"
EXTENDED = ROOT / "results/supplement_extended"
SOURCES = {
    "minimax_regret.csv": "results/sepsis_primary/consequence_scenarios/paper_minimax_behavior_budget.csv",
    "transfer_target_sensitivity.csv": "results/sepsis_primary/era_and_transport/paper_transport_decomposition.csv",
    "original_eight_scenarios.csv": "simulations/eight_scenarios/analysis2_existing_summary.csv",
    "conventional_selection_uncertainty.csv": "results/sepsis_primary/conventional_rules/comparator_selection_bootstrap_summary.csv",
}
COHORTS = {
    "MIMIC_heldout": "MIMIC internal validation set",
    "MIMIC held-out validation": "MIMIC internal validation set",
    "Stanford": "Stanford external validation cohort",
    "Stanford external validation": "Stanford external validation cohort",
}


def calculate():
    """Read saved scenarios and join subgroup operating and calibration summaries."""
    tables = {name: pd.read_csv(ROOT / path) for name, path in SOURCES.items()}
    keys = ["cohort", "subgroup_variable", "subgroup"]
    operating = pd.read_csv(PRIMARY / "subgroups/v7_subgroup_paper_summary_reconstructed.csv")
    calibration = pd.read_csv(PRIMARY / "subgroups/subgroup_predictive_calibration_detail.csv")
    if calibration.duplicated(keys).any() or operating.duplicated(keys + ["level"]).any():
        raise ValueError("Subgroup keys are not unique")
    shared = set(operating.columns).intersection(calibration.columns) - set(keys)
    # Retain shared counts once, after checking agreement at every reference level.
    checked = operating.merge(calibration, on=keys, validate="many_to_one", suffixes=("", "_calibration"))
    if len(checked) != len(operating):
        raise ValueError("Some operating groups have no calibration summary")
    for name in shared:
        np.testing.assert_allclose(checked[name], checked[name + "_calibration"], rtol=0, atol=0)
    merged = operating.merge(calibration.drop(columns=sorted(shared)), on=keys, validate="many_to_one")
    if len(merged[keys].drop_duplicates()) != len(calibration):
        raise ValueError("Some calibration groups have no operating summary")
    tables["subgroup_diagnostics.csv"] = merged
    for frame in tables.values():
        for column in ("cohort", "site", "label"):
            if column in frame:
                frame[column] = frame[column].replace(COHORTS)
    return tables


def check_operating(frame):
    """Check exact count arithmetic with the action-known yield denominator."""
    assert frame[["TP", "FP", "FN", "TN"]].sum(axis=1).eq(frame.N).all()
    assert (frame.TP + frame.FP).eq(frame.flagged_N).all()
    assert (frame.action_positive_flagged_N <= frame.action_known_flagged_N).all()
    assert (frame.action_known_flagged_N <= frame.flagged_N).all()
    expected = {
        "alerts_per_1000": 1000 * frame.flagged_N / frame.N,
        "observed_action_yield": frame.action_positive_flagged_N / frame.action_known_flagged_N,
        "sensitivity": frame.TP / (frame.TP + frame.FN),
        "specificity": frame.TN / (frame.TN + frame.FP),
        "unflagged_outcomes_per_1000": 1000 * frame.FN / frame.N,
        "FAE_per_1000": 1000 * (frame.FP + (11299 / 804) * frame.FN) / frame.N,
    }
    for name, values in expected.items():
        np.testing.assert_allclose(frame[name], values, rtol=0, atol=1e-10)


def check_primary():
    """Validate saved tiers/rules and reconstruct the 0–100 FAE curve from bins."""
    characteristics = pd.read_csv(PRIMARY / "cohort_characteristics.csv")
    actions = characteristics.loc[characteristics.section.eq("Action denominators")].pivot(
        index="cohort", columns="characteristic", values="value"
    ).astype(int)
    assert (actions.recorded_action_known_N + actions.recorded_action_unknown_N).eq(actions.encounters).all()
    assert (actions.recorded_action_positive_N <= actions.recorded_action_known_N).all()
    np.testing.assert_array_equal(
        actions.loc["MIMIC-IV-ED"],
        actions.loc["MIMIC derivation set"] + actions.loc["MIMIC internal validation set"],
    )
    rules = pd.read_csv(PRIMARY / "conventional_rules/rule_operating_rows.csv")
    tiers = pd.read_csv(PRIMARY / "conventional_rules/esrp_tier_boundaries.csv")
    for frame, thresholds in ((rules, {26, 34, 40, 45}), (tiers, {21, 31, 45})):
        check_operating(frame)
        assert not frame.duplicated(["cohort", "threshold"]).any()
        assert all(set(g.threshold) == thresholds for _, g in frame.groupby("cohort"))
    raw = pd.read_csv(PRIMARY / "conventional_rules/comparator_operating_results_extended.csv")
    count_cols = ["TP", "FP", "FN", "TN", "flagged_N", "action_known_flagged_N", "action_positive_flagged_N"]
    for row in rules.itertuples():
        matches = raw.loc[raw.cohort.replace(COHORTS).eq(row.cohort) & raw.threshold.eq(row.threshold), count_cols]
        assert len(matches) and len(matches.drop_duplicates()) == 1
        np.testing.assert_array_equal(matches.iloc[0], [getattr(row, c) for c in count_cols])
    for cohort, group in tiers.loc[tiers.threshold.eq(45)].groupby("cohort"):
        reference = rules.loc[rules.cohort.eq(cohort) & rules.threshold.eq(45)]
        np.testing.assert_array_equal(group[count_cols], reference[count_cols])
    hist = pd.read_csv(PRIMARY / "consequence_scenarios/comparator_development_selection_curve.csv")
    curve = pd.read_csv(PRIMARY / "learning_fae_curve.csv")
    assert curve.threshold.tolist() == list(range(101))
    n, positives = int(hist.score_N.sum()), int(hist.score_positive.sum())
    assert (n, positives) == (314658, 12099)
    for row in curve.itertuples():
        flagged = hist.loc[hist.threshold.ge(row.threshold)]
        alert, tp = int(flagged.score_N.sum()), int(flagged.score_positive.sum())
        fp, fn = alert - tp, positives - tp
        np.testing.assert_array_equal([row.N, row.alert_N, row.TP, row.FP, row.FN, row.TN],
                                      [n, alert, tp, fp, fn, n - positives - fp])
        np.testing.assert_allclose(row.FAE_per_1000, 1000 * (fp + 11299 / 804 * fn) / n, rtol=0, atol=1e-9)
    assert int(curve.loc[curve.FAE_per_1000.idxmin(), "threshold"]) == 34
    return curve


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "output/extended")
    args = parser.parse_args()
    tables = calculate()
    manifest = json.loads((EXTENDED / "manifest.json").read_text(encoding="utf-8"))
    for name, frame in tables.items():
        path = EXTENDED / name
        if hashlib.sha256(path.read_bytes()).hexdigest() != manifest["files"][name]["sha256"]:
            raise ValueError("Extended summary checksum mismatch: " + name)
        pd.testing.assert_frame_equal(frame, pd.read_csv(path), check_dtype=False, rtol=1e-13, atol=1e-13)
    curve = check_primary()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.to_csv(args.output_dir / name, index=False)
    print("PASS: five extended summaries; 8 rule rows; 6 ESRP tier rows; {} derivation thresholds.".format(len(curve)))
    print("Saved estimates and intervals are reused; no clinical analysis or simulation was rerun.")


if __name__ == "__main__":
    main()
