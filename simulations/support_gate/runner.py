"""Authorized v8 additive analyses. Existing data, code and outputs are read-only.

Run with -B. Only a new bundle is written; master integration is a separate step.
Synthetic replicates and aggregate clinical results contain no patient identifiers.
"""
from __future__ import annotations

import os
for _k in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS']:
    os.environ[_k] = '1'
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
import argparse
import re
import ast
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, replace
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import sys
import time
import warnings

import numpy as np
import pandas as pd
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.special import expit
from scipy.stats import beta
import statsmodels.api as sm
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupShuffleSplit

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT
sys.path.insert(0, str(PACKAGE / 'src'))
from universal_cutoff.config import Module2Config
from universal_cutoff.exceptions import InsufficientBinsError
from universal_cutoff.module2 import (fit_behavior_thresholds, choose_bin_width,
                                     build_response_curve, derive_semantic_anchors)

MASTER = ROOT / 'cutoff_experiment_master_evidence_handoff.md'
OLD_SIM = ROOT / 'simulation_final_outputs/run_20260913T092841426893Z_727eb2dd9311'
OLD_RUNNER = ROOT / 'simulations/eight_scenarios/runner.py'
OLD_V8 = ROOT / 'v8_outputs/run_20260829T065744238923Z_248d10f0e784'
CURVE = ROOT / 'v8_addendum_outputs/run_20260901T114212647018Z_7a68fbe37684/tables/semantic_response_curve.csv'
ACTION = ROOT / 'built_heart_score/adapted_heart_evidence_v28/run_20261002T082847Z_history_action_calibration'
PRECISION = ROOT / 'bootstrap_precision_addendum_outputs/run_20261005T080004570969Z_2e75da2c1f5d'
COMPARATOR = ROOT / 'sepsis_comparator_actionref_outputs/run_20261010T084546891552Z_7fb192bc1a2b'
QSOFA = ROOT / 'sepsis_comparator_actionref_outputs/run_20261010T093951021453Z_7ef624c3251f'
DATA = ROOT.parent / 'dataset/mimic_analysis/mimic_cohort/master_data_enriched.csv'
SUPPLEMENT = ROOT / 'paper/paper——V5/V7/ActionRef_Supplement_EN_20261010_v7.docx'
LEVELS = ['Low', 'Mid', 'High']
SCENARIOS = ['strong_signal', 'flat_null', 'weak_signal', 'sparse_tail', 'low_ceiling', 'short_3', 'short_4']
DEFAULT = Module2Config()
CONFIG = {
    'analysis': 'v8_support_gate_addendum',
    'default_module2': asdict(DEFAULT),
    'default_changes': [],
    'analyses': [1, 2, 3, 4, 5],
    'simulation': {
        'n': [6000, 2000], 'requested_replicates_per_scenario_n': 200,
        'seed': 2026101101,
        'seed_stream': 'default_rng(SeedSequence([base_seed, scenario_index, n, replicate]))',
        'paired_data': True,
        'methods': {
            'M1_default': 'Unchanged fit_behavior_thresholds with unchanged Module2Config.',
            'M2_no_gate_no_relative': 'Same default-selected bin width, min_bin_n=40 and isotonic curve; waive minimum-bin precondition and behavior gate; absolute targets only; same ordering/collision rules; unattainable absolute target unavailable.',
            'M2a_gate_only': 'Additional explicit isolation control: waive minimum-bin precondition and behavior gate on same bins; retain default relative fallback, ordering and collision rules.',
            'M3_short_scale': 'Short scenarios only: min_valid_bins=3 or 4, fixed by prespecified structural support; all other default settings unchanged.',
        },
        'strong_signal': 'Exact existing aligned_sigmoid action curve and beta-mixture score generator; no outcome simulated.',
        'flat_null': 'Exact existing flat_behavior_null: p=0.18; same beta-mixture scores.',
        'weak_signal': 'p(s)=0.36+0.0008*s on [0,100]; true full-support span=0.08; same beta-mixture scores.',
        'sparse_tail': '0.99*Uniform(0,80)+0.01*Uniform(80,100); p(s)=0.04+0.88*expit((s-70)/8); top 20% score range has population mass 1%.',
        'low_ceiling': 'Exact existing low_ceiling p(s)=0.03+0.25*expit((s-50)/9); same beta-mixture scores.',
        'short_3': {'values': [0, 1, 2], 'mass': [0.70, 0.25, 0.05], 'action_probability': [0.10, 0.55, 0.90]},
        'short_4': {'values': [0, 1, 2, 3], 'mass': [0.40, 0.30, 0.20, 0.10], 'action_probability': [0.10, 0.35, 0.65, 0.90]},
        'truth': 'Known population P(A|S), with population-marginal action rate for Low; continuous crossing or first native value at target. Constant curve has no identifiable behavioral reference. Absolute and relative truth computed separately, over full prespecified score support. Error uses the output target family. Relative output when 0.80 is unattainable is legitimate, never itself a false output.',
        'output': 'Candidate availability and independent retention reported separately. Shared-threshold suppression is not semantic abstention. Over-abstention uses existence of default semantic truth; absolute-only over-abstention also reported for M2 to distinguish absence of fallback from gate effects.',
        'error': 'Absolute score-unit error conditional on output with an existing same-family truth; additionally error versus default population reference and sample-score-conditional Low truth. Population rather than fitted-support endpoints govern relative truth.',
        'workers': 4,
        'parameter_adjustments': [],
    },
    'clinical': {
        'split': 'GroupShuffleSplit(train_size=0.70, random_state=2026), original 425011-row universe before complete-case filtering',
        'action': 'Missing-aware OR(lactate,icu_fluid,vasopressor,steroid), legacy_v7_primary_eligible=1',
        'logistic': 'Unpenalized binomial GLM A~S fitted once on all learning score/action complete encounters; intercept included',
        'isotonic': 'Saved original curve read unchanged; raw-score linear interpolation and endpoint clipping',
        'metrics': 'Brier on raw predicted probabilities; log loss and descriptive calibration diagnostics clipped at 1e-6, matching eTable6C',
        'bootstrap': {'requested': 200, 'seed': 2026101103, 'unit': 'patient cluster', 'sampling': 'default_rng.multinomial(G, equal patient probabilities), sorted eligible-patient order; all eligible encounters per sampled patient; fixed both curves; no refit'},
        'paired_difference': 'isotonic Brier minus logistic Brier',
        'interval': 'linear percentiles 2.5 and 97.5; evaluation uncertainty conditional on fixed curves',
        'calibration': 'Joint intercept/slope diagnostic LogisticRegression(C=1e6, lbfgs, tol=1e-10, max_iter=2000), matching original diagnostic; no recalibration',
        'reliability_bins': '10 fixed probability bins [0,.1),...,[.9,1]',
        'logistic_crossings': 'Diagnostic continuous crossing, first native supported value, and first saved supported bin; not a new operational reference selection',
    },
    'saved_only': {'analysis2': True, 'analysis4': True},
    'tolerance_audit': 'Historical source search and numerical rule replay on saved curve only; no change to default code or any old sensitivity row.',
    'policy': 'Synthetic evidence is not clinical evidence; no reliability guarantee or statistical calibration claim; no clinical superiority claim for curve comparison.',
}


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def clean(x):
    if isinstance(x, dict): return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return [clean(v) for v in x]
    if isinstance(x, np.generic): return clean(x.item())
    if isinstance(x, float) and not np.isfinite(x): return None
    if isinstance(x, Path): return str(x)
    return x


