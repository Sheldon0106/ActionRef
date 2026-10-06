"""Controlled V7 regression. Private clinical data must not be committed.

Usage: python examples/sepsis_v7_integration.py --mimic PATH --stanford PATH
"""
import argparse

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from universal_cutoff import fit_behavior_thresholds


def missing_aware_or(data, columns):
    values = data[columns].apply(pd.to_numeric, errors="coerce")
    result = pd.Series(np.nan, index=data.index, dtype=float)
    positive = values.eq(1).any(axis=1)
    all_observed = values.notna().all(axis=1)
    result.loc[positive] = 1
    result.loc[(~positive) & all_observed] = 0
    return result


def thresholds(result):
    return result.anchors.set_index("level").selected_threshold.to_dict()


def run(mimic_path, stanford_path):
    mimic_columns = [
        "subject_id", "stay_id", "intime", "outcome_sepsis3", "score_ESRP_new",
        "lactate_flag", "icu_fluid_flag", "vasopressor_flag", "steroid_flag",
        "legacy_v7_primary_eligible",
    ]
    mimic = pd.read_csv(mimic_path, usecols=mimic_columns, low_memory=False)
    mimic["response"] = missing_aware_or(
        mimic, ["lactate_flag", "icu_fluid_flag", "vasopressor_flag", "steroid_flag"])
    mimic.loc[pd.to_numeric(mimic.legacy_v7_primary_eligible, errors="coerce").ne(1), "response"] = np.nan
    eligible = mimic.loc[pd.to_datetime(mimic.intime, errors="coerce").notna()].copy()
    splitter = GroupShuffleSplit(n_splits=1, train_size=.70, random_state=2026)
    learning_index, _ = next(splitter.split(eligible, y=eligible.outcome_sepsis3,
                                             groups=eligible.subject_id))
    mimic_result = fit_behavior_thresholds(eligible.iloc[learning_index], "score_ESRP_new", "response")

    stanford_columns = [
        "subject_id", "stay_id", "outcome_sepsis3", "score_ESRP", "lactate_flag",
        "fluid_6h", "vasopressor_flag", "steroid_flag",
    ]
    stanford = pd.read_csv(stanford_path, usecols=stanford_columns, low_memory=False)
    fluid = pd.to_numeric(stanford.fluid_6h, errors="coerce")
    stanford["fluid_component"] = np.where(fluid.notna(), (fluid >= 2000).astype(float), np.nan)
    stanford["response"] = missing_aware_or(
        stanford, ["lactate_flag", "fluid_component", "vasopressor_flag", "steroid_flag"])
    stanford_result = fit_behavior_thresholds(stanford, "score_ESRP", "response")

    observed = {"MIMIC": thresholds(mimic_result), "Stanford": thresholds(stanford_result)}
    expected = {"MIMIC": {"Low": 27, "Mid": 36, "High": 51},
                "Stanford": {"Low": 26, "Mid": 36, "High": 50}}
    if observed != expected:
        raise AssertionError("V7 regression mismatch: observed={!r}, expected={!r}".format(observed, expected))
    print("Controlled V7 regression passed:", observed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mimic", required=True)
    parser.add_argument("--stanford", required=True)
    args = parser.parse_args()
    run(args.mimic, args.stanford)

