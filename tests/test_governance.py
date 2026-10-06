import numpy as np
import pandas as pd

from universal_cutoff import (audit_subgroups, audit_temporal, audit_transport,
                              evaluate_frozen_thresholds, normalize_era)


def fixture():
    rng = np.random.RandomState(91)
    score = rng.randint(0, 61, 6000)
    probability = .04 + .90 / (1 + np.exp(-(score - 30) / 6))
    response = rng.binomial(1, probability)
    outcome = rng.binomial(1, np.clip(.02 + .75 * probability, 0, 1))
    return pd.DataFrame({
        "score": score,
        "response": response,
        "outcome": outcome,
        "sex": np.where(np.arange(len(score)) % 2, "F", "M"),
        "insurance": np.where(np.arange(len(score)) % 3, "Admitted", "Not admitted"),
        "era": np.where(np.arange(len(score)) < 3000, "2011 - 2013", "2014\u20132016"),
        "subject": np.arange(len(score)),
    })


def test_frozen_evaluation_never_changes_requested_thresholds():
    frozen = {"Low": 20, "Mid": 30, "High": 40}
    result = evaluate_frozen_thresholds(fixture(), "score", frozen, outcome_col="outcome")
    assert result.frozen_thresholds == frozen
    assert result.table.set_index("level").frozen_threshold.to_dict() == frozen
    assert "cannot move" in result.interpretation_guard


def test_subgroup_roles_and_guards_are_explicit():
    frozen = {"Low": 20, "Mid": 30, "High": 40}
    result = audit_subgroups(
        fixture(), "score", frozen, "insurance", outcome_col="outcome",
        subgroup_role="exploratory_operational_proxy")
    assert set(result.table.subgroup) == {"Admitted", "Not admitted"}
    assert set(result.table.level) == set(frozen)
    assert "operational or downstream proxy" in result.interpretation_guard
    assert "cannot automatically" in result.interpretation_guard


def test_temporal_normalization_overlap_and_local_role():
    data = fixture()
    data.loc[3000, "subject"] = data.loc[0, "subject"]
    result = audit_temporal(
        data, "score", {"Low": 20, "Mid": 30, "High": 40}, "era",
        response_col="response", outcome_col="outcome", subject_col="subject",
        local_module2=True)
    assert normalize_era("2011 - 2013") == "2011-2013"
    assert normalize_era("2014\u20132016") == "2014-2016"
    assert set(result.frozen_performance.era) == {"2011-2013", "2014-2016"}
    assert result.overlap_audit["cross_era_subject_count"] == 1
    assert set(result.local_diagnostic_thresholds.status) == {"local_diagnostic_reestimation"}
    assert "not a bootstrap significance claim" in result.interpretation_guard


def test_transport_keeps_frozen_and_local_diagnostic_tables_separate():
    frozen = {"Low": 20, "Mid": 30, "High": 40}
    result = audit_transport(
        fixture(), "score", frozen, "Synthetic external site",
        response_col="response", outcome_col="outcome", local_module2=True)
    assert set(result.frozen_performance.transport_role) == {"frozen_transport_evaluation"}
    assert set(result.local_diagnostic_thresholds.transport_role) == {
        "local_diagnostic_reestimation"}
    assert result.status["local"] == "completed_local_diagnostic"
    assert "cannot replace" in result.interpretation_guard
