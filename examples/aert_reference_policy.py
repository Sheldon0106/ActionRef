"""Short-discrete AERT research policy used in Supplement eMethods 2.

This is an application-specific extension, separate from the core default policy.
Inputs are score-level counts; no clinical records or identifiers are required.
It retains the original support, evidence, ordering and terminal-tail rules.
"""
from __future__ import annotations

from functools import lru_cache
import json
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
from scipy.stats import hypergeom
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

from universal_cutoff import Module2Config, fit_behavior_thresholds
from universal_cutoff.module2 import derive_semantic_anchors

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs/aert.json").read_text(encoding="utf-8"))["reference_policy"]
DEFAULT = Module2Config()
SHORT_COMPARATOR = Module2Config(min_valid_bins=4)
V1 = "short_semantic_guarded_v1"
V2 = "short_semantic_tail_guarded_v2"

def reversal_check(counts, responses):
    keep = counts > 0
    n, k = counts[keep], responses[keep]
    left, right = np.triu_indices(len(n), k=1)
    if not len(left):
        return dict(min_pair_p=1., bonferroni_p=1., pairs=0, shape_veto=False)
    # Table [[k_i, n_i-k_i], [k_j, n_j-k_j]], alternative OR>1.
    p = hypergeom.sf(k[left]-1, n[left]+n[right], k[left]+k[right], n[left])
    assert np.isfinite(p).all() and np.all((p >= 0) & (p <= 1))
    minimum = float(p.min())
    adjusted = min(1., minimum * len(left))
    return dict(min_pair_p=minimum, bonferroni_p=adjusted, pairs=len(left),
                shape_veto=bool(adjusted < CONFIG['directional_pairwise_fisher_alpha_bonferroni']))

def aggregated_fit(counts, responses):
    counts = np.asarray(counts, dtype=int)
    responses = np.asarray(responses, dtype=int)
    assert np.all(counts >= 0) and np.all((responses >= 0) & (responses <= counts))
    scores = np.arange(len(counts), dtype=float)
    supported = counts >= DEFAULT.min_bin_n
    n, positive = int(counts.sum()), int(responses.sum())
    both_classes = 0 < positive < n
    valid_n = int(supported.sum())
    curve = pd.DataFrame({'score': scores[supported], 'count': counts[supported],
                          'observed_rate': responses[supported] / counts[supported]})
    if valid_n:
        iso = IsotonicRegression(y_min=0, y_max=1, increasing=True, out_of_bounds='clip')
        curve['isotonic_rate'] = iso.fit_transform(curve.score, curve.observed_rate, sample_weight=curve['count'])
        dynamic = float(curve.isotonic_rate.max() - curve.isotonic_rate.min())
    else:
        curve['isotonic_rate'] = pd.Series(dtype=float)
        dynamic = 0.
    slope, improvement = np.nan, np.nan
    if both_classes:
        x_pair = np.repeat(scores, 2).reshape(-1, 1)
        y_pair = np.tile([0, 1], len(scores))
        weights = np.column_stack([counts-responses, responses]).ravel()
        model = LogisticRegression(C=1e6, solver='lbfgs', max_iter=1000).fit(x_pair, y_pair, sample_weight=weights)
        p1 = np.clip(model.predict_proba(scores.reshape(-1, 1))[:, 1], 1e-9, 1-1e-9)
        p0 = float(np.clip(positive/n, 1e-9, 1-1e-9))
        ll0 = positive * np.log(p0) + (n-positive) * np.log1p(-p0)
        ll1 = np.sum(responses * np.log(p1) + (counts-responses) * np.log1p(-p1))
        improvement = float((-2*ll0 + math.log(n)) - (-2*ll1 + 2*math.log(n)))
        slope = float(model.coef_[0, 0])
    gate_pass = bool(valid_n >= 4 and both_classes and dynamic >= DEFAULT.min_isotonic_dynamic_range and
                     slope > 0 and improvement >= DEFAULT.min_logistic_bic_improvement)
    gate = dict(passed=gate_pass, status='supported' if gate_pass else 'unsupported_abstention',
                reason='aggregate implementation of unchanged dynamic/slope/BIC evidence rule',
                n_valid_bins=valid_n, isotonic_dynamic_range=dynamic,
                logistic_slope=slope, logistic_bic_improvement=improvement)
    anchors = derive_semantic_anchors(curve, scores[counts > 0], positive/n, pd.DataFrame(), 1., gate, SHORT_COMPARATOR)
    finite = anchors.selected_threshold.dropna().to_numpy(float)
    assert len(finite) < 2 or np.all(np.diff(finite) >= 0)
    assert not anchors.cp_corroborated.any()
    prerequisites = n >= CONFIG['min_N'] and min(positive, n-positive) >= CONFIG['min_each_response']
    mass = float(counts[supported].sum()/n)
    shape = reversal_check(counts, responses)
    short_support = (valid_n >= CONFIG['guarded_min_valid_bins'] and mass >= CONFIG['guarded_min_supported_mass'] and
                     np.count_nonzero(counts) <= CONFIG['maximum_short_score_levels'])
    policies = {}
    emitted = int(anchors.operational_representative.sum())
    for policy, support in [('package_default_8', valid_n >= DEFAULT.min_valid_bins),
                            ('support_only_4', valid_n >= 4), ('short_semantic_guarded_v1', short_support)]:
        eligible = bool(prerequisites and support)
        passed = bool(eligible and gate_pass and (policy != 'short_semantic_guarded_v1' or not shape['shape_veto']))
        policies[policy] = dict(eligible=eligible, gate_passed=passed, any_anchor=bool(passed and emitted),
                               unique_anchors=emitted if passed else 0)
    diagnostic = dict(N=n, response_positive=positive, valid_bins=valid_n, supported_mass=mass,
                      dynamic_range=dynamic, logistic_slope=slope, logistic_BIC_improvement=improvement,
                      common_evidence_gate_pass=gate_pass, **shape)
    return policies, diagnostic, anchors, curve, gate

