import numpy as np
import pandas as pd

from universal_cutoff import BootstrapConfig, Module2Config, bootstrap_module2


def fixture():
    rng = np.random.RandomState(719)
    score = rng.randint(0, 101, 4000)
    probability = .08 + .84 / (1 + np.exp(-(score - 48) / 8))
    return pd.DataFrame({"score": score, "response": rng.binomial(1, probability),
                         "subject": np.arange(len(score)) // 2})


def test_bootstrap_is_disabled_by_default():
    result = bootstrap_module2(fixture(), "score", "response")
    assert result.status == "disabled"
    assert result.anchors.empty


def test_enabled_bootstrap_reestimates_and_reports_invariants():
    result = bootstrap_module2(
        fixture(), "score", "response", Module2Config(),
        BootstrapConfig(enabled=True, n_bootstrap=4, group_col="subject", random_state=17),
    )
    assert result.status == "completed"
    assert len(result.joint_tier_audit) == 4
    assert set(result.stability_summary.level) == {"Low", "Mid", "High"}
    assert {"threshold", "probability"}.issubset(result.threshold_frequencies.columns)
    assert set(result.adjacent_gap_summary.gap) == {"low_mid_gap", "mid_high_gap"}
    assert {"level", "provenance_tier", "probability"}.issubset(
        result.provenance_frequencies.columns)
    assert {"bin_width", "valid_bin_count", "probability"}.issubset(
        result.binning_stability.columns)
    assert result.joint_summary["evaluated_replicates"] == 4
    assert result.config["estimated_module2_fits"] == 5
    assert set(result.validated_full_anchors.level) == {"Low", "Mid", "High"}
    pd.testing.assert_series_equal(
        result.validated_full_anchors.set_index("level").selected_threshold,
        result.stability_summary.set_index("level").full_data_threshold,
        check_names=False,
    )
    assert result.failures.empty


def test_bootstrap_replays_deterministically_under_fixed_seed():
    config = BootstrapConfig(enabled=True, n_bootstrap=4, group_col="subject", random_state=17)
    first = bootstrap_module2(fixture(), "score", "response", Module2Config(), config)
    second = bootstrap_module2(fixture(), "score", "response", Module2Config(), config)
    pd.testing.assert_frame_equal(first.anchors, second.anchors)
    pd.testing.assert_frame_equal(first.threshold_frequencies, second.threshold_frequencies)
    pd.testing.assert_frame_equal(first.adjacent_gap_summary, second.adjacent_gap_summary)
    pd.testing.assert_frame_equal(first.provenance_frequencies, second.provenance_frequencies)
    pd.testing.assert_frame_equal(first.binning_stability, second.binning_stability)
    pd.testing.assert_frame_equal(first.changepoint_support, second.changepoint_support)
    pd.testing.assert_frame_equal(first.validated_full_anchors, second.validated_full_anchors)
    assert first.joint_summary == second.joint_summary