def js(path, x):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(clean(x), f, ensure_ascii=False, indent=2, allow_nan=False)


def csv(path, data):
    d = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
    with Path(path).open('x', encoding='utf-8', newline='') as f:
        d.to_csv(f, index=False, float_format='%.17g')
    return d


def log(event, **kw):
    print(json.dumps(clean({'utc': datetime.now(timezone.utc).isoformat(), 'event': event, **kw}), ensure_ascii=False), flush=True)


def old_dgp():
    """Read historical definitions without executing historical analysis/main."""
    tree = ast.parse(OLD_RUNNER.read_text(encoding='utf-8-sig'))
    constants, funcs = {}, []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ['SCENARIOS', 'SIMULATION_CONDITIONS']:
                    constants[target.id] = ast.literal_eval(node.value)
        if isinstance(node, ast.FunctionDef) and node.name in ['expit_stable', 'response_probability', 'draw_scores']:
            funcs.append(node)
    ns = {'np': np, **constants}
    exec(compile(ast.Module(body=funcs, type_ignores=[]), str(OLD_RUNNER), 'exec'), ns)
    assert len(funcs) == 3 and len(ns['SCENARIOS']) == 8
    return ns


_DGP = None


def dgp():
    global _DGP
    if _DGP is None: _DGP = old_dgp()
    return _DGP


def probability(scenario, scores):
    s = np.asarray(scores, dtype=float)
    if scenario == 'strong_signal': return dgp()['response_probability'](s, 'aligned_sigmoid')
    if scenario == 'flat_null': return dgp()['response_probability'](s, 'flat_behavior_null')
    if scenario == 'weak_signal': return .36 + .0008*s
    if scenario == 'sparse_tail': return .04 + .88*expit((s-70)/8)
    if scenario == 'low_ceiling': return dgp()['response_probability'](s, 'low_ceiling')
    p = CONFIG['simulation'][scenario]
    return np.asarray(p['action_probability'])[s.astype(int)]


@lru_cache(maxsize=None)
def population_truth(scenario):
    short = scenario.startswith('short_')
    grid = np.array(CONFIG['simulation'][scenario]['values'], float) if short else np.array([0., 100.])
    p = probability(scenario, grid)
    if short:
        marginal = float(p @ np.array(CONFIG['simulation'][scenario]['mass']))
    elif scenario == 'sparse_tail':
        marginal = .99*quad(lambda s: float(probability(scenario, s)), 0, 80, epsabs=1e-12)[0]/80
        marginal += .01*quad(lambda s: float(probability(scenario, s)), 80, 100, epsabs=1e-12)[0]/20
    else:
        marginal = quad(lambda u: float(probability(scenario, 100*u))*(.9*beta.pdf(u, 2.2, 3.5)+.1*beta.pdf(u, 4, 2.2)), 0, 1, epsabs=1e-12)[0]
    pmin, pmax = float(p[0]), float(p[-1])
    flat = np.isclose(pmin, pmax, rtol=0, atol=1e-12)

    def crossing(target):
        if flat or target < pmin-1e-12 or target > pmax+1e-12: return np.nan
        if short:
            hit = np.flatnonzero(p >= target-1e-12)
            return float(grid[hit[0]]) if len(hit) else np.nan
        if abs(target-pmin) <= 1e-12: return 0.
        if abs(target-pmax) <= 1e-12: return 100.
        return float(brentq(lambda s: float(probability(scenario, s))-target, 0, 100, xtol=1e-11))

    result = {}
    for level, absolute, fraction in [('Low', marginal, None), ('Mid', .5, .5), ('High', .8, .8)]:
        absolute_t = crossing(absolute)
        relative_p = pmin + fraction*(pmax-pmin) if fraction is not None else np.nan
        relative_t = crossing(relative_p) if fraction is not None else np.nan
        family = 'A' if np.isfinite(absolute_t) else 'B' if np.isfinite(relative_t) else 'E'
        result[level] = {'absolute_target': absolute, 'absolute_threshold': absolute_t,
                         'relative_target': relative_p, 'relative_threshold': relative_t,
                         'default_threshold': absolute_t if family == 'A' else relative_t,
                         'default_family': family, 'default_exists': family != 'E',
                         'absolute_exists': np.isfinite(absolute_t), 'flat': flat,
                         'population_action_rate': marginal, 'p_min': pmin, 'p_max': pmax}
    # Independent truth follows the unchanged priority Mid, Low, High.
    used = []
    for level in ['Mid', 'Low', 'High']:
        t = result[level]['default_threshold']
        independent = bool(np.isfinite(t) and not any(np.isclose(t, old) for old in used))
        result[level]['default_independent'] = independent
        if independent: used.append(t)
    return result, crossing


