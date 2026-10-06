import numpy as np
import pandas as pd
import pytest

from universal_cutoff.config import Module2Config
from universal_cutoff.exceptions import InsufficientBinsError
from universal_cutoff.module2 import derive_semantic_anchors, fit_behavior_thresholds


def test_supported_monotone_curve_has_absolute_anchors():
    rng = np.random.RandomState(719)
    score = rng.randint(0, 101, 12000)
    p = 0.05 + 0.92 / (1 + np.exp(-(score - 45) / 8))
    result = fit_behavior_thresholds(pd.DataFrame({"s": score, "a": rng.binomial(1, p)}), "s", "a")
    assert result.evidence_gate["passed"]
    assert result.anchors.selected_threshold.notna().all()
    assert set(result.anchors.provenance_tier) == {"A"}


def test_weak_curve_explicitly_abstains():
    score = np.repeat(np.arange(101), 100)
    response = np.tile(np.r_[np.ones(30), np.zeros(70)], 101)
    result = fit_behavior_thresholds(pd.DataFrame({"s": score, "a": response}), "s", "a")
    assert not result.evidence_gate["passed"]
    assert result.anchors.selected_threshold.isna().all()
    assert set(result.anchors.provenance_tier) == {"E"}


def _anchors(curve, prevalence, cps=None):
    return derive_semantic_anchors(
        curve, curve.score, prevalence,
        pd.DataFrame(columns=["cp", "isotonic_rate_at_cp"]) if cps is None else cps,
        1.0, {"passed": True, "reason": "supported"}, Module2Config())


def test_unreachable_low_has_no_fallback():
    curve = pd.DataFrame({"score": np.arange(10), "isotonic_rate": np.linspace(.2, .9, 10)})
    anchors = _anchors(curve, .05)
    low = anchors[anchors.level == "Low"].iloc[0]
    assert np.isnan(low.selected_threshold)
    assert low.provenance_tier == "E"
    assert "no relative fallback" in low.reason


def test_unreachable_mid_high_use_only_prespecified_relative_anchors():
    curve = pd.DataFrame({"score": np.arange(10), "isotonic_rate": np.linspace(.05, .40, 10)})
    anchors = _anchors(curve, .20)
    assert anchors.loc[anchors.level == "Mid", "anchor_family"].iloc[0] == "relative"
    assert anchors.loc[anchors.level == "High", "anchor_family"].iloc[0] == "relative"
    assert set(anchors.loc[anchors.level.isin(["Mid", "High"]), "provenance_tier"]) == {"B"}


def test_changepoint_corroborates_but_never_moves_semantic_threshold():
    curve = pd.DataFrame({"score": np.arange(11), "isotonic_rate": np.linspace(0, 1, 11)})
    cps = pd.DataFrame({"cp": [6.0], "isotonic_rate_at_cp": [.6],
                        "bootstrap_support": [.80], "status": ["supported"]})
    anchors = _anchors(curve, .30, cps)
    mid = anchors[anchors.level == "Mid"].iloc[0]
    assert mid.cp_corroborated
    assert mid.semantic_threshold_operational == 5
    assert mid.selected_threshold == 5
    assert mid.corroborating_cp == 6


def test_pending_or_low_support_changepoint_cannot_corroborate():
    curve = pd.DataFrame({"score": np.arange(11), "isotonic_rate": np.linspace(0, 1, 11)})
    cps = pd.DataFrame({
        "cp": [6.0, 6.0],
        "isotonic_rate_at_cp": [.6, .6],
        "bootstrap_support": [np.nan, .49],
        "status": ["point_evidence_pending_bootstrap", "supported"],
    })
    anchors = _anchors(curve, .30, cps)
    mid = anchors[anchors.level == "Mid"].iloc[0]
    assert not mid.cp_corroborated
    assert mid.selected_threshold == 5
    assert mid.selected_type == "semantic-only"


def test_equal_operational_thresholds_have_one_representative():
    curve = pd.DataFrame({"score": [0, 10, 20], "isotonic_rate": [.1, .85, .9]})
    anchors = _anchors(curve, .5)
    equal = anchors[anchors.selected_threshold == 10]
    assert len(equal) >= 2
    assert int(equal.operational_representative.sum()) == 1


def test_coarse_score_abstains_as_insufficient_bins():
    frame = pd.DataFrame({"s": np.repeat([0, 1, 2], 100), "a": np.tile([0, 1], 150)})
    with pytest.raises(InsufficientBinsError):
        fit_behavior_thresholds(frame, "s", "a")