@lru_cache(maxsize=16)
def contrast_indices(levels):
    left, right = np.triu_indices(levels, k=1)
    starts, boundaries = [], []
    for boundary in range(1, levels):
        for start in range(boundary):
            starts.append(start)
            boundaries.append(boundary)
    return left, right, np.asarray(starts, dtype=int), np.asarray(boundaries, dtype=int)

def contrast_tables(counts, responses):
    n = np.asarray(counts, dtype=int)
    k = np.asarray(responses, dtype=int)
    assert n.ndim == k.ndim == 1 and len(n) == len(k) and len(n) >= 2
    assert np.all(n >= 0) and np.all((k >= 0) & (k <= n))
    left, right, starts, boundaries = contrast_indices(len(n))
    cn = np.r_[0, n.cumsum()]
    ck = np.r_[0, k.cumsum()]
    n_left = np.r_[n[left], cn[boundaries]-cn[starts]]
    n_right = np.r_[n[right], cn[-1]-cn[boundaries]]
    k_left = np.r_[k[left], ck[boundaries]-ck[starts]]
    k_right = np.r_[k[right], ck[-1]-ck[boundaries]]
    assert len(n_left) == len(n)*(len(n)-1)
    return n_left, n_right, k_left, k_right, len(left)

def evaluate_tail_guard(counts, responses, alpha=.05):
    n_left, n_right, k_left, k_right, pair_count = contrast_tables(counts, responses)
    p = np.ones(len(n_left), dtype=float)
    nonempty = (n_left > 0) & (n_right > 0)
    p[nonempty] = hypergeom.sf(k_left[nonempty]-1, n_left[nonempty]+n_right[nonempty],
                             k_left[nonempty]+k_right[nonempty], n_left[nonempty])
    assert np.isfinite(p).all() and np.all((p >= 0) & (p <= 1))
    pair_min = float(p[:pair_count].min())
    tail_min = float(p[pair_count:].min())
    adjusted = min(1., float(p.min())*len(p))
    winner = int(np.argmin(p))
    return dict(v2_min_pair_p=pair_min, v2_min_terminal_tail_p=tail_min,
                v2_registered_contrasts=len(p), v2_nonempty_contrasts=int(nonempty.sum()),
                v2_joint_bonferroni_p=adjusted, v2_shape_veto=bool(adjusted < alpha),
                v2_minimum_contrast_family='individual_pair' if winner < pair_count else 'terminal_tail',
                v2_minimum_left_N=int(n_left[winner]), v2_minimum_right_N=int(n_right[winner]))