def absolute_only_anchors(curve, scores, prevalence):
    """Named M2 selector, intentionally without relative fallback, same ordering."""
    observed = np.sort(np.unique(scores))
    rows = []
    for level, target in [('Low', prevalence), ('Mid', .5), ('High', .8)]:
        hit = curve[curve.isotonic_rate.ge(target-1e-12)]
        attainable = curve.isotonic_rate.min()-1e-12 <= target <= curve.isotonic_rate.max()+1e-12
        raw = float(hit.iloc[0].score) if len(hit) and attainable else np.nan
        candidates = observed[observed >= raw-1e-12] if np.isfinite(raw) else []
        t = float(candidates[0]) if len(candidates) else np.nan
        rows.append({'level': level, 'selected_threshold': t, 'provenance_tier': 'A' if np.isfinite(t) else 'E',
                     'operational_representative': False, 'target_probability': target,
                     'reason': 'absolute first crossing' if np.isfinite(t) else 'absolute target unattainable; no relative fallback'})
    values = {r['level']: r['selected_threshold'] for r in rows}
    for level in ['Mid', 'High']:
        prior = values['Low'] if level == 'Mid' else values['Mid'] if np.isfinite(values['Mid']) else values['Low']
        if np.isfinite(values[level]) and np.isfinite(prior) and values[level] < prior-1e-12:
            row = next(r for r in rows if r['level'] == level)
            row.update(selected_threshold=np.nan, provenance_tier='E', reason='semantic ordering inversion')
    used = []
    for level in ['Mid', 'Low', 'High']:
        row = next(r for r in rows if r['level'] == level)
        t = row['selected_threshold']
        if np.isfinite(t) and not any(np.isclose(t, old) for old in used):
            row['operational_representative'] = True
            used.append(t)
    return pd.DataFrame(rows)


def simulate_one(task):
    scenario, n, replicate = task
    rng = np.random.default_rng(np.random.SeedSequence([CONFIG['simulation']['seed'], SCENARIOS.index(scenario), n, replicate]))
    if scenario.startswith('short_'):
        c = CONFIG['simulation'][scenario]
        score = rng.choice(c['values'], size=n, p=c['mass']).astype(float)
    elif scenario == 'sparse_tail':
        tail = rng.random(n) < .01
        score = np.where(tail, rng.uniform(80, 100, n), rng.uniform(0, 80, n))
    else:
        score = dgp()['draw_scores'](rng, n)
    pp = probability(scenario, score)
    a = rng.binomial(1, pp)
    frame = pd.DataFrame({'score': score, 'action': a})
    draw_hash = hashlib.sha256(score.tobytes()+a.tobytes()).hexdigest()
    common_binning = choose_bin_width(score, DEFAULT)
    # This named bypass removes only the precondition for constructing the common
    # curve; bin selection still uses DEFAULT and min_bin_n remains 40.
    use, curve, _ = build_response_curve(frame, 'score', 'action', common_binning['bin_width'], replace(DEFAULT, min_valid_bins=2))
    gate = None
    outputs, reason = {}, ''
    try:
        original = fit_behavior_thresholds(frame, 'score', 'action', DEFAULT)
        assert np.array_equal(original.response_curve.score, curve.score)
        assert np.allclose(original.response_curve.isotonic_rate, curve.isotonic_rate, rtol=0, atol=0)
        outputs['M1_default'] = original.anchors
        gate = original.evidence_gate
    except InsufficientBinsError as e:
        reason = str(e)
        outputs['M1_default'] = pd.DataFrame([{'level': l, 'selected_threshold': np.nan, 'provenance_tier': 'E', 'operational_representative': False, 'reason': reason} for l in LEVELS])
    forced = {'passed': True, 'reason': 'explicit gate-only ablation'}
    outputs['M2a_gate_only'] = derive_semantic_anchors(curve, score, float(a.mean()), pd.DataFrame(), common_binning['bin_width'], forced, DEFAULT)
    outputs['M2_no_gate_no_relative'] = absolute_only_anchors(curve, score, float(a.mean()))
    if scenario.startswith('short_'):
        c = replace(DEFAULT, min_valid_bins=len(CONFIG['simulation'][scenario]['values']))
        special = fit_behavior_thresholds(frame, 'score', 'action', c)
        assert np.array_equal(special.response_curve.score, curve.score)
        outputs['M3_short_scale'] = special.anchors
    truth, cross = population_truth(scenario)
    sample_low = cross(float(pp.mean()))
    out = []
    for method, anchors in outputs.items():
        for row in anchors.to_dict('records'):
            level, t, fam = row['level'], float(row['selected_threshold']), row['provenance_tier']
            q = truth[level]
            available = bool(np.isfinite(t))
            same_truth = q['absolute_threshold'] if fam == 'A' else q['relative_threshold'] if fam == 'B' else np.nan
            false_output = available and not np.isfinite(same_truth)
            out.append({'scenario': scenario, 'n': n, 'replicate': replicate, 'method': method,
                        'level': level, 'paired_data_sha256': draw_hash, 'selected_threshold': t,
                        'family': fam, 'output': available, 'independent_retained': bool(row['operational_representative']),
                        'population_default_exists': q['default_exists'], 'population_absolute_exists': q['absolute_exists'],
                        'population_default_family': q['default_family'], 'population_default_threshold': q['default_threshold'],
                        'matched_family_truth': same_truth, 'false_output': false_output,
                        'absolute_false_output': available and fam == 'A' and not q['absolute_exists'],
                        'over_abstention': q['default_exists'] and not available,
                        'absolute_over_abstention': q['absolute_exists'] and not available,
                        'relative_used': available and fam == 'B',
                        'family_mismatch': available and fam != q['default_family'],
                        'absolute_error': abs(t-same_truth) if available and np.isfinite(same_truth) else np.nan,
                        'error_vs_default_truth': abs(t-q['default_threshold']) if available and q['default_exists'] else np.nan,
                        'sample_conditional_low_error': abs(t-sample_low) if level == 'Low' and available and np.isfinite(sample_low) else np.nan,
                        'bin_width': common_binning['bin_width'], 'valid_bins': len(curve),
                        'M1_gate_passed': bool(gate['passed']) if gate else False,
                        'M1_gate_reason': gate['reason'] if gate else reason,
                        'M1_dynamic_range': gate['isotonic_dynamic_range'] if gate else np.nan,
                        'M1_logistic_BIC_improvement': gate['logistic_bic_improvement'] if gate else np.nan,
                        'sample_tail_fraction': float((score >= 80).mean()) if scenario == 'sparse_tail' else np.nan,
                        'reason': row.get('reason', '')})
    return out


