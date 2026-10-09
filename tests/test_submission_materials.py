"""Check the reported additional applications and their publication boundaries."""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def example(name):
    examples = str(ROOT / 'examples')
    if examples not in sys.path:
        sys.path.insert(0, examples)
    spec = importlib.util.spec_from_file_location(name, ROOT / 'examples' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_corrected_copd_keeps_partial_output_and_excludes_score_fitting_patients():
    tables = example('reproduce_additional').calculate()
    anchors = tables['etable21_copd_references'].set_index('level')
    assert anchors.loc['High', 'attainability_status'] == 'unavailable_ordering'
    assert np.isnan(anchors.loc['High', 'selected_threshold'])
    assert anchors.loc['High', 'semantic_threshold_raw'] < anchors.loc['Mid', 'semantic_threshold_raw']
    stability = tables['etable39_copd_reference_uncertainty'].set_index('level')
    assert stability.loc['High', 'available_replicates'] == 142
    assert np.isfinite(stability.loc['High', 'median'])  # Available draws cannot fill the missing point reference.
    subset = tables['etable41_copd_predictive'].set_index('cohort').loc['heldout_score_fit_excluded']
    assert (subset.patients, subset.encounters, subset.outcome_positive) == (13978, 15221, 91)
    assert round(float(subset.AUROC), 3) == .894


def test_aert_replays_all_reported_settings_without_promoting_default_abstention():
    tables = example('reproduce_aert').calculate()
    refs = tables['etable33_reference_replay']
    row = refs.loc[refs.analysis.eq('3h_report_evidence_strict_baseline_raw')
                   & refs.scale.eq('native') & refs.policy.eq('package_default_8')].iloc[0]
    assert row.references == {} and not row.any_anchor
    main = tables['table4_aert']
    assert dict(zip(main.level, main.threshold)) == {'Mid': 3., 'High': 6.}
    assert main.N.eq(756).all()
    operating = tables['supplementary_data1_operating']
    native = operating.loc[operating.scale.eq('native')]
    assert len(native) == 55
    assert (native.policy == 'short_semantic_tail_guarded_v2').sum() == 31
    shifted = operating.loc[operating.scale.eq('fill1')]
    paired = native.merge(shifted, on=['analysis', 'policy', 'level'], suffixes=('_native', '_shifted'))
    np.testing.assert_allclose(paired.threshold_shifted, paired.threshold_native + 1)
    for metric in ['N', 'TP', 'FP', 'FN', 'TN', 'alert_count', 'response_captured']:
        np.testing.assert_allclose(paired[metric + '_shifted'], paired[metric + '_native'])


def test_aert_terminal_tail_veto_includes_sparse_high_scores():
    policy = example('aert_reference_policy')
    counts = np.array([300] * 7 + [15, 15])
    positive = np.array([30, 60, 90, 120, 150, 180, 210, 0, 0])
    tail = policy.evaluate_tail_guard(counts, positive)
    assert tail['v2_registered_contrasts'] == 72
    assert tail['v2_shape_veto']
    output, _ = policy.fit_both(counts, positive)
    assert not output[0][policy.V2]['any_anchor']


def test_learning_grid_is_separate_from_fixed_pair_sensitivity():
    import pandas as pd
    data = ROOT / 'results/sepsis_primary'
    grid = pd.read_csv(data / 'learning_R_selection.csv')
    assert grid.learning_N.eq(297476).all() and grid.Low_alert_ceiling.eq(109888).all()
    assert grid.loc[grid.R.eq(20), 'low_ceiling_threshold'].iloc[0] == 28
    assert grid.loc[grid.R.eq(20), 'unconstrained_threshold'].iloc[0] == 26
    assert grid.loc[grid.R.eq(100), 'low_ceiling_threshold'].iloc[0] == 27
    invariance = pd.read_csv(data / 'learning_R_invariance.csv')
    np.testing.assert_allclose(invariance.reference_ratio, 11299 / 804)
    np.testing.assert_allclose(invariance.ratio_band_high, 11299 / 804)
    assert invariance.distinct_thresholds.tolist() == [14, 11]
    fixed = pd.read_csv(data / 'fixed_candidate_R_sensitivity.csv')
    assert 'low_ceiling_threshold' not in fixed.columns
