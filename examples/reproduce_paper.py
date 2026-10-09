"""Rebuild primary paper tables from shared aggregate counts and estimates.

No clinical data are loaded and no thresholds are selected in this entry point.
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
        cand = frame.loc[frame.threshold.eq(31)].iloc[0]
        if cand.policy_N != ref.policy_N:
            raise ValueError('Fixed comparison requires the same policy denominator')
        d_fp, d_fn = int(cand.FP - ref.FP), int(cand.FN - ref.FN)
        crossing = -d_fp / d_fn
        for r in protocol['R_grid']:
            sensitivities.append(dict(cohort=cohort, R=r,
                delta_FAE_per_1000_31_minus_27=1000 * (d_fp + r * d_fn) / ref.policy_N,
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
    return {'table3_operating_results': table3, 'etable35_action_counts': actions,
            'etable36_action_probability': pd.DataFrame(probability),
            'etable37_fixed_R_sensitivity': sensitivity,
            'fixed_candidate_comparison': pd.DataFrame(comparisons)}


def additional_report():
    """Table 4 and eTable 41 from the corrected, supplied-score aggregates."""
    copd_source = ROOT / 'results/copd/validation_v2_corrected'
    copd = pd.read_csv(copd_source / 'tables/operating_comparison.csv')
    copd = copd.loc[copd.response_version.eq('corrected') & copd.cohort.eq('heldout_full')]
    aert = pd.DataFrame(json.loads((ROOT / 'results/aert/test_operating_point.json').read_text(encoding='utf-8')))
    aert = aert.loc[aert.analysis.eq('3h_report_evidence_strict_baseline_raw')
                    & aert.scale.eq('native') & aert.policy.eq('short_semantic_tail_guarded_v2')]
    lines = ['', '## Additional applications (Table 4)', '',
        'COPD is evaluated conditional on the supplied score. AERT is an exploratory',
        'HEART-derived application using the previously inspected patient-disjoint test',
        'partition. The disease-specific outcomes and recorded actions differ.', '',
        '| Application / level | Threshold | Encounters | Alerts /1,000 | Action yield | Outcome recall |',
        '|---|---:|---:|---:|---:|---:|']
    for r in copd.itertuples():
        lines.append('| COPD / {} | {:.4f} | {:,} | {:.1f} | {:.1%} | {:.1%} |'.format(
            r.level, r.frozen_threshold, r.policy_N, r.alerts_per_1000, r.response_yield, r.recall))
    for r in aert.itertuples():
        lines.append('| AERT ADMITTED/HOME / {} | {:g} | {:,} | {:.1f} | {:.1%} | {:.1%} |'.format(
            r.level, r.threshold, r.N, 1000*r.alert_fraction, r.response_yield, r.recall))
    lines += ['', 'COPD action is documented bronchodilator administration/start within 24 hours',
        'OR the legacy Pyxis steroid-record proxy. Its High reference is unavailable:',
        'relative target 0.4278 reaches bin 50 below Mid bin 55, and ordering allows no',
        'replacement. Reference uncertainty is in eTables 21 and 39; operating intervals',
        'are in eTable 22 and the corrected source bundle.', '',
        'AERT Table 4 uses ADMITTED/HOME, with other dispositions excluded. The separate',
        'hospitalization-linkage analysis retains Low 3 in 785 test encounters. The',
        'unchanged eight-bin policy abstains in both strict three-hour baseline settings;',
        'the reported references use the separate short-discrete research extension.',
        'eTables 32–34 and 38 and Supplementary Data 1–2 retain all 16 settings and',
        'their conditional patient-bootstrap summaries. No K, R or FAE is applied to AERT.', '',
        '## COPD evaluation excluding score-fitting patients (eTable 41)', '']
    predictive = pd.read_csv(copd_source / 'tables/predictive_point.csv')
    p = predictive.loc[predictive.cohort.eq('heldout_score_fit_excluded')].iloc[0]
    assert int(p.patients) == 13978 and int(p.encounters) == 15221 and round(float(p.AUROC), 3) == .894
    ci = pd.read_csv(copd_source / 'tables/predictive_intervals.csv')
    auc = ci.loc[ci.cohort.eq(p.cohort) & ci.metric.eq('AUROC')].iloc[0]
    lines += ['The subset contains **13,978 patients / 15,221 encounters**, after excluding',
        'every patient represented in score-fitting rows. AUROC is **0.894**',
        '(95% patient-cluster interval, {:.3f}–{:.3f}). The score, full-learning'.format(auc.CI_2_5, auc.CI_97_5),
        'references and historical preprocessing/rescaling remain fixed; this is a',
        'supplemental evaluation conditional on the supplied score.', '',
        '| Level | Threshold | Flagged / total | Outcome-positive flagged / total | Action yield |',
        '|---|---:|---:|---:|---:|']
    subset = pd.read_csv(copd_source / 'tables/operating_comparison.csv')
    subset = subset.loc[subset.cohort.eq(p.cohort) & subset.response_version.eq('corrected')]
    for r in subset.itertuples():
        lines.append('| {} | {:.4f} | {:,} / {:,} | {} / {} | {:.1%} |'.format(
            r.level, r.frozen_threshold, r.alert_count, r.policy_N, r.TP, r.TP+r.FN, r.response_yield))
    lines += ['', 'See the [evidence guide](evidence.md) for the analysis roles and source-file',
        'mapping. AKI and pneumonia remain development records and are not reported',
        'in the paper.']
    return '\n'.join(lines)


def report(tables):
    lines = ['# Reported paper results', '',
        'These tables summarize the primary sepsis analysis. Behavioral references',
        'were learned from recorded actions. Candidate 31 was selected on MIMIC learning',
        'data with Low 27 as the workload comparator and R = 11,299/804.', '',
        '## Fixed operating results (Table 3)', '',
        'Unflagged counts refer to outcome-positive encounters below the threshold.', '']
    for cohort, frame in tables['table3_operating_results'].groupby('cohort', sort=False):
        lines += ['**{}**'.format(cohort), '',
            '| Threshold | Alerts /1,000 | Action yield | Recall | Unflagged /1,000 | FAE /1,000 |',
            '|---:|---:|---:|---:|---:|---:|']
        for r in frame.itertuples():
            lines.append('| {} | {:.1f} | {:.1%} | {:.1%} | {:.2f} | {:.2f} |'.format(
                r.threshold, r.alerts_per_1000, r.observed_action_yield, r.recall,
                r.unflagged_outcomes_per_1000, r.FAE_per_1000))
        lines.append('')
    lines += ['', 'Action yield uses flagged encounters with known action status. Recall uses',
        'outcome-positive encounters. Per-1,000 rates use 127,528 MIMIC held-out or',
        '118,385 Stanford encounters. FAE is',
        'false-alarm-equivalent loss, FP + R × FN. It is a scenario-weighted count.', '',
        '## Action-probability evaluation (eTable 36)', '',
        'Evaluation uses 126,332 encounters from 60,903 patients. The learning curve and',
        'constant learning-rate comparator are held fixed. Intervals use 200 patient-cluster',
        'resamples and quantify evaluation uncertainty conditional on those predictions.', '',
        '| Metric | Continuous interpolation | 95% interval | Bin-assignment sensitivity |',
        '|---|---:|---|---:|']
    labels = {'action_rate':'Observed action rate', 'mean_predicted':'Mean prediction',
              'calibration_gap':'Predicted minus observed', 'action_Brier':'Brier score',
              'constant_development_rate_Brier':'Constant-rate Brier score',
              'delta_Brier_vs_constant':'Paired Brier difference', 'Brier_skill':'Brier skill',
              'action_log_loss':'Log loss', 'calibration_intercept':'Calibration intercept',
              'calibration_slope':'Calibration slope'}
    for r in tables['etable36_action_probability'].itertuples():
        interval = '{:.5f} to {:.5f}'.format(r.lower_025, r.upper_975) if np.isfinite(r.lower_025) else 'Not estimated'
        lines.append('| {} | {:.5f} | {} | {:.5f} |'.format(labels[r.metric], r.continuous_interpolation,
                                                               interval, r.bin_assignment_sensitivity))
    lines += ['', 'Calibration intercept and slope are descriptive fits to fixed predictions.',
        'The bin-assignment sensitivity is reported as a point estimate.', '',
        '## Fixed 31-versus-27 comparison (eTable 37)', '',
        '| R | MIMIC ΔFAE /1,000 | Stanford ΔFAE /1,000 |', '|---:|---:|---:|']
    for _, rows in tables['etable37_fixed_R_sensitivity'].groupby('R', sort=True):
        m = rows.loc[rows.cohort.eq('MIMIC held-out')].iloc[0]
        s = rows.loc[rows.cohort.eq('Stanford transport')].iloc[0]
        lines.append('| {:.5g} | {:.2f} | {:.2f} |'.format(m.R, m.delta_FAE_per_1000_31_minus_27,
                                                        s.delta_FAE_per_1000_31_minus_27))
    lines += ['', 'ΔFAE = L(31) − L(27). Negative values favor 31 within this fixed pair.',
        'Equality occurs at R = 17.18699 in MIMIC and 22.50785 in Stanford.',
        'Candidates are not reselected on evaluation data. These crossings describe',
        'this pair, not an optimum over all possible thresholds.', '',
        'eTable 37 contains this fixed comparison only. Learning-data re-selection and',
        'R-setting are described in Supplement eMethods 3 and the [R guide](R_GUIDANCE.md).']
    lines += additional_report().splitlines()
    lines += ['',
        '## Reproduction', '',
        'Run `python examples/reproduce_paper.py` from the repository root.',
        'It recomputes operating rates, action yields and R sensitivity from shared counts.',
        'The action-probability estimates and intervals are restored from the reported',
        'aggregate outputs; recomputing them requires encounter-level action and score data.', '',
        'Run `python examples/reproduce_additional.py` for corrected COPD tables and',
        '`python examples/reproduce_aert.py` for the AERT aggregate replay, eTables',
        '32–34 and 38 and Supplementary Data 1–2. Their saved bootstrap intervals are',
        'assembled without reading patient records.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, default=SOURCE)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'output/paper')
    parser.add_argument('--write-docs', action='store_true', help='Also update docs/paper-results.md')
    args = parser.parse_args()
    tables = calculate(args.source_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(args.output_dir / (name + '.csv'), index=False)
    text = report(tables)
    (args.output_dir / 'results.md').write_text(text, encoding='utf-8')
    if args.write_docs:
        (ROOT / 'docs/paper-results.md').write_text(text, encoding='utf-8')
    print('Rebuilt Table 3 and eTables 35–37 from aggregate sources; source and arithmetic checks passed.')
    print('Individual action probabilities and bootstrap intervals were not re-estimated.')


if __name__ == '__main__':
    main()