def quantile_triplet(values):
    a = np.asarray(values, float)
    a = a[np.isfinite(a)]
    return (float(np.median(a)), float(np.quantile(a, .025)), float(np.quantile(a, .975))) if len(a) else (np.nan, np.nan, np.nan)


def analysis1(bundle):
    truth_rows, curve_rows = [], []
    for s in SCENARIOS:
        truth, _ = population_truth(s)
        for level, q in truth.items(): truth_rows.append({'scenario': s, 'level': level, **q})
        grid = np.array(CONFIG['simulation'][s]['values'], float) if s.startswith('short_') else np.linspace(0, 100, 1001)
        for x, p in zip(grid, probability(s, grid)):
            curve_rows.append({'scenario': s, 'score': x, 'true_action_probability': p})
    csv(bundle/'tables/analysis1_true_references.csv', truth_rows)
    csv(bundle/'tables/analysis1_true_curves.csv', curve_rows)
    tasks = [(s, n, b) for s in SCENARIOS for n in [6000, 2000] for b in range(200)]
    results = []
    log('analysis1_started', datasets=len(tasks), paired_methods=True)
    with ProcessPoolExecutor(max_workers=4) as pool:
        pending = {pool.submit(simulate_one, t): t for t in tasks}
        for i, future in enumerate(as_completed(pending), 1):
            results.extend(future.result())
            if i % 100 == 0: log('analysis1_progress', completed_datasets=i, requested=len(tasks))
    d = pd.DataFrame(results).sort_values(['scenario', 'n', 'replicate', 'method', 'level'])
    assert d.groupby(['scenario', 'n', 'replicate']).paired_data_sha256.nunique().eq(1).all()
    rows = []
    for key, g in d.groupby(['scenario', 'n', 'method', 'level'], sort=False):
        med, lo, hi = quantile_triplet(g.absolute_error)
        row = dict(zip(['scenario', 'n', 'method', 'level'], key))
        row.update(requested_replicates=200, completed_replicates=g.replicate.nunique(),
                   output_N=int(g.output.sum()), output_rate=float(g.output.mean()),
                   independent_retained_N=int(g.independent_retained.sum()), independent_retention_rate=float(g.independent_retained.mean()),
                   false_output_N=int(g.false_output.sum()), false_output_rate=float(g.false_output.mean()),
                   false_output_given_output=float(g.false_output.sum()/g.output.sum()) if g.output.sum() else np.nan,
                   absolute_false_output_N=int(g.absolute_false_output.sum()),
                   population_default_exists=bool(g.population_default_exists.iloc[0]),
                   population_absolute_exists=bool(g.population_absolute_exists.iloc[0]),
                   over_abstention_N=int(g.over_abstention.sum()),
                   over_abstention_rate=float(g.over_abstention.mean()) if g.population_default_exists.iloc[0] else np.nan,
                   absolute_over_abstention_rate=float(g.absolute_over_abstention.mean()) if g.population_absolute_exists.iloc[0] else np.nan,
                   relative_use_N=int(g.relative_used.sum()), relative_use_rate=float(g.relative_used.mean()),
                   family_mismatch_rate=float(g.family_mismatch.mean()),
                   error_evaluable_output_N=int(g.absolute_error.notna().sum()),
                   error_median=med, error_p025=lo, error_p975=hi,
                   error_vs_default_median=quantile_triplet(g.error_vs_default_truth)[0],
                   default_gate_pass_rate=float(g.M1_gate_passed.mean()))
        assert row['completed_replicates'] == 200
        rows.append(row)
    csv(bundle/'tables/analysis1_summary.csv', rows)
    csv(bundle/'replicates/analysis1_replicates.csv', d)
    log('analysis1_complete', datasets=len(tasks), method_level_rows=len(d), summary_rows=len(rows))


