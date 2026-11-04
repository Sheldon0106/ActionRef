"""Recalculate sepsis summaries from shared aggregate counts and estimates.

No clinical data are loaded or models fitted. Learning R-grid choices are replayed
from saved confusion counts; evaluation thresholds remain fixed.
Run from a repository checkout: python examples/reproduce_paper.py
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'results/sepsis_primary'
EARLY_WARNING_SOURCE = ROOT / 'results/early_warning_scores/default'


def verify_sources(source):
    manifest = json.loads((source / 'manifest.json').read_text(encoding='utf-8'))
    for name, record in manifest['files'].items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != record['sha256']:
            raise ValueError('Source checksum mismatch: ' + name)
    record = manifest['config']
    if hashlib.sha256((ROOT / record['path']).read_bytes()).hexdigest() != record['sha256']:
        raise ValueError('Paper configuration checksum mismatch')
    return json.loads((ROOT / record['path']).read_text(encoding='utf-8'))


def calculate(source=SOURCE):
    source = Path(source)
    protocol = verify_sources(source)
    ratio = protocol['candidate']['R_numerator'] / protocol['candidate']['R_denominator']
    counts = pd.read_csv(source / 'operating_counts.csv')
    actions = pd.read_csv(source / 'observed_action_yield.csv')
    keys = ['cohort', 'threshold']
    if counts.duplicated(keys).any() or actions.duplicated(keys).any():
        raise ValueError('Duplicate cohort/threshold source rows')
    if not counts[['TP', 'FP', 'FN', 'TN']].sum(axis=1).eq(counts.policy_N).all():
        raise ValueError('Confusion counts do not sum to policy_N')
    if not ((actions.action_positive_flagged_N <= actions.action_known_flagged_N)
            & (actions.action_known_flagged_N <= actions.flagged_N)).all():
        raise ValueError('Invalid action denominators')
    recomputed_yield = actions.action_positive_flagged_N / actions.action_known_flagged_N
    np.testing.assert_allclose(recomputed_yield, actions.observed_action_yield, rtol=0, atol=1e-12)
    actions['observed_action_yield'] = recomputed_yield
    table = counts.merge(actions, on=keys, how='left', validate='one_to_one')
    if table.observed_action_yield.isna().any() or not (table.TP + table.FP).eq(table.flagged_N).all():
        raise ValueError('Operating counts and action counts do not match')
    table['R'] = ratio
    table['alerts_per_1000'] = 1000 * table.flagged_N / table.policy_N
    table['recall'] = table.TP / (table.TP + table.FN)
    table['unflagged_outcomes_per_1000'] = 1000 * table.FN / table.policy_N
    table['FAE_per_1000'] = 1000 * (table.FP + ratio * table.FN) / table.policy_N
    table3 = table.loc[table.cohort != 'MIMIC learning'].copy()
    sensitivities, comparisons = [], []
    for cohort, frame in table3.groupby('cohort', sort=False):
        ref = frame.loc[frame.threshold.eq(27)].iloc[0]
        cand = frame.loc[frame.threshold.eq(34)].iloc[0]
        if cand.policy_N != ref.policy_N:
            raise ValueError('Fixed comparison requires the same policy denominator')
        d_fp, d_fn = int(cand.FP - ref.FP), int(cand.FN - ref.FN)
        crossing = -d_fp / d_fn
        for r in protocol['R_grid']:
            sensitivities.append(dict(cohort=cohort, R=r,
                delta_FAE_per_1000_34_minus_27=1000 * (d_fp + r * d_fn) / ref.policy_N,
                equality_R=crossing))
        comparisons.append(dict(cohort=cohort, policy_N=int(ref.policy_N),
            fewer_alerts_per_1000=1000 * (ref.flagged_N-cand.flagged_N)/ref.policy_N,
            fewer_false_positive_alerts_per_1000=-1000*d_fp/ref.policy_N,
            additional_unflagged_outcomes_per_1000=1000*d_fn/ref.policy_N,
            delta_FAE_per_1000=cand.FAE_per_1000-ref.FAE_per_1000,
            relative_FAE_reduction=(ref.FAE_per_1000-cand.FAE_per_1000)/ref.FAE_per_1000,
            equality_R=crossing))
    sensitivity = pd.DataFrame(sensitivities)
    expected = pd.read_csv(source / 'fixed_candidate_R_sensitivity.csv')
    if sensitivity.cohort.tolist() != expected.cohort.tolist():
        raise ValueError('Unexpected sensitivity cohort order')
    np.testing.assert_allclose(sensitivity.select_dtypes('number'), expected.select_dtypes('number'),
                               rtol=0, atol=1e-10)
    points = pd.DataFrame(json.loads((source / 'sepsis_action_points.json').read_text(encoding='utf-8')))
    ci = pd.DataFrame(json.loads((source / 'sepsis_action_intervals.json').read_text(encoding='utf-8')))
    primary = points.loc[points.prediction.eq('continuous_interpolation')].iloc[0]
    binned = points.loc[points.prediction.eq('bin_assignment_sensitivity')].iloc[0]
    metrics = ['action_rate', 'mean_predicted', 'calibration_gap', 'action_Brier',
               'constant_development_rate_Brier', 'delta_Brier_vs_constant', 'Brier_skill',
               'action_log_loss', 'calibration_intercept', 'calibration_slope']
    probability = []
    for name in metrics:
        interval = ci.loc[ci.metric.eq(name)]
        if not interval.empty:
            np.testing.assert_allclose(interval.point, primary[name], rtol=0, atol=1e-12)
        probability.append(dict(metric=name, continuous_interpolation=primary[name],
            lower_025=interval.lower_025.iloc[0] if not interval.empty else np.nan,
            upper_975=interval.upper_975.iloc[0] if not interval.empty else np.nan,
            bin_assignment_sensitivity=binned[name]))
    reliability = pd.DataFrame(json.loads((source / 'sepsis_action_reliability.json').read_text(encoding='utf-8')))
    if int(reliability.N.sum()) != int(primary.N):
        raise ValueError('Reliability counts and point-estimate denominator disagree')
    learning_selection, learning_invariance = calculate_learning_R_selection(source)
    return {'learning_R_selection': learning_selection, 'learning_R_invariance': learning_invariance,
            'table3_operating_results': table3, 'action_counts': actions,
            'action_probability': pd.DataFrame(probability),
            'fixed_R_sensitivity': sensitivity,
            'fixed_candidate_comparison': pd.DataFrame(comparisons)}


def calculate_learning_R_selection(source=SOURCE):
    """Replay the saved learning-grid arithmetic, without fitting or resampling."""
    source = Path(source)
    protocol = verify_sources(source)
    folder = source / 'consequence_scenarios'
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    name = 'comparator_development_selection_curve.csv'
    if hashlib.sha256((folder / name).read_bytes()).hexdigest() != manifest['files'][name]['sha256']:
        raise ValueError('Learning threshold-curve checksum mismatch')
    curve = pd.read_csv(folder / name)
    expected = pd.read_csv(source / 'learning_R_selection.csv')
    n = protocol['expected']['learning_score_N']
    ceiling = protocol['candidate']['learning_workload_ceiling']
    if not curve[['TP', 'FP', 'FN', 'TN']].sum(axis=1).eq(n).all():
        raise ValueError('Learning confusion counts do not sum to the cohort denominator')
    rows = []
    for ratio in expected.R:
        chosen = []
        for capacity in [None, ceiling]:
            eligible = curve if capacity is None else curve.loc[curve.alert_N.le(capacity)]
            ranked = eligible.assign(loss=eligible.FP + ratio * eligible.FN).sort_values(
                ['loss', 'alert_N', 'threshold'], ascending=[True, False, True])
            chosen.append(int(ranked.iloc[0].threshold))
        rows.append(dict(R=ratio, unconstrained_threshold=chosen[0],
                         low_ceiling_threshold=chosen[1], learning_N=n, Low_alert_ceiling=ceiling))
    selection = pd.DataFrame(rows)
    np.testing.assert_allclose(selection, expected, rtol=0, atol=1e-10)
    reference_ratio = protocol['candidate']['R_numerator'] / protocol['candidate']['R_denominator']
    candidate = protocol['candidate']['threshold']
    bands = []
    for column, capacity in [('unconstrained_threshold', None), ('low_ceiling_threshold', ceiling/n)]:
        matching = selection.loc[selection[column].eq(candidate), 'R']
        bands.append(dict(K_frac=capacity, threshold_at_reference=candidate,
                          ratio_band_low=matching.min(), ratio_band_high=matching.max(),
                          distinct_thresholds=selection[column].nunique(), reference_ratio=reference_ratio,
                          grid_low=selection.R.min(), grid_high=selection.R.max()))
    invariance = pd.DataFrame(bands)
    np.testing.assert_allclose(invariance, pd.read_csv(source / 'learning_R_invariance.csv'),
                               rtol=0, atol=1e-10, equal_nan=True)
    return selection, invariance


def calculate_early_warning_scores(source=SOURCE, early_warning_source=EARLY_WARNING_SOURCE):
    """Recalculate four-score rates without selecting or re-estimating thresholds."""
    early_warning_source = Path(early_warning_source)
    manifest = json.loads((early_warning_source / 'manifest.json').read_text(encoding='utf-8'))
    for name, record in manifest['files'].items():
        if hashlib.sha256((early_warning_source / name).read_bytes()).hexdigest() != record['sha256']:
            raise ValueError('Early-warning source checksum mismatch: ' + name)
    saved = pd.read_csv(early_warning_source / 'fixed_reference_operating_points.csv')
    if saved.duplicated(['cohort', 'score', 'reference']).any():
        raise ValueError('Duplicate early-warning operating rows')
    if set(saved.score) != {'NEWS2', 'MEWS', 'REMS'} or len(saved) != 18:
        raise ValueError('The four-score comparison requires three supported comparator scores at both sites')
    if not saved.reference_source.eq('MIMIC_learning').all():
        raise ValueError('The four-score comparison applies MIMIC references unchanged')
    denominators = saved.cohort.map({'MIMIC_heldout': 134146, 'Stanford': 118385})
    if denominators.isna().any() or not saved.score_evaluable_N.eq(denominators).all():
        raise ValueError('Unexpected early-warning evaluation denominator')
    if not saved[['TP', 'FP', 'FN', 'TN']].sum(axis=1).eq(denominators).all():
        raise ValueError('Early-warning confusion counts do not sum to the evaluation denominator')
    if not (saved.TP + saved.FP).eq(saved.flagged_N).all():
        raise ValueError('Early-warning alert and confusion counts disagree')
    alerts = 1000 * saved.flagged_N / denominators
    sensitivity = saved.TP / (saved.TP + saved.FN)
    np.testing.assert_allclose(alerts, saved.flagged_per_1000_scored, rtol=0, atol=1e-10)
    np.testing.assert_allclose(sensitivity, saved.sepsis_recall, rtol=0, atol=1e-12)
    comparators = saved[['cohort', 'score', 'reference', 'threshold', 'TP', 'FP',
                         'FN', 'TN', 'flagged_N']].copy()
    # Preserve historical keys in source files; use manuscript names in reports.
    comparators['score'] = comparators.score.map({'NEWS2': 'NEWS2', 'MEWS': 'MEWS', 'REMS': 'REMS'})
    comparators['cohort'] = comparators.cohort.map(
        {'MIMIC_heldout': 'MIMIC held-out', 'Stanford': 'Stanford transport'})
    comparators['policy_N'] = denominators
    comparators['alerts_per_1000'] = alerts
    comparators['sepsis_sensitivity'] = sensitivity
    esrp = calculate(source)['table3_operating_results']
    esrp = esrp.loc[esrp.threshold.isin([27, 39, 54])].copy()
    esrp['score'] = 'ESRP'
    esrp['reference'] = esrp.threshold.map({27: 'Low', 39: 'Mid', 54: 'High'})
    esrp['sepsis_sensitivity'] = esrp.recall
    expected = esrp.cohort.map({'MIMIC held-out': 134146, 'Stanford transport': 118385})
    if not esrp.policy_N.eq(expected).all() or len(esrp) != 6:
        raise ValueError('Unexpected ESRP evaluation denominator or reference rows')
    return pd.concat([esrp[comparators.columns], comparators], ignore_index=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, default=SOURCE)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'output/paper')
    parser.add_argument('--early-warning-scores', action='store_true',
                        help='Also verify and report four-score rates from saved aggregate counts')
    args = parser.parse_args()
    tables = calculate(args.source_dir)
    if args.early_warning_scores:
        tables['four_score_operating_results'] = calculate_early_warning_scores(args.source_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(args.output_dir / (name + '.csv'), index=False)
    print('Recalculated sepsis operating rates, recorded-action yields and fixed R comparisons; source and arithmetic checks passed.')
    if args.early_warning_scores:
        display = tables['four_score_operating_results'].replace({'cohort': {
            'MIMIC held-out': 'MIMIC internal validation set',
            'Stanford transport': 'Stanford external validation cohort'}})
        print(display[
            ['cohort', 'score', 'reference', 'threshold', 'policy_N',
             'alerts_per_1000', 'sepsis_sensitivity']].to_string(index=False))
    print('Individual action probabilities and bootstrap intervals were not re-estimated.')


if __name__ == '__main__':
    main()
