"""Synthetic contract tests for disease-agnostic behavior in the core modules."""
import pathlib
import re

import numpy as np
import pandas as pd
import pytest

from universal_cutoff import CapacityConfig, apply_capacity, build_threshold_table, fit_behavior_thresholds

CORE = pathlib.Path(__file__).resolve().parents[1] / "src" / "universal_cutoff"
DISEASE_WORDS = ("sepsis", "copd", "pneumonia", "aki", "bronchodilator", "lactate",
                 "vasopressor", "antibiotic", "esrp", "autoscore", "news2", "qsofa")


def synthetic(seed, ceiling=0.95, floor=0.05, n=12000, midpoint=50.0, scale=8.0):
    rng = np.random.RandomState(seed)
    score = rng.randint(0, 101, n)
    probability = floor + (ceiling - floor) / (1.0 + np.exp(-(score - midpoint) / scale))
    return pd.DataFrame({
        "score": score,
        "response": rng.binomial(1, probability),
        "outcome": rng.binomial(1, np.clip(probability * .4, 0, 1)),
    })


def test_core_modules_contain_no_disease_or_source_column_names():
    offenders = []
    for path in sorted(CORE.glob("*.py")):
        text = path.read_text(encoding="utf-8").lower()
        for word in DISEASE_WORDS:
            if re.search(r"\b{}\b".format(re.escape(word)), text):
                offenders.append("{}: {}".format(path.name, word))
    assert not offenders, offenders


def test_two_unrelated_synthetic_diseases_run_through_one_unchanged_code_path():
    results = [fit_behavior_thresholds(synthetic(seed, midpoint=midpoint), "score", "response")
               for seed, midpoint in ((11, 40.0), (12, 65.0))]
    for result in results:
        assert result.evidence_gate["passed"] is True
        assert result.anchors.selected_threshold.notna().any()
    first, second = (r.anchors.set_index("level").selected_threshold for r in results)
    assert first["Mid"] != second["Mid"]
    assert all(r.config == results[0].config for r in results)


def test_low_ceiling_response_uses_a_labelled_relative_anchor_and_never_a_structural_one():
    """v0.3 prohibits structural fallback. A relative anchor is semantic, so it is permitted."""
    result = fit_behavior_thresholds(synthetic(21, ceiling=.35), "score", "response")
    anchors = result.anchors.set_index("level")
    for level in ("Mid", "High"):
        assert anchors.loc[level, "anchor_name"].endswith("relative_response")
        assert anchors.loc[level, "selected_type"] == "relative-anchor"
    assert (result.anchors.selected_type != "structural").all()
    assert (result.anchors.selected_type != "structural-fallback").all()


def test_flat_response_abstains_across_every_level():
    rng = np.random.RandomState(5)
    flat = pd.DataFrame({"score": rng.randint(0, 101, 12000)})
    flat["response"] = rng.binomial(1, .3, len(flat))
    result = fit_behavior_thresholds(flat, "score", "response")
    assert result.evidence_gate["passed"] is False
    assert result.anchors.selected_threshold.isna().all()


def test_capacity_reports_unavailable_rather_than_creating_a_missing_threshold():
    rng = np.random.RandomState(7)
    flat = pd.DataFrame({"score": rng.randint(0, 101, 12000)})
    flat["response"] = rng.binomial(1, .3, len(flat))
    flat["outcome"] = rng.binomial(1, .05, len(flat))
    result = fit_behavior_thresholds(flat, "score", "response")
    table = build_threshold_table(flat, "score", response_col="response", outcome_col="outcome")
    capacity = apply_capacity(table, result.anchors, CapacityConfig(K=1000, period="cohort"))
    assert (capacity.table.status == "unavailable_behavior_threshold").all()
    assert capacity.table.operational_threshold.isna().all()