def analysis2(bundle):
    historical = dgp()
    old_manifest = json.loads((OLD_SIM/'manifest.json').read_text(encoding='utf-8'))
    registration = next(x for x in old_manifest['source_registry'] if x['path'].endswith('run_final_simulation_validation.py'))
    assert sha(OLD_RUNNER) == registration['sha256'], 'Historical generator has changed'
    mechanism = []
    for s, c in historical['SCENARIOS'].items():
        form = {'sigmoid': 'floor+(ceiling-floor)*expit((S-center)/scale)', 'piecewise': 'linear interpolation of stated knots/values', 'flat': 'constant action probability'}[c['response_kind']]
        mechanism.append({'scenario': s, 'function': form, 'parameters': json.dumps(c, sort_keys=True),
                          'score_generator': '.90*100*Beta(2.2,3.5)+.10*100*Beta(4,2.2) mixture (not weighted sum)',
                          'conditions': json.dumps(historical['SIMULATION_CONDITIONS'], sort_keys=True),
                          'label_noise_function': 'q+(1-2q)*p', 'generator_sha256': sha(OLD_RUNNER)})
    csv(bundle/'tables/analysis2_generation_mechanisms.csv', mechanism)
    truth = pd.read_csv(OLD_SIM/'tables/oracle_truth.csv')
    csv(bundle/'tables/analysis2_existing_true_references.csv', truth)
    d = pd.read_csv(OLD_SIM/'tables/threshold_replicates.csv')
    rows = []
    for key, g in d.groupby(['scenario', 'condition', 'method', 'level'], sort=False):
        med, lo, hi = quantile_triplet(g.absolute_error)
        n = g.replicate.nunique()
        assert n == 25
        rows.append({**dict(zip(['scenario', 'condition', 'method', 'level'], key)),
                     'requested_replicates': 25, 'completed_replicates': n,
                     'output_N': int(g.estimated_available.sum()), 'output_rate': float(g.estimated_available.mean()),
                     'abstention_rate': float((~g.estimated_available).mean()),
                     'false_output_rate': float((g.estimated_available & ~g.true_available).mean()),
                     'over_abstention_rate': float((~g.estimated_available & g.true_available).mean()) if g.true_available.any() else np.nan,
                     'error_output_N': int(g.absolute_error.notna().sum()),
                     'error_median': med, 'error_p025': lo, 'error_p975': hi,
                     'truth_min': float(g.true_threshold.min()) if g.true_threshold.notna().any() else np.nan,
                     'truth_max': float(g.true_threshold.max()) if g.true_threshold.notna().any() else np.nan,
                     'source': 'existing threshold_replicates.csv; no rerun'})
    csv(bundle/'tables/analysis2_existing_summary.csv', rows)
    # Saved oracle uses a 200000-score Monte Carlo population, 0.05 grid, and
    # native operationalization. Export it as saved, without replacing it.
    js(bundle/'analysis2_status.json', {
        'status': 'complete_from_saved_outputs', 'new_simulation_replicates': 0,
        'all_eight_scenarios': True, 'scenario_condition_combinations': 32,
        'saved_replicates_per_scenario_condition': 25, 'methods': d.method.unique().tolist(),
        'missing_requested_quantities': [],
        'truth_convention': 'Saved oracle_n=200000, oracle grid linspace(0,100,2001), population sample expected action rate, first crossing mapped to a sampled native score. Tied-score/noise conditions have their own saved oracle truth.',
        'structural_truth_discrepancy': 'two_changepoints generator knots are 30 and 50, while legacy CP truth records 30 and 55; preserved unchanged. This analysis concerns semantic references, not a new claim of CP recovery.',
        'same_family_error_not_recoverable_from_saved_threshold_replicates': 'Candidate family per replicate was not in this file; existing saved errors are versus the saved default oracle reference. No new same-family relabeling is imposed.',
    })
    log('analysis2_complete', old_replicates=800, summary_rows=len(rows))


