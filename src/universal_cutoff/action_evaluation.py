"""Evaluate an already learned action curve on separate encounters."""
from dataclasses import dataclass
from typing import Any, Dict, Optional
import warnings

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression

from .validation import binary_series, validate_columns


@dataclass
class ActionCurveEvaluation:
    points: Dict[str, Any]
    intervals: pd.DataFrame
    reliability: pd.DataFrame
    metadata: Dict[str, Any]


def predict_action_probability(scores, curve: pd.DataFrame):
    """Linearly interpolate supported curve coordinates; clip at both endpoints.

    ``curve`` has columns ``score`` and ``isotonic_rate``. Missing/nonfinite
    scores return NaN. The function neither fits a curve nor learns thresholds.
    """
    validate_columns(curve, ['score', 'isotonic_rate'])
    x = pd.to_numeric(curve.score, errors='coerce').to_numpy(dtype=float)
    p = pd.to_numeric(curve.isotonic_rate, errors='coerce').to_numpy(dtype=float)
    if (len(x) < 2 or not np.isfinite(x).all() or not np.isfinite(p).all()
            or np.any(np.diff(x) <= 0) or np.any(np.diff(p) < -1e-12)
            or np.any((p < 0) | (p > 1))):
        raise ValueError('Curve needs increasing distinct scores and finite monotone probabilities in [0, 1]')
    s = pd.to_numeric(pd.Series(scores), errors='coerce').to_numpy(dtype=float)
    out = np.full(len(s), np.nan)
    valid = np.isfinite(s)
    out[valid] = np.interp(s[valid], x, p)
    return out


def _summary(sums):
    n, actions, predicted, loss, constant_loss = sums
    return dict(N=int(n), action_rate=float(actions / n),
                mean_predicted=float(predicted / n),
                calibration_gap=float((predicted - actions) / n),
                action_Brier=float(loss / n),
                constant_development_rate_Brier=float(constant_loss / n),
                delta_Brier_vs_constant=float((loss - constant_loss) / n),
                Brier_skill=float(1 - loss / constant_loss) if constant_loss else np.nan)


def _calibration(y, p):
    result = dict(calibration_intercept=np.nan, calibration_slope=np.nan,
                  diagnostic_role='diagnostic_fit_of_frozen_predictions_not_recalibration',
                  diagnostic_status='insufficient_group_support')
    if len(y) < 100 or min(y.sum(), len(y) - y.sum()) < 20 or len(np.unique(p)) < 3:
        return result
    clipped = np.clip(p, 1e-6, 1 - 1e-6)
    logits = np.log(clipped / (1 - clipped)).reshape(-1, 1)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always', ConvergenceWarning)
        model = LogisticRegression(C=1e6, solver='lbfgs', max_iter=2000, tol=1e-10).fit(logits, y)
    if model.n_iter_[0] >= 2000 or any(issubclass(w.category, ConvergenceWarning) for w in caught):
        result['diagnostic_status'] = 'not_converged'
        return result
    result.update(calibration_intercept=float(model.intercept_[0]),
                  calibration_slope=float(model.coef_[0, 0]),
                  diagnostic_status='estimated_descriptive_only')
    return result


def evaluate_action_curve(data: pd.DataFrame, score_col: str, response_col: str,
                          curve: pd.DataFrame, learning_action_rate: float,
                          group_col: Optional[str] = None, n_bootstrap: int = 0,
                          random_state: int = 2026100288) -> ActionCurveEvaluation:
    """Fixed-curve action metrics with optional paired patient-cluster intervals.

    The comparator is the supplied learning action rate. Complete finite-score,
    observed-action rows are used. Bootstrap resamples whole groups, holding the
    curve and comparator fixed; it excludes uncertainty from learning the curve.
    Calibration intercept/slope are descriptive diagnostics, not recalibration.
    No individual predictions or group identifiers are returned.
    """
    validate_columns(data, [score_col, response_col, group_col])
    if not np.isfinite(learning_action_rate) or not 0 <= learning_action_rate <= 1:
        raise ValueError('learning_action_rate must be finite and in [0, 1]')
    if isinstance(n_bootstrap, bool) or int(n_bootstrap) != n_bootstrap or n_bootstrap < 0:
        raise ValueError('n_bootstrap must be a nonnegative integer')
    if n_bootstrap and group_col is None:
        raise ValueError('Patient-cluster intervals require group_col')
    score = pd.to_numeric(data[score_col], errors='coerce').to_numpy(dtype=float)
    action = binary_series(data[response_col], response_col).to_numpy(dtype=float)
    valid = np.isfinite(score) & np.isfinite(action)
    if not valid.any():
        raise ValueError('No complete score-action rows')
    s, y = score[valid], action[valid]
    p = predict_action_probability(s, curve)
    knots = pd.to_numeric(curve.score, errors='raise').to_numpy(dtype=float)
    loss, loss0 = (p - y) ** 2, (learning_action_rate - y) ** 2
    points = _summary([len(y), y.sum(), p.sum(), loss.sum(), loss0.sum()])
    pc = np.clip(p, 1e-6, 1 - 1e-6)
    points['action_log_loss'] = float(-(y * np.log(pc) + (1-y) * np.log(1-pc)).mean())
    points.update(_calibration(y, p))
    metadata = dict(input_N=len(data), complete_N=len(y), excluded_N=int((~valid).sum()),
                    prediction='continuous_interpolation_with_endpoint_clipping',
                    below_support_N=int((s < knots.min()).sum()),
                    above_support_N=int((s > knots.max()).sum()),
                    learning_action_rate=float(learning_action_rate),
                    bootstrap_conditioning='fixed curve and fixed learning-rate comparator',
                    bootstrap_unit='patient_cluster', bootstrap_replicates=int(n_bootstrap),
                    bootstrap_seed=int(random_state), group_N=None)
    groups = None
    if group_col is not None:
        ids = data.loc[valid, group_col]
        if ids.isna().any():
            raise ValueError('Complete score-action rows require nonmissing group identifiers')
        _, groups = np.unique(ids.to_numpy(), return_inverse=True)
        metadata['group_N'] = int(groups.max() + 1)
    interval_rows = []
    if n_bootstrap:
        ng = metadata['group_N']
        clusters = np.column_stack([np.bincount(groups), np.bincount(groups, weights=y),
                                    np.bincount(groups, weights=p), np.bincount(groups, weights=loss),
                                    np.bincount(groups, weights=loss0)])
        rng = np.random.default_rng(random_state)
        draws = pd.DataFrame([_summary(rng.multinomial(ng, np.full(ng, 1 / ng)) @ clusters)
                              for _ in range(int(n_bootstrap))])
        for metric in draws:
            values = draws[metric].to_numpy(dtype=float)
            values = values[np.isfinite(values)]
            lo, med, hi = np.quantile(values, [.025, .5, .975]) if len(values) else [np.nan] * 3
            interval_rows.append(dict(metric=metric, point=points[metric], B=int(n_bootstrap),
                                      unit='patient_cluster', finite_replicates=len(values),
                                      lower_025=lo, median=med, upper_975=hi))
    bin_id = np.minimum((p * 10).astype(int), 9)
    bins = []
    for b in range(10):
        mask = bin_id == b
        bins.append(dict(lower=b/10, upper=(b+1)/10, N=int(mask.sum()),
                         actions=int(y[mask].sum()),
                         observed=float(y[mask].mean()) if mask.any() else np.nan,
                         predicted=float(p[mask].mean()) if mask.any() else np.nan))
    return ActionCurveEvaluation(points, pd.DataFrame(interval_rows), pd.DataFrame(bins), metadata)
