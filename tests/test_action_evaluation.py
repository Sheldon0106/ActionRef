import numpy as np
import pandas as pd
import pytest

from universal_cutoff import evaluate_action_curve, predict_action_probability


def test_interpolation_endpoints_missing_scores_and_curve_immutability():
    curve = pd.DataFrame({'score': [10, 20, 30], 'isotonic_rate': [.1, .4, .9]})
    before = curve.copy(deep=True)
    got = predict_action_probability([0, 10, 15, 25, 40, np.nan, np.inf], curve)
    np.testing.assert_allclose(got, [.1, .1, .25, .65, .9, np.nan, np.nan], equal_nan=True)
    pd.testing.assert_frame_equal(curve, before)


@pytest.mark.parametrize('x,p', [([0, 0], [0, 1]), ([1, 0], [0, 1]),
                                 ([0, 1], [.8, .2]), ([0, 1], [0, 1.1])])
def test_invalid_probability_maps_are_rejected(x, p):
    with pytest.raises(ValueError):
        predict_action_probability([.5], pd.DataFrame({'score': x, 'isotonic_rate': p}))


def test_complete_action_denominator_is_separate_from_all_score_rows():
    curve = pd.DataFrame({'score': [0, 1], 'isotonic_rate': [0, 1]})
    frame = pd.DataFrame({'s': [0, 1, 1, np.nan, np.inf], 'a': [0, 1, np.nan, 0, 1]})
    result = evaluate_action_curve(frame, 's', 'a', curve, .25)
    assert result.points['N'] == 2
    assert result.metadata['excluded_N'] == 3
    assert result.points['action_Brier'] == 0
    assert result.points['constant_development_rate_Brier'] == .3125
    assert result.reliability.N.sum() == 2
    assert result.reliability.iloc[-1].N == 1  # p=1 belongs to the last bin
    assert result.reliability.loc[result.reliability.N.eq(0), 'observed'].isna().all()


def test_paired_cluster_intervals_preserve_all_encounters_per_patient():
    curve = pd.DataFrame({'score': [0, 1], 'isotonic_rate': [0, 1]})
    frame = pd.DataFrame({'s': [0]*2+[1]*5, 'a': [0]*2+[1]*5, 'patient': [11]*2+[22]*5})
    result = evaluate_action_curve(frame, 's', 'a', curve, .5, 'patient', 200, 19)
    ci = result.intervals.set_index('metric')
    # Resampling both patients with replacement yields N=4, 7 or 10, not fixed N=7.
    assert ci.loc['N', 'lower_025'] == 4
    assert ci.loc['N', 'upper_975'] == 10
    assert result.metadata['group_N'] == 2
    assert ci.loc['delta_Brier_vs_constant', 'lower_025'] == -.25
    assert ci.loc['delta_Brier_vs_constant', 'upper_975'] == -.25
    assert ci.loc['Brier_skill', 'lower_025'] == 1
    with pytest.raises(ValueError, match='group_col'):
        evaluate_action_curve(frame, 's', 'a', curve, .5, n_bootstrap=2)
    frame.loc[0, 'patient'] = np.nan
    with pytest.raises(ValueError, match='nonmissing group'):
        evaluate_action_curve(frame, 's', 'a', curve, .5, 'patient', 2)


def test_constant_perfect_comparator_has_undefined_skill_not_zero():
    curve = pd.DataFrame({'score': [0, 1], 'isotonic_rate': [0, .5]})
    frame = pd.DataFrame({'s': [0, 0], 'a': [0, 0]})
    result = evaluate_action_curve(frame, 's', 'a', curve, 0)
    assert np.isnan(result.points['Brier_skill'])
    assert result.points['diagnostic_status'] == 'insufficient_group_support'
