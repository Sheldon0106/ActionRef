import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def load_example(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'examples'/(name+'.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_paper_count_algebra_and_separate_action_denominator():
    tables = load_example('reproduce_paper').calculate()
    results = tables['table3_operating_results']
    row = results.loc[results.cohort.eq('MIMIC held-out') & results.threshold.eq(34)].iloc[0]
    assert row.policy_N == 134146
    assert row.observed_action_yield == 14024/25234
    assert row.observed_action_yield != 14024/25352
    assert round(row.FAE_per_1000, 2) == 422.31
    sensitivity = tables['fixed_R_sensitivity']
    for cohort, expected, low_r, high_r in [('MIMIC held-out', 22327/1075, 20, 25),
                                          ('Stanford transport', 22603/860, 25, 30)]:
        frame = sensitivity.loc[sensitivity.cohort.eq(cohort)]
        np.testing.assert_allclose(frame.equality_R, expected)
        assert frame.loc[frame.R.eq(low_r), 'delta_FAE_per_1000_34_minus_27'].iloc[0] < 0
        assert frame.loc[frame.R.eq(high_r), 'delta_FAE_per_1000_34_minus_27'].iloc[0] > 0


def test_early_warning_reference_values_and_shared_qsofa_level():
    folder = ROOT / 'results/early_warning_scores'
    anchors = pd.read_csv(folder / 'default/reference_point_anchors.csv')
    learning = anchors.loc[anchors.cohort.eq('MIMIC_learning')]
    for score, expected in [('NEWS2', [2, 3, 7]), ('MEWS', [2, 4, 6]), ('REMS', [3, 11, 12])]:
        values = learning.loc[learning.score.eq(score)].set_index('level')
        assert values.loc[['Low', 'Mid', 'High'], 'selected_threshold'].tolist() == expected
    assert learning.loc[learning.score.eq('qSOFA'), 'selected_threshold'].isna().all()
    short = pd.read_csv(folder / 'qsofa_short_scale/reference_point_anchors.csv')
    for _, values in short.groupby('cohort'):
        values = values.set_index('level')
        assert values.loc[['Low', 'Mid', 'High'], 'selected_threshold'].tolist() == [1, 1, 2]
        assert not values.loc['Low', 'operational_representative']
        assert values.loc['Mid', 'operational_representative']


def test_four_score_rates_and_transport_use_manuscript_denominators():
    table = load_example('reproduce_paper').calculate_early_warning_scores()
    assert len(table) == 24
    mimic = table.loc[table.cohort.eq('MIMIC held-out')]
    for score, alerts, sensitivity, denominator in [
        ('ESRP', 363.4, 74.1, 134146), ('NEWS2', 187.5, 42.9, 134146),
        ('MEWS', 236.0, 45.1, 134146), ('REMS', 569.6, 84.1, 134146),
    ]:
        row = mimic.loc[mimic.score.eq(score) & mimic.reference.eq('Low')].iloc[0]
        assert row.policy_N == denominator
        assert round(row.alerts_per_1000, 1) == alerts
        assert round(100 * row.sepsis_sensitivity, 1) == sensitivity
    stanford = table.loc[table.cohort.eq('Stanford transport')]
    assert stanford.policy_N.eq(118385).all()
    mews = stanford.loc[stanford.score.eq('MEWS') & stanford.reference.eq('Mid')].iloc[0]
    assert mews.threshold == 4  # Local Stanford Mid = 3 must not replace transported Mid = 4.
    assert round(mews.alerts_per_1000, 1) == 54.3
    assert round(100 * mews.sepsis_sensitivity, 1) == 24.8


def test_current_uncertainty_families_and_default_qsofa_not_run():
    root = ROOT / 'results'
    points = pd.read_csv(root / 'sepsis_primary/operating_uncertainty/operating_points.csv')
    assert len(points) == 8 and points.bootstrap_B.eq(1000).all()
    assert set(points.policy_id) == {'ESRP_MIMIC_primary_Low', 'ESRP_MIMIC_primary_Mid',
                                      'ESRP_MIMIC_primary_High', 'modeled_R_candidate'}
    conventional = pd.read_csv(root / 'sepsis_primary/conventional_rules/comparator_operating_results_extended.csv')
    assert conventional.bootstrap_B.eq(200).all()
    diagnostics = pd.read_csv(root / 'early_warning_scores/default/reference_point_diagnostics.csv')
    qsofa = diagnostics.loc[diagnostics.score.eq('qSOFA')]
    assert len(qsofa) == 2 and qsofa.bootstrap_status.eq('not run').all()
    summary = pd.read_csv(root / 'early_warning_scores/default/reference_bootstrap_summary.csv')
    assert not summary.score.eq('qSOFA').any()  # No draws is not zero success out of 500.
    short = pd.read_csv(root / 'early_warning_scores/qsofa_short_scale/reference_bootstrap_summary.csv')
    assert short.candidate_available_replicates.eq(500).all()
    assert short.loc[short.level.eq('Low'), 'independently_retained_replicates'].eq(0).all()
    assert short.loc[short.level.ne('Low'), 'independently_retained_replicates'].eq(500).all()


def test_primary_missingness_uses_current_outcome_without_old_linkage_mask():
    runner = load_example('sepsis_paper_analysis')
    frame = pd.DataFrame({'subject_id': [1, 2, 3, 4], 'score_ESRP_new': [10]*4,
        'sepsis3_new': [0, 0, 1, 1], 'outcome_sepsis3': [1]*4,
        'lactate_flag': [1, 0, 0, 1], 'icu_fluid_flag': [np.nan, 0, np.nan, 0],
        'vasopressor_flag': [0]*4, 'steroid_flag': [0]*4, 'legacy_data_available': [1]*4,
        'legacy_subject_id_discordant': [0, 0, 0, 1], 'legacy_hadm_id_discordant': [0]*4})
    out = runner.prepare_mimic(frame)
    np.testing.assert_allclose(out.response, [1, 0, np.nan, 1], equal_nan=True)
    np.testing.assert_array_equal(out.outcome, [0, 0, 1, 1])
    counts = runner.fixed_counts(out, [10], 'example').iloc[0]
    assert counts.policy_N == 4
    assert counts.flagged_N == 4
    assert counts.action_known_flagged_N == 3
    assert counts.observed_action_yield == 2/3


def test_stanford_uses_corrected_score_and_current_clinical_outcome():
    runner = load_example('sepsis_paper_analysis')
    frame = pd.DataFrame({'score_corrected': [34, 27], 'score_ESRP': [31, 26],
        'sepsis3_new': [0, 1], 'outcome_sepsis3': [1, 0], 'fluid_6h': [2000, np.nan],
        'lactate_flag': [0, 0], 'vasopressor_flag': [0, 0], 'steroid_flag': [0, 0]})
    out = runner.prepare_stanford(frame)
    np.testing.assert_array_equal(out.score, [34, 27])
    np.testing.assert_array_equal(out.outcome, [0, 1])
    np.testing.assert_allclose(out.response, [1, np.nan], equal_nan=True)


def test_authorized_data_runner_on_synthetic_inputs():
    runner = load_example('sepsis_paper_analysis')
    rng = np.random.RandomState(719)
    n = 8000
    score = rng.randint(0, 101, n)
    action = rng.binomial(1, .05 + .92/(1+np.exp(-(score-45)/8)))
    frame = pd.DataFrame({'subject_id': np.repeat(np.arange(n//2), 2), 'score_ESRP_new': score,
        'sepsis3_new': rng.binomial(1, .03+.45*(score/100)**2), 'lactate_flag': action,
        'icu_fluid_flag': 0, 'vasopressor_flag': 0, 'steroid_flag': 0})
    config = json.loads((ROOT/'configs/sepsis_primary.json').read_text(encoding='utf-8'))
    config['action_probability']['bootstrap_replicates'] = 4
    result = runner.analyze(frame, config)
    assert result['summary']['source_N'] == n
    low = result['summary']['references']['Low']
    assert result['selection']['behavior_threshold'] == low
    assert result['selection']['same_or_lower_workload_alert_count'] <= result['selection']['behavior_alert_count']
    assert result['evaluation'].metadata['group_N'] > 0
    assert set(result['operating'].cohort) == {'MIMIC learning', 'MIMIC held-out'}


def test_reported_esrp_tiers_and_derivation_loss_curve():
    extended = load_example('reproduce_extended')
    curve = extended.check_primary()
    row = curve.loc[curve.threshold.eq(34)].iloc[0]
    assert (row.N, row.TP, row.FP, row.FN, row.TN) == (314658, 6272, 53577, 5827, 248982)
    assert round(row.FAE_per_1000, 2) == 430.52
    assert curve.loc[curve.alert_N.gt(116236), 'threshold'].tolist() == list(range(27))
    tiers = pd.read_csv(ROOT / 'results/sepsis_primary/conventional_rules/esrp_tier_boundaries.csv')
    expected = {
        ('MIMIC internal validation set', 21): (4953, 86411, 253, 42529, 34106, 90393),
        ('MIMIC internal validation set', 31): (3177, 29456, 2029, 99484, 16972, 32501),
        ('Stanford external validation cohort', 21): (3656, 80034, 153, 34542, 30407, 83690),
        ('Stanford external validation cohort', 31): (2606, 23530, 1203, 91046, 14857, 26136),
    }
    for key, counts in expected.items():
        row = tiers.loc[tiers.cohort.eq(key[0]) & tiers.threshold.eq(key[1])].iloc[0]
        assert tuple(row[['TP', 'FP', 'FN', 'TN', 'action_positive_flagged_N', 'action_known_flagged_N']]) == counts


def test_extended_subgroup_join_retains_point_only_calibration():
    tables = load_example('reproduce_extended').calculate()
    assert {k: len(v) for k, v in tables.items()} == {
        'minimax_regret.csv': 6, 'transfer_target_sensitivity.csv': 3,
        'original_eight_scenarios.csv': 192, 'conventional_selection_uncertainty.csv': 6,
        'subgroup_diagnostics.csv': 96,
    }
    subgroups = tables['subgroup_diagnostics.csv']
    keys = ['cohort', 'subgroup_variable', 'subgroup']
    assert len(subgroups[keys].drop_duplicates()) == 32
    assert subgroups.calibration_bootstrap_requested_B.eq(0).all()
    assert subgroups.groupby(keys).calibration_slope.nunique().le(1).all()
    assert set(subgroups.level) == {'Low', 'Mid', 'High'}
    for name, frame in tables.items():
        saved = pd.read_csv(ROOT / 'results/supplement_extended' / name)
        pd.testing.assert_frame_equal(frame, saved, check_dtype=False, rtol=1e-13, atol=1e-13)


def test_learning_grid_is_separate_from_fixed_pair_sensitivity():
    import pandas as pd
    data = ROOT / 'results/sepsis_primary'
    grid = pd.read_csv(data / 'learning_R_selection.csv')
    assert grid.learning_N.eq(314658).all() and grid.Low_alert_ceiling.eq(116236).all()
    assert grid.loc[grid.R.eq(20), 'low_ceiling_threshold'].iloc[0] == 31
    assert grid.loc[grid.R.eq(20), 'unconstrained_threshold'].iloc[0] == 31
    assert grid.loc[grid.R.eq(100), 'low_ceiling_threshold'].iloc[0] == 27
    invariance = pd.read_csv(data / 'learning_R_invariance.csv')
    np.testing.assert_allclose(invariance.reference_ratio, 11299 / 804)
    np.testing.assert_allclose(invariance.ratio_band_high, 16)
    assert invariance.distinct_thresholds.tolist() == [15, 13]
    fixed = pd.read_csv(data / 'fixed_candidate_R_sensitivity.csv')
    assert 'low_ceiling_threshold' not in fixed.columns
