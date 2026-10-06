import numpy as np
import pandas as pd

from universal_cutoff import (CapacityConfig, apply_capacity, audit_cost_governance,
                              build_threshold_table, minimax_regret_cost_audit)
from universal_cutoff.module3b import _select_minimum, lambda_fae_at_threshold


def fixture():
    frame = pd.DataFrame({"score": [1, 1, 2, 2, 3, 3],
                          "response": [0, 0, 0, 1, 1, 1],
                          "outcome": [0, 0, 0, 1, 1, 1]})
    anchors = pd.DataFrame([{"level": "Low", "selected_threshold": 1.0, "provenance_tier": "A"}])
    return build_threshold_table(frame, "score", "response", "outcome"), anchors


def test_capacity_floor_is_conservative_with_ties():
    thresholds, anchors = fixture()
    result = apply_capacity(thresholds, anchors, CapacityConfig(K=3, period="per shift"))
    assert result.table.iloc[0].adjusted_alert_count <= 3
    assert result.table.iloc[0].operational_threshold >= result.table.iloc[0].nominal_threshold


def test_cost_comparators_and_near_regions_are_reported():
    thresholds, _ = fixture()
    result = audit_cost_governance(thresholds, 2, 5)
    assert result.summary["same_or_lower_workload_alert_count"] <= result.summary["behavior_alert_count"]
    assert "unconstrained_comparator_threshold" in result.summary
    assert "constrained_near_abs1_FAE_per_1000_threshold_min" in result.summary


def test_module3b_cannot_redefine_or_mutate_module2_levels():
    thresholds, anchors = fixture()
    before = anchors.copy(deep=True)
    result = audit_cost_governance(thresholds, float(anchors.iloc[0].selected_threshold), 5)
    pd.testing.assert_frame_equal(anchors, before)
    assert not {"level", "selected_threshold", "anchor_name", "provenance_tier"}.intersection(result.summary)
    assert result.summary["behavior_threshold_role"] == "frozen Module 2 input"
    assert result.summary["same_or_lower_workload_threshold_role"] == "Module 3B comparator only"


def test_missing_calibrator_is_unavailable_not_zero_when_binding():
    result = lambda_fae_at_threshold(2, None, 15, True)
    assert result.value is None
    assert result.status == "unavailable_missing_calibrator"


def test_nonbinding_lambda_is_calculated_zero():
    result = lambda_fae_at_threshold(2, None, 15, False)
    assert result.value == 0
    assert result.status == "available_nonbinding"


def test_minimax_regret_is_secondary_and_uses_prespecified_r_grid():
    data = pd.DataFrame({"score": [0, 1, 2, 3, 4, 5],
                         "outcome": [0, 0, 1, 0, 1, 1]})
    thresholds = build_threshold_table(data, "score", outcome_col="outcome")
    result = minimax_regret_cost_audit(thresholds, [1, 3, 9], max_alert_count=4)
    assert result.status == "secondary_minimax_regret_comparator"
    assert result.R_grid == [1.0, 3.0, 9.0]
    assert result.selected_alert_count <= 4
    assert "cannot define" in result.interpretation_guard
    assert set(result.regret_matrix.columns) == {"threshold", "R=1", "R=3", "R=9"}


def test_equal_cost_tie_retains_the_more_inclusive_strategy():
    """V7 contract: among equal-cost strategies, keep the one alerting on more patients."""
    tied = pd.DataFrame({"threshold": [10.0, 20.0],
                         "alert_count": [100, 50],
                         "cost_FAE": [7.0, 7.0]})
    assert int(_select_minimum(tied).alert_count) == 100
    assert float(_select_minimum(tied).threshold) == 10.0