def aggregate_with_order_contract(base, counts, responses):
    """Use the frozen fast implementation, diagnosing only its known order assertion.

    An unordered public-package result is preserved raw, but no usable policy is
    emitted. Any other assertion remains fatal. No sorting or replacement occurs.
    """
    n, k = np.asarray(counts, dtype=int), np.asarray(responses, dtype=int)
    try:
        output = base.aggregated_fit(n, k)
    except AssertionError:
        data = pd.DataFrame({'score': np.repeat(np.arange(len(n)), n),
            'response': np.concatenate([np.r_[np.ones(kk, dtype=int), np.zeros(nn-kk, dtype=int)] for nn, kk in zip(n, k)])})
        raw = base.fit_behavior_thresholds(data, 'score', 'response', base.Module2Config(min_valid_bins=4))
        finite = raw.anchors.selected_threshold.dropna().to_numpy(float)
        if len(finite) < 2 or np.all(np.diff(finite) >= 0):
            raise
        # Recover only the proven public-package order contract failure. All raw
        # numeric quantities and raw anchors come from the public API unchanged.
        total, positive = int(n.sum()), int(k.sum())
        curve, gate, anchors = raw.response_curve, raw.evidence_gate, raw.anchors
        valid = len(curve)
        mass = float(curve['count'].sum()/total)
        prerequisites = total >= base.CONFIG['min_N'] and min(positive, total-positive) >= base.CONFIG['min_each_response']
        short_support = (valid >= base.CONFIG['guarded_min_valid_bins'] and
                         mass >= base.CONFIG['guarded_min_supported_mass'] and
                         np.count_nonzero(n) <= base.CONFIG['maximum_short_score_levels'])
        policies = {}
        for policy, support in [('package_default_8', valid >= base.DEFAULT.min_valid_bins),
                                ('support_only_4', valid >= 4), ('short_semantic_guarded_v1', short_support)]:
            policies[policy] = dict(eligible=bool(prerequisites and support), gate_passed=False,
                                    any_anchor=False, unique_anchors=0)
        diagnostic = dict(N=total, response_positive=positive, valid_bins=valid, supported_mass=mass,
            dynamic_range=gate['isotonic_dynamic_range'], logistic_slope=gate['logistic_slope'],
            logistic_BIC_improvement=gate['logistic_bic_improvement'],
            common_evidence_gate_pass=bool(gate['passed']), **base.reversal_check(n, k),
            anchor_order_contract_valid=False, anchor_order_contract_status='whole_result_abstention_invalid_surviving_order')
        return policies, diagnostic, anchors, curve, gate
    output[1]['anchor_order_contract_valid'] = True
    output[1]['anchor_order_contract_status'] = 'valid'
    return output

base = SimpleNamespace(
    aggregated_fit=aggregated_fit, fit_behavior_thresholds=fit_behavior_thresholds,
    Module2Config=Module2Config, CONFIG=CONFIG, DEFAULT=DEFAULT,
    reversal_check=reversal_check,
)

def fit_both(counts, responses):
    output = aggregate_with_order_contract(base, counts, responses)
    policies, diagnostic, anchors = output[:3]
    tail = evaluate_tail_guard(counts, responses, CONFIG['pair_and_tail_joint_family_alpha'])
    eligible = policies[V1]['eligible']
    passed = bool(eligible and diagnostic['common_evidence_gate_pass'] and not tail['v2_shape_veto']
                  and diagnostic['anchor_order_contract_valid'])
    unique = int(anchors.operational_representative.sum())
    policies[V2] = dict(eligible=eligible, gate_passed=passed, any_anchor=bool(passed and unique),
                        unique_anchors=unique if passed else 0)
    return output, tail
