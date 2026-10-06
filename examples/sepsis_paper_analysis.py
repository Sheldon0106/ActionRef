"""Run the primary sepsis workflow on separately authorized analysis tables.

Inputs are prepared analysis variables, not raw database exports. See
docs/paper-data.md. Outputs contain aggregate results only.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from universal_cutoff import (audit_cost_governance, build_threshold_table,
                              evaluate_action_curve, fit_behavior_thresholds)
from universal_cutoff.validation import binary_series, validate_columns

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ['lactate_flag', 'icu_fluid_flag', 'vasopressor_flag', 'steroid_flag']
LINKAGE = ['legacy_data_available', 'legacy_subject_id_discordant', 'legacy_hadm_id_discordant']


def missing_aware_or(frame, columns):
    values = frame[columns].apply(pd.to_numeric, errors='coerce')
    values = values.where(values.isin([0, 1]))
    response = pd.Series(np.nan, index=frame.index, dtype=float)
    response.loc[values.eq(1).any(axis=1)] = 1.
    response.loc[values.eq(0).all(axis=1)] = 0.
    return response


def prepare_mimic(frame):
    validate_columns(frame, ['subject_id', 'score_ESRP_new', 'outcome_sepsis3'] + COMPONENTS)
    if frame.subject_id.isna().any():
        raise ValueError('All source rows need a patient identifier before splitting')
    out = frame.copy()
    if 'legacy_v7_primary_eligible' not in out:
        validate_columns(out, LINKAGE)
        links = out[LINKAGE].apply(pd.to_numeric, errors='coerce')
        out['legacy_v7_primary_eligible'] = (links.legacy_data_available.eq(1)
            & links.legacy_subject_id_discordant.eq(0) & links.legacy_hadm_id_discordant.eq(0)).astype(int)
    out['response'] = missing_aware_or(out, COMPONENTS)
    out.loc[~pd.to_numeric(out.legacy_v7_primary_eligible, errors='coerce').eq(1), 'response'] = np.nan
    out['score'] = pd.to_numeric(out.score_ESRP_new, errors='coerce').replace([np.inf, -np.inf], np.nan)
    out['outcome'] = binary_series(out.outcome_sepsis3, 'outcome_sepsis3')
    return out


def prepare_stanford(frame):
    fields = ['score_ESRP', 'outcome_sepsis3', 'fluid_6h', 'lactate_flag', 'vasopressor_flag', 'steroid_flag']
    validate_columns(frame, fields)
    out = frame.copy()
    fluid = pd.to_numeric(out.fluid_6h, errors='coerce')
    out['fluid_component'] = np.where(fluid.notna(), (fluid >= 2000).astype(float), np.nan)
    out['response'] = missing_aware_or(out, ['lactate_flag', 'fluid_component', 'vasopressor_flag', 'steroid_flag'])
    out['score'] = pd.to_numeric(out.score_ESRP, errors='coerce').replace([np.inf, -np.inf], np.nan)
    out['outcome'] = binary_series(out.outcome_sepsis3, 'outcome_sepsis3')
    return out


def fixed_counts(frame, thresholds, cohort):
    d = frame.loc[frame.score.notna()]
    if d.outcome.isna().any():
        raise ValueError('The paper operating analysis requires complete outcomes among valid-score rows')
    rows = []
    for threshold in sorted(set(thresholds)):
        flagged = d.score.ge(threshold)
        known = flagged & d.response.notna()
        tp = int((flagged & d.outcome.eq(1)).sum())
        fp = int((flagged & d.outcome.eq(0)).sum())
        fn = int((~flagged & d.outcome.eq(1)).sum())
        tn = int((~flagged & d.outcome.eq(0)).sum())
        positive = int(d.loc[known, 'response'].sum())
        rows.append(dict(cohort=cohort, threshold=threshold, policy_N=len(d), TP=tp, FP=fp, FN=fn, TN=tn,
                         flagged_N=int(flagged.sum()), action_known_flagged_N=int(known.sum()),
                         action_positive_flagged_N=positive,
                         observed_action_yield=positive/known.sum() if known.any() else np.nan))
    return pd.DataFrame(rows)


def analyze(mimic, protocol, stanford=None, verify_reported=False):
    f = prepare_mimic(mimic)
    cfg = protocol['mimic_split']
    train, test = next(GroupShuffleSplit(n_splits=1, train_size=cfg['train_size'],
        random_state=cfg['random_state']).split(f, groups=f.subject_id))
    learning, heldout = f.iloc[train].copy(), f.iloc[test].copy()
    if not set(learning.subject_id).isdisjoint(set(heldout.subject_id)):
        raise ValueError('Patient overlap between learning and evaluation')
    behavior = fit_behavior_thresholds(learning, 'score', 'response')
    anchors = behavior.anchors.set_index('level').selected_threshold.to_dict()
    low = anchors['Low']
    if not np.isfinite(low):
        raise ValueError('This paper workflow requires a supported Low reference')
    if learning.loc[learning.score.notna(), 'outcome'].isna().any():
        raise ValueError('Candidate selection requires complete learning outcomes')
    learning_table = build_threshold_table(learning, 'score', 'response', 'outcome')
    # Explicit Low comparison; do not use run_framework's Mid-first convenience path.
    c = protocol['candidate']
    ratio = c['R_numerator'] / c['R_denominator']
    selection = audit_cost_governance(learning_table, float(low), R=ratio)
    candidate = selection.summary['same_or_lower_workload_threshold']
    complete = learning.dropna(subset=['score', 'response'])
    rate = float(complete.response.mean())
    curve = behavior.response_curve[['score', 'count', 'observed_rate', 'isotonic_rate']].copy()
    ap = protocol['action_probability']
    evaluation = evaluate_action_curve(heldout, 'score', 'response', curve, rate,
        group_col='subject_id', n_bootstrap=ap['bootstrap_replicates'], random_state=ap['bootstrap_seed'])
    binned = heldout.copy()
    origin = float(complete.score.min())
    width = float(behavior.binning['bin_width'])
    binned['score'] = np.floor((binned.score - origin)/width)*width + origin
    sensitivity = evaluate_action_curve(binned, 'score', 'response', curve, rate)
    thresholds = [t for t in anchors.values() if np.isfinite(t)] + [candidate]
    operating = [fixed_counts(learning, thresholds, 'MIMIC learning'),
                 fixed_counts(heldout, thresholds, 'MIMIC held-out')]
    local = None
    if stanford is not None:
        external = prepare_stanford(stanford)
        operating.append(fixed_counts(external, thresholds, 'Stanford transport'))
        local = fit_behavior_thresholds(external, 'score', 'response').anchors
    operating = pd.concat(operating, ignore_index=True)
    operating['FAE_per_1000'] = 1000 * (operating.FP + ratio * operating.FN) / operating.policy_N
    rs = []
    for cohort, frame in operating.loc[operating.cohort.ne('MIMIC learning')].groupby('cohort', sort=False):
        ref, cand = frame.loc[frame.threshold.eq(low)].iloc[0], frame.loc[frame.threshold.eq(candidate)].iloc[0]
        for r in protocol['R_grid']:
            rs.append(dict(cohort=cohort, R=r, reference_threshold=low, candidate_threshold=candidate,
                delta_FAE_per_1000=1000*((cand.FP-ref.FP)+r*(cand.FN-ref.FN))/ref.policy_N))
    summary = dict(source_N=len(f), learning_N=len(learning), heldout_N=len(heldout),
        learning_action_N=len(complete), learning_actions=int(complete.response.sum()),
        learning_score_N=int(learning.score.notna().sum()), heldout_score_N=int(heldout.score.notna().sum()),
        supported_bin_N=len(curve), supported_encounters=int(curve['count'].sum()),
        heldout_action_N=evaluation.points['N'], heldout_action_patients=evaluation.metadata['group_N'],
        references=anchors, candidate=candidate, bin_width=width,
        learning_workload_ceiling=selection.summary['behavior_alert_count'])
    if verify_reported:
        for key, expected in protocol['expected'].items():
            if key == 'stanford_N':
                if stanford is not None and len(stanford) != expected:
                    raise ValueError('Stanford cohort size differs from the paper')
            elif summary[key] != expected:
                raise ValueError('Paper mismatch: ' + key)
        if anchors != protocol['reference_thresholds'] or candidate != c['threshold'] or width != 3:
            raise ValueError('References, candidate or bin width differ from the paper')
        if summary['learning_workload_ceiling'] != c['learning_workload_ceiling']:
            raise ValueError('Learning workload comparator differs from the paper')
        saved = ROOT / 'results/sepsis_primary'
        np.testing.assert_allclose(curve.to_numpy(), pd.read_csv(saved/'semantic_response_curve.csv')[curve.columns].to_numpy(), rtol=0, atol=1e-10)
        point = json.loads((saved/'sepsis_action_points.json').read_text(encoding='utf-8'))[0]
        for key in ['action_Brier', 'action_rate', 'mean_predicted', 'delta_Brier_vs_constant']:
            np.testing.assert_allclose(evaluation.points[key], point[key], rtol=0, atol=1e-10)
        reported_ci = pd.DataFrame(json.loads((saved/'sepsis_action_intervals.json').read_text(encoding='utf-8')))
        cols = ['lower_025', 'median', 'upper_975']
        np.testing.assert_allclose(evaluation.intervals.set_index('metric')[cols].sort_index(),
            reported_ci.set_index('metric')[cols].sort_index(), rtol=0, atol=1e-10)
        expected_counts = pd.read_csv(saved/'operating_counts.csv')
        expected_actions = pd.read_csv(saved/'observed_action_yield.csv')
        for saved_table, cols in [(expected_counts, ['policy_N', 'TP', 'FP', 'FN', 'TN']),
                                  (expected_actions, ['flagged_N', 'action_known_flagged_N', 'action_positive_flagged_N'])]:
            required = saved_table.loc[saved_table.cohort.isin(operating.cohort.unique())]
            checked = required.merge(operating, on=['cohort', 'threshold'], validate='one_to_one', suffixes=('_expected', '_actual'))
            if len(checked) != len(required):
                raise ValueError('Missing expected operating thresholds')
            for col in cols:
                if not checked[col+'_expected'].eq(checked[col+'_actual']).all():
                    raise ValueError('Paper operating mismatch: ' + col)
        if local is not None and local.set_index('level').selected_threshold.to_dict() != protocol['stanford_local_references']:
            raise ValueError('Stanford local references differ from the paper')
    return dict(summary=summary, references=behavior.anchors, curve=curve, evaluation=evaluation,
                bin_assignment=sensitivity, operating=operating, selection=selection.summary,
                R_sensitivity=pd.DataFrame(rs), stanford_local=local)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mimic', type=Path, required=True)
    parser.add_argument('--stanford', type=Path)
    parser.add_argument('--output-dir', type=Path, default=ROOT/'output/sepsis-analysis')
    parser.add_argument('--verify-reported', action='store_true', help='Fail if supplied cohorts differ from the reported analysis')
    args = parser.parse_args()
    columns = ['subject_id', 'score_ESRP_new', 'outcome_sepsis3', 'legacy_v7_primary_eligible'] + COMPONENTS + LINKAGE
    mimic = pd.read_csv(args.mimic, usecols=lambda col: col in columns, low_memory=False)
    fields = ['score_ESRP', 'outcome_sepsis3', 'fluid_6h', 'lactate_flag', 'vasopressor_flag', 'steroid_flag']
    stanford = pd.read_csv(args.stanford, usecols=fields, low_memory=False) if args.stanford else None
    config = json.loads((ROOT/'configs/sepsis_primary.json').read_text(encoding='utf-8'))
    result = analyze(mimic, config, stanford, args.verify_reported)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for key in ['references', 'curve', 'operating', 'R_sensitivity', 'stanford_local']:
        if result[key] is not None:
            result[key].to_csv(args.output_dir/(key+'.csv'), index=False)
    ev = result['evaluation']
    ev.intervals.to_csv(args.output_dir/'action_intervals.csv', index=False)
    ev.reliability.to_csv(args.output_dir/'action_reliability.csv', index=False)
    pd.DataFrame([dict(prediction='continuous_interpolation', **ev.points),
                  dict(prediction='bin_assignment_sensitivity', **result['bin_assignment'].points)]).to_csv(
                      args.output_dir/'action_points.csv', index=False)
    (args.output_dir/'summary.json').write_text(json.dumps(result['summary'], indent=2), encoding='utf-8')
    (args.output_dir/'action_protocol.json').write_text(json.dumps(ev.metadata, indent=2), encoding='utf-8')
    print('Saved aggregate sepsis results. References and candidates were selected on learning data only.')
    if args.verify_reported:
        print('Reported cohort, reference, candidate, operating count and action-evaluation checks passed.')


if __name__ == '__main__':
    main()
