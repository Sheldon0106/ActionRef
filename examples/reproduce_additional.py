"""Assemble the corrected COPD paper results from public aggregates.

The evaluation is conditional on the supplied score. Patient-bootstrap intervals
are supplied aggregates, not re-estimated by this command.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results/copd/validation_v2_corrected"


def calculate(source=SOURCE):
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    for name, item in manifest["public_files"].items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Corrected COPD source checksum mismatch: " + name)
    anchors = pd.read_csv(source / "reference/module2_point_anchors.csv")
    values = anchors.set_index("level").selected_threshold
    np.testing.assert_allclose(values.loc[["Low", "Mid"]],
                               [17.779760509763356, 55.07187581853598], rtol=0, atol=1e-12)
    high = anchors.set_index("level").loc["High"]
    assert pd.isna(high.selected_threshold) and high.attainability_status == "unavailable_ordering"
    assert high.semantic_threshold_raw == 50
    operating = pd.read_csv(source / "tables/operating_comparison.csv")
    corrected = operating.loc[operating.response_version.eq("corrected")].copy()
    assert (corrected.TP + corrected.FP + corrected.FN + corrected.TN).eq(corrected.policy_N).all()
    np.testing.assert_allclose(corrected.alert_count, corrected.TP + corrected.FP)
    np.testing.assert_allclose(corrected.response_yield, corrected.response_count / corrected.alert_count)
    predictive = pd.read_csv(source / "tables/predictive_point.csv")
    subset = predictive.loc[predictive.cohort.eq("heldout_score_fit_excluded")].iloc[0]
    assert int(subset.patients) == 13978 and int(subset.encounters) == 15221
    assert round(float(subset.AUROC), 3) == 0.894
    return {
        "etable22_copd_full_heldout": corrected.loc[corrected.cohort.eq("heldout_full")],
        "etable21_copd_references": anchors,
        "etable22_copd_operating": corrected,
        "etable39_copd_reference_uncertainty": pd.read_csv(source / "reference/stability_summary_package.csv"),
        "etable41_copd_predictive": predictive,
        "etable41_copd_predictive_intervals": pd.read_csv(source / "tables/predictive_intervals.csv"),
        "etable41_copd_operating_intervals": pd.read_csv(source / "tables/operating_intervals.csv").loc[
            lambda x: x.response_version.eq("corrected") & x.cohort.eq("heldout_score_fit_excluded")],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output/copd")
    args = parser.parse_args()
    tables = calculate(args.source)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(args.out_dir / (name + ".csv"), index=False)
    print("PASS: corrected COPD sources, partial references and score-fit-patient-excluded evaluation.")


if __name__ == "__main__":
    main()