def analysis3(bundle):
    cols = ['subject_id', 'score_ESRP_new', 'legacy_v7_primary_eligible', 'lactate_flag', 'icu_fluid_flag', 'vasopressor_flag', 'steroid_flag']
    f = pd.read_csv(DATA, usecols=cols, low_memory=False)
    assert len(f) == 425011 and f.subject_id.notna().all()
    mat = f[cols[3:]].apply(pd.to_numeric, errors='coerce')
    assert mat.stack().isin([0, 1]).all()
    f['action'] = np.nan
    f.loc[mat.eq(1).any(axis=1), 'action'] = 1.
    f.loc[mat.eq(0).all(axis=1), 'action'] = 0.
    f.loc[~pd.to_numeric(f.legacy_v7_primary_eligible, errors='coerce').eq(1), 'action'] = np.nan
    f['score'] = pd.to_numeric(f.score_ESRP_new, errors='coerce')
    train, test = next(GroupShuffleSplit(n_splits=1, train_size=.7, random_state=2026).split(f, groups=f.subject_id))
    assert (len(train), len(test)) == (297478, 127533)
    dev = f.iloc[train].dropna(subset=['score', 'action'])
    held = f.iloc[test].dropna(subset=['score', 'action'])
    assert len(dev) == 294713 and int(dev.action.sum()) == 96268
    assert len(held) == 126332 and held.subject_id.nunique() == 60903
    assert set(dev.subject_id).isdisjoint(set(held.subject_id))
    # Verify the saved curve's input counts; do not fit a new isotonic curve.
    old = pd.read_csv(CURVE)
    bins = np.floor((dev.score-dev.score.min())/3)*3+dev.score.min()
    ck = dev.assign(bin=bins).groupby('bin').action.agg(['mean', 'size'])
    ck = ck[ck['size'].ge(40)]
    assert np.array_equal(ck.index, old.score) and np.array_equal(ck['size'], old['count'])
    assert np.allclose(ck['mean'], old.observed_rate, rtol=0, atol=1e-12)
    # The new logistic fit uses exact grouped binomial sufficient statistics.
    grouped = dev.groupby('score').action.agg(['sum', 'size'])
    model = sm.GLM(grouped['sum']/grouped['size'], sm.add_constant(grouped.index.to_numpy(float)),
                   family=sm.families.Binomial(), freq_weights=grouped['size']).fit(tol=1e-9, maxiter=200)
    assert model.converged
    assert np.max(np.abs(model.model.score(model.params))) < 1e-6
    intercept, slope = map(float, model.params)
    s = held.score.to_numpy(float); y = held.action.to_numpy(float)
    pred = {'logistic': expit(intercept+slope*s), 'isotonic': np.interp(s, old.score, old.isotonic_rate)}
    points, reliability = [], []
    expected = json.loads((ACTION/'sepsis_action_points.json').read_text(encoding='utf-8'))[0]
    for name, p in pred.items():
        pc = np.clip(p, 1e-6, 1-1e-6)
        cl = np.log(pc/(1-pc))
        cal = LogisticRegression(C=1e6, solver='lbfgs', max_iter=2000, tol=1e-10).fit(cl[:, None], y.astype(int))
        assert cal.n_iter_[0] < 2000
        points.append({'curve': name, 'learning_N': len(dev), 'heldout_N': len(held), 'heldout_patients': held.subject_id.nunique(),
                       'Brier': float(np.mean((p-y)**2)), 'log_loss': float(np.mean(-(y*np.log(pc)+(1-y)*np.log(1-pc)))),
                       'calibration_intercept': float(cal.intercept_[0]), 'calibration_slope': float(cal.coef_[0, 0]),
                       'observed_action_rate': float(y.mean()), 'mean_predicted': float(p.mean())})
        assignment = np.minimum((p*10).astype(int), 9)
        for b in range(10):
            z = assignment == b
            reliability.append({'curve': name, 'bin': b, 'lower': b/10, 'upper': (b+1)/10,
                                'N': int(z.sum()), 'actions': int(y[z].sum()),
                                'observed': float(y[z].mean()) if z.any() else np.nan,
                                'predicted': float(p[z].mean()) if z.any() else np.nan})
    isotonic = next(x for x in points if x['curve'] == 'isotonic')
    differences = []
    for new_name, old_name, tolerance in [('Brier', 'action_Brier', 1e-12), ('log_loss', 'action_log_loss', 1e-12),
                                           ('calibration_intercept', 'calibration_intercept', 1e-6), ('calibration_slope', 'calibration_slope', 1e-6),
                                           ('mean_predicted', 'mean_predicted', 1e-12), ('observed_action_rate', 'action_rate', 1e-12)]:
        differences.append({'metric': new_name, 'existing_point': expected[old_name], 'current_point': isotonic[new_name],
                            'difference': isotonic[new_name]-expected[old_name], 'matching_tolerance': tolerance,
                            'within_tolerance': abs(isotonic[new_name]-expected[old_name]) <= tolerance})
    # All patients retained per cluster draw; both loss arrays use identical weights.
    _, g = np.unique(held.subject_id.to_numpy(), return_inverse=True)
    G = int(g.max()+1)
    cluster = np.column_stack([np.bincount(g), np.bincount(g, weights=(pred['logistic']-y)**2),
                               np.bincount(g, weights=(pred['isotonic']-y)**2)])
    rng = np.random.default_rng(CONFIG['clinical']['bootstrap']['seed'])
    draws = []
    for b in range(200):
        weights = rng.multinomial(G, np.full(G, 1/G))
        n, lo, iso = weights @ cluster
        draws.append({'replicate': b, 'N': int(n), 'logistic_Brier': lo/n, 'isotonic_Brier': iso/n,
                      'paired_difference_isotonic_minus_logistic': (iso-lo)/n})
    med, lower, upper = quantile_triplet([x['paired_difference_isotonic_minus_logistic'] for x in draws])
    pmap = {x['curve']: x for x in points}
    delta = pmap['isotonic']['Brier']-pmap['logistic']['Brier']
    csv(bundle/'tables/analysis3_curve_comparison.csv', points)
    csv(bundle/'tables/analysis3_reliability_bins.csv', reliability)
    csv(bundle/'tables/analysis3_existing_isotonic_reconciliation.csv', differences)
    csv(bundle/'tables/analysis3_paired_Brier_interval.csv', [{'orientation': 'isotonic_minus_logistic', 'point': delta, 'median': med, 'lower_025': lower, 'upper_975': upper, 'requested': 200, 'valid': 200, 'unit': 'patient_cluster'}])
    csv(bundle/'replicates/analysis3_paired_Brier.csv', draws)
    crossings = []
    natives = np.sort(dev.score.unique())
    for level, target, original in [('Low', float(dev.action.mean()), 27), ('Mid', .5, 36), ('High', .8, 51)]:
        continuous = (np.log(target/(1-target))-intercept)/slope
        eligible = natives[expit(intercept+slope*natives) >= target-1e-12]
        eligible_bins = old.score[expit(intercept+slope*old.score) >= target-1e-12]
        crossings.append({'level': level, 'target_probability': target, 'logistic_continuous_crossing': continuous,
                          'logistic_first_native_value': float(eligible[0]) if len(eligible) else np.nan,
                          'logistic_first_saved_supported_bin': float(eligible_bins.iloc[0]) if len(eligible_bins) else np.nan,
                          'existing_isotonic_reference': original, 'role': 'alternative-fit diagnostic; existing references unchanged'})
    csv(bundle/'tables/analysis3_logistic_crossings.csv', crossings)
    unique_grid = np.sort(np.unique(np.r_[natives, old.score]))
    csv(bundle/'tables/analysis3_probability_curves.csv', pd.DataFrame({'score': unique_grid, 'logistic_action_probability': expit(intercept+slope*unique_grid), 'saved_isotonic_action_probability': np.interp(unique_grid, old.score, old.isotonic_rate)}))
    js(bundle/'analysis3_status.json', {'status': 'complete', 'logistic_intercept': intercept, 'logistic_score_coefficient': slope,
                                      'GLM_solver': 'IRLS, maxiter=200, deviance convergence tolerance=1e-9',
                                      'GLM_converged': bool(model.converged), 'GLM_iterations': model.fit_history['iteration'],
                                      'GLM_max_absolute_score': float(np.max(np.abs(model.model.score(model.params)))),
                                      'isotonic_read_from_saved_curve_not_refitted': True, 'existing_results_unchanged': True,
                                      'isotonic_points_reproduce': all(x['within_tolerance'] for x in differences),
                                      'difference_logistic_minus_isotonic_rejected': 'Only stated orientation isotonic minus logistic is used.',
                                      'curve_comparison_is_predictive_diagnostic_not_clinical_superiority': True})
    log('analysis3_complete', points=points, paired_difference=delta, lower=lower, upper=upper, crossings=crossings)


