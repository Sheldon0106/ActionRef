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
    row = results.loc[results.cohort.eq('MIMIC held-out') & results.threshold.eq(31)].iloc[0]
    assert row.policy_N == 127528
    assert row.observed_action_yield == 16909/30834
    assert row.observed_action_yield != 16909/30952
    assert round(row.FAE_per_1000, 2) == 478.51
    sensitivity = tables['etable37_fixed_R_sensitivity']
    for cohort, expected, low_r, high_r in [('MIMIC held-out', 14798/861, 15, 20),
                                          ('Stanford transport', 15778/701, 20, 25)]:
        frame = sensitivity.loc[sensitivity.cohort.eq(cohort)]
        np.testing.assert_allclose(frame.equality_R, expected)
        assert frame.loc[frame.R.eq(low_r), 'delta_FAE_per_1000_31_minus_27'].iloc[0] < 0
        assert frame.loc[frame.R.eq(high_r), 'delta_FAE_per_1000_31_minus_27'].iloc[0] > 0


def test_primary_missingness_and_linkage_eligibility():
    runner = load_example('sepsis_paper_analysis')
    frame = pd.DataFrame({'subject_id': [1, 2, 3, 4], 'score_ESRP_new': [10]*4,
        'outcome_sepsis3': [0]*4, 'lactate_flag': [1, 0, 0, 1], 'icu_fluid_flag': [np.nan, 0, np.nan, 0],
        'vasopressor_flag': [0]*4, 'steroid_flag': [0]*4, 'legacy_data_available': [1]*4,
        'legacy_subject_id_discordant': [0, 0, 0, 1], 'legacy_hadm_id_discordant': [0]*4})
    out = runner.prepare_mimic(frame)
    np.testing.assert_allclose(out.response, [1, 0, np.nan, np.nan], equal_nan=True)
    counts = runner.fixed_counts(out, [10], 'example').iloc[0]
    assert counts.policy_N == 4
    assert counts.flagged_N == 4
    assert counts.action_known_flagged_N == 2
    assert counts.observed_action_yield == .5


def test_authorized_data_runner_on_synthetic_inputs():
    runner = load_example('sepsis_paper_analysis')
    rng = np.random.RandomState(719)
    n = 8000
    score = rng.randint(0, 101, n)
    action = rng.binomial(1, .05 + .92/(1+np.exp(-(score-45)/8)))
    frame = pd.DataFrame({'subject_id': np.repeat(np.arange(n//2), 2), 'score_ESRP_new': score,
        'outcome_sepsis3': rng.binomial(1, .03+.45*(score/100)**2), 'lactate_flag': action,
        'icu_fluid_flag': 0, 'vasopressor_flag': 0, 'steroid_flag': 0, 'legacy_v7_primary_eligible': 1})
    config = json.loads((ROOT/'configs/sepsis_primary.json').read_text(encoding='utf-8'))
    config['action_probability']['bootstrap_replicates'] = 4
    result = runner.analyze(frame, config)
    assert result['summary']['source_N'] == n
    low = result['summary']['references']['Low']
    assert result['selection']['behavior_threshold'] == low
    assert result['selection']['same_or_lower_workload_alert_count'] <= result['selection']['behavior_alert_count']
    assert result['evaluation'].metadata['group_N'] > 0
    assert set(result['operating'].cohort) == {'MIMIC learning', 'MIMIC held-out'}