def analysis4(bundle):
    objects = [
        ('REMS_High_MIMIC', COMPARATOR/'reference/MIMIC_learning_REMS/anchors.csv'),
        ('REMS_High_Stanford', COMPARATOR/'reference/Stanford_REMS/anchors.csv'),
        ('ESRP_1h_High_MIMIC', PRECISION/'reference/window_1h/replicate_anchors.csv'),
        ('qSOFA_3bin_High_MIMIC', QSOFA/'reference/MIMIC_learning_qSOFA/anchors.csv'),
        ('qSOFA_3bin_High_Stanford', QSOFA/'reference/Stanford_qSOFA/anchors.csv'),
    ]
    rows, audit = [], []
    for name, path in objects:
        d = pd.read_csv(path)
        g = d[d.level.eq('High')]
        assert g.replicate.nunique() == 500 and len(g) == 500
        # Anchor family survives ordering abstention; provenance E means final
        # unavailability, not that no absolute/relative target was attempted.
        for label in ['absolute', 'relative', 'no_target']:
            mask = g.anchor_family.eq(label) if label != 'no_target' else ~g.anchor_family.isin(['absolute', 'relative'])
            part = g[mask]
            v = part.selected_threshold
            med, lower, upper = quantile_triplet(v)
            independent = part[part.operational_representative.eq(True)]
            imed, ilo, ihi = quantile_triplet(independent.selected_threshold)
            rows.append({'object': name, 'target_family': label, 'requested': 500, 'family_occurrence_N': len(part),
                         'family_occurrence_fraction': len(part)/500, 'available_selected_N': int(v.notna().sum()),
                         'threshold_median': med, 'threshold_p025': lower, 'threshold_p975': upper,
                         'independent_retained_N': len(independent), 'independent_retained_fraction_all_requests': len(independent)/500,
                         'independent_threshold_median': imed, 'independent_threshold_p025': ilo, 'independent_threshold_p975': ihi,
                         'shared_threshold_N': int((part.selected_threshold.notna() & ~part.operational_representative.eq(True)).sum()),
                         'unavailable_after_target_N': int(part.selected_threshold.isna().sum()),
                         'final_provenance_A_N': int(part.provenance_tier.eq('A').sum()),
                         'final_provenance_B_N': int(part.provenance_tier.eq('B').sum()),
                         'final_provenance_E_N': int(part.provenance_tier.eq('E').sum())})
        audit.append({'object': name, 'requested': 500, 'rows': len(g), 'total_family_count': sum(int(g.provenance_tier.eq(k).sum()) for k in ['A', 'B', 'E']), 'source_sha256': sha(path), 'new_resamples': 0})
    csv(bundle/'tables/analysis4_separated_provenance_summary.csv', rows)
    csv(bundle/'tables/analysis4_request_audit.csv', audit)
    log('analysis4_complete', objects=5, new_resamples=0, rows=rows)


def analysis5(bundle):
    manifest = json.loads((OLD_V8/'manifest.json').read_text(encoding='utf-8'))
    record = next(x for x in manifest['source_registry'] if x['source'] == 'V8 notebook')
    source = Path(record['path'])
    historic = pd.read_csv(OLD_V8/'tables/semantic_gate_one_factor_sensitivity.csv')
    curve = pd.read_csv(CURVE)
    marginal = 96268/294713
    rows = []
    for tolerance in [.005, .010]:
        group = historic[(historic.variant_family == 'attainability_tolerance') & np.isclose(pd.to_numeric(historic.variant_value, errors='coerce'), tolerance)]
        assert len(group) == 3
        for level, target in [('Low', marginal), ('Mid', .5), ('High', .8)]:
            saved = float(group.loc[group.level.eq(level), 'threshold'].iloc[0])
            range_only_eligible = curve[curve.isotonic_rate.ge(target-1e-12)]
            hit_eligible = curve[curve.isotonic_rate.ge(target-tolerance)]
            original = float(range_only_eligible.iloc[0].score)
            replay = float(hit_eligible.iloc[0].score)
            rows.append({'tolerance': tolerance, 'level': level, 'saved_threshold': saved,
                         'range_only_tolerance_replay': original,
                         'bin_target_tolerance_replay': replay,
                         'bin_target_replay_matches_saved': np.isclose(saved, replay),
                         'range_only_replay_matches_saved': np.isclose(saved, original),
                         'target_probability': target,
                         'fitted_rate_at_replayed_bin': float(hit_eligible.iloc[0].isotonic_rate),
                         'source_script_available': source.exists(),
                         'source_script_hash_recorded': record['fingerprint'],
                         'source_script_hash_verified_currently': sha(source) if source.exists() else '',
                         'historical_table_sha256': sha(OLD_V8/'tables/semantic_gate_one_factor_sensitivity.csv'),
                         'current_default_module2_sha256': sha(PACKAGE/'src/universal_cutoff/module2.py'),
                         'current_default_epsilon': 1e-12,
                         'status': 'numerical bin-crossing rule reproducible; original source unavailable' if not source.exists() else 'source requires code inspection'})
    csv(bundle/'tables/analysis5_tolerance_rule_replay.csv', rows)
    js(bundle/'analysis5_status.json', {
        'status': 'partially_resolved_original_generator_unavailable',
        'historical_generator_registry': record,
        'historical_generator_exists_now': source.exists(),
        'historical_config': manifest['configuration'],
        'source_search_scope': 'Project notebooks/scripts and attainability_tolerance search in package source and workspace scripts, excluding dependencies/build',
        'numerical_replay_all_six_thresholds_match_bin_target_tolerance': all(x['bin_target_replay_matches_saved'] for x in rows),
        'range_only_rule_cannot_explain_Low24_at_010': True,
        'inference': 'Low24 at .010 is consistent with allowing a bin rate within tolerance below the target, rather than merely expanding the fitted probability range. Missing historical source prevents certifying the complete original implementation.',
        'missing': ['Original V8 generation notebook/script and exact executed source/config beyond manifest flags; original full implementation cannot be replayed'],
        'default_algorithm_changed': False, 'old_rows_modified_or_deleted': False,
    })
    log('analysis5_complete', status='partial_provenance_gap', numeric_replay_matches=True, Low_010=24)


def protected_files():
    paths = {MASTER, DATA, OLD_RUNNER, CURVE, SUPPLEMENT}
    paths.update((PACKAGE/'src').rglob('*.py'))
    paths.update((PACKAGE/'configs').rglob('*.*'))
    for folder in [OLD_SIM, OLD_V8, ACTION, PRECISION, COMPARATOR, QSOFA]:
        paths.update(p for p in folder.rglob('*') if p.is_file())
    paths.update(p for p in (ROOT/'v7_outputs').glob('*') if p.is_file())
    paths.update(p for p in ROOT.glob('*.ipynb'))
    for p in (ROOT/'paper/paper——V5/V7').glob('*.docx'): paths.add(p)
    return sorted(paths, key=str)


def prepare():
    config_bytes = json.dumps(CONFIG, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    config_sha = hashlib.sha256(config_bytes).hexdigest()
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    bundle = ROOT/'v8_support_gate_addendum_outputs'/f'run_{stamp}_{config_sha[:12]}'
    bundle.mkdir(parents=True, exist_ok=False)
    for sub in ['tables', 'replicates', 'controlled']: (bundle/sub).mkdir()
    js(bundle/'config.json', CONFIG)
    shutil.copyfile(Path(__file__), bundle/'runner.py')
    before = [{'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in protected_files()]
    js(bundle/'controlled/protected_sources_before.json', before)
    js(bundle/'controlled/source_registry.json', {'source_data': str(DATA), 'source_data_sha256': sha(DATA),
                                              'original_simulation': str(OLD_SIM), 'saved_action_curve': str(CURVE),
                                              'master_before_sha256': sha(MASTER)})
    js(bundle/'runtime.json', {'python': sys.version, 'executable': sys.executable,
                              'packages': {name: importlib.metadata.version(name) for name in ['numpy', 'pandas', 'scipy', 'scikit-learn', 'statsmodels']},
                              'config_sha256': config_sha, 'runner_sha256': sha(bundle/'runner.py')})
    log('prepared', bundle=str(bundle), config_sha256=config_sha, protected_files=len(before))
    return bundle


def finalize(bundle):
    before = json.loads((bundle/'controlled/protected_sources_before.json').read_text(encoding='utf-8'))
    after = []
    for r in before:
        current = sha(r['path'])
        after.append({**r, 'after_sha256': current, 'unchanged': current == r['sha256']})
    js(bundle/'controlled/protected_sources_before_after.json', after)
    assert all(r['unchanged'] for r in after), 'Protected source changed; investigate without replacing outputs'
    # Public tables/replicates may have synthetic run indexes but no clinical IDs.
    for directory in ['tables', 'replicates']:
        for path in (bundle/directory).glob('*.csv'):
            text = path.read_text(encoding='utf-8')
            assert not any(re.search(r'(?i)\b[a-z]:[\\/]+', cell) for row in __import__('csv').reader(text.splitlines()) for cell in row)
            headers = pd.read_csv(path, nrows=0).columns
            assert not any(k in headers for k in ['subject_id', 'stay_id', 'hadm_id', 'patient_id'])
    runtime = json.loads((bundle/'runtime.json').read_text(encoding='utf-8'))
    recovery_path = bundle/'controlled/execution_recovery.json'
    recovery = json.loads(recovery_path.read_text(encoding='utf-8')) if recovery_path.exists() else None
    registry = [{'relative_path': p.relative_to(bundle).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)}
                for p in sorted(bundle.rglob('*')) if p.is_file() and p.name != 'manifest.json']
    js(bundle/'manifest.json', {'status': 'complete_with_analysis5_provenance_gap', 'completed_utc': datetime.now(timezone.utc).isoformat(),
                              'analyses_complete': [1, 2, 3, 4], 'analysis5': 'numeric rule replay complete; original generator missing',
                              'config_sha256': runtime['config_sha256'], 'runner_sha256': sha(bundle/'runner.py'),
                              'initial_executed_runner_sha256': runtime['runner_sha256'],
                              'execution_recovery': recovery,
                              'protected_files_unchanged': len(after), 'all_protected_files_unchanged': True,
                              'clinical_individual_data_exported': False, 'simulation_datasets': 2800,
                              'simulation_replicates_each_cell': 200, 'paired_patient_bootstrap': 200,
                              'new_reference_bootstrap': 0, 'files': registry})
    log('complete', bundle=str(bundle), manifest_sha256=sha(bundle/'manifest.json'), files=len(registry))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--bundle', type=Path)
    parser.add_argument('--analysis', type=int, choices=[1, 2, 3, 4, 5])
    parser.add_argument('--finalize-only', action='store_true')
    args = parser.parse_args()
    bundle = args.bundle or prepare()
    if args.prepare_only: return
    if args.finalize_only: finalize(bundle); return
    if args.analysis:
        globals()[f'analysis{args.analysis}'](bundle)
        return
    for i in [2, 4, 5, 3, 1]: globals()[f'analysis{i}'](bundle)
    finalize(bundle)


if __name__ == '__main__':
    main()
