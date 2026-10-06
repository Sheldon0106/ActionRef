import math
from itertools import combinations
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

from .config import Module2Config
from .exceptions import InsufficientBinsError, InputValidationError
from .results import Module2Result
from .validation import binary_series, numeric_series, validate_columns


PROVENANCE = {
    "A": "local_behavioral_absolute",
    "B": "local_behavioral_relative",
    "E": "explicit_abstention",
}
SELECTION_PRIORITY = {"Mid": 1, "Low": 2, "High": 3}


def _integer_like(values, tolerance=1e-8):
    values = np.asarray(values, dtype=float)
    return bool(len(values) and np.all(np.abs(values - np.round(values)) < tolerance))


def choose_bin_width(scores, config: Module2Config):
    score = numeric_series(pd.Series(scores)).dropna().to_numpy(float)
    if not len(score) or float(np.ptp(score)) <= 0:
        raise InputValidationError("Score has no usable range for Module 2")
    score_min, score_max = float(score.min()), float(score.max())
    score_range = score_max - score_min
    integer = _integer_like(score)
    unique_n = len(np.unique(score))
    if config.bin_width is not None:
        candidates = [float(config.bin_width)]
        reason = "manual override"
    elif integer and unique_n <= 20:
        candidates = [1.0]
        reason = "small discrete integer score"
    elif integer:
        candidates = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15]
        reason = "automatic valid-bin optimization"
    else:
        candidates = sorted(set(round(score_range / n, 6) for n in [40, 35, 30, 25, 20, 15, 10]))
        candidates = [x for x in candidates if x > 0]
        reason = "automatic valid-bin optimization"
    rows = []
    for width in candidates:
        bins = np.floor((score - score_min) / width) * width + score_min
        valid_n = int((pd.Series(bins).value_counts() >= config.min_bin_n).sum())
        rows.append({"bin_width": float(width), "valid_bins": valid_n,
                     "distance_to_target": abs(valid_n - config.target_valid_bins)})
    table = pd.DataFrame(rows)
    preferred = table[(table.valid_bins >= config.min_valid_bins) &
                      (table.valid_bins <= config.max_valid_bins)]
    if preferred.empty:
        preferred = table[table.valid_bins >= config.min_valid_bins]
    if preferred.empty:
        preferred = table
    chosen = preferred.sort_values(["distance_to_target", "bin_width"]).iloc[0]
    return {
        "bin_width": float(chosen.bin_width), "valid_bins": int(chosen.valid_bins),
        "integer_score": integer, "small_integer_score": bool(integer and unique_n <= 20),
        "score_min": score_min, "score_max": score_max, "score_range": score_range,
        "selection_reason": reason,
        "candidate_table": table.sort_values(["distance_to_target", "bin_width"]).reset_index(drop=True),
    }


def build_response_curve(data, score_col, response_col, bin_width, config):
    use = data[[score_col, response_col]].copy()
    use[score_col] = numeric_series(use[score_col])
    use[response_col] = binary_series(use[response_col], response_col)
    use = use.dropna(subset=[score_col, response_col])
    if use.empty:
        raise InputValidationError("No complete score-response rows")
    origin = float(use[score_col].min())
    use["score_bin"] = np.floor((use[score_col] - origin) / bin_width) * bin_width + origin
    curve = (use.groupby("score_bin")[response_col].agg(["mean", "size"]).reset_index()
             .rename(columns={"score_bin": "score", "mean": "observed_rate", "size": "count"}))
    curve = curve[curve["count"] >= config.min_bin_n].sort_values("score").reset_index(drop=True)
    if len(curve) < config.min_valid_bins:
        raise InsufficientBinsError("Only {} valid bins; {} required (min_bin_n={})".format(
            len(curve), config.min_valid_bins, config.min_bin_n))
    iso = IsotonicRegression(y_min=0, y_max=1, increasing=True, out_of_bounds="clip")
    curve["isotonic_rate"] = iso.fit_transform(
        curve.score.to_numpy(float), curve.observed_rate.to_numpy(float),
        sample_weight=curve["count"].to_numpy(float))
    return use, curve, iso


def behavior_evidence_gate(use, curve, score_col, response_col, config):
    dynamic = float(curve.isotonic_rate.max() - curve.isotonic_rate.min())
    x = use[score_col].to_numpy(float)
    y = use[response_col].to_numpy(int)
    n = len(y)
    p0 = float(np.clip(y.mean(), 1e-9, 1 - 1e-9))
    ll0 = float(np.sum(y * np.log(p0) + (1 - y) * np.log(1 - p0)))
    bic0 = -2 * ll0 + math.log(max(n, 2))
    try:
        model = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000).fit(x.reshape(-1, 1), y)
        p1 = np.clip(model.predict_proba(x.reshape(-1, 1))[:, 1], 1e-9, 1 - 1e-9)
        ll1 = float(np.sum(y * np.log(p1) + (1 - y) * np.log(1 - p1)))
        delta = float(bic0 - (-2 * ll1 + 2 * math.log(max(n, 2))))
        slope = float(model.coef_[0, 0])
    except Exception as exc:
        return {"status": "unsupported_abstention", "passed": False,
                "reason": "logistic gate failed: {!r}".format(exc),
                "isotonic_dynamic_range": dynamic, "logistic_slope": np.nan,
                "logistic_bic_improvement": np.nan}
    reasons = []
    if dynamic < config.min_isotonic_dynamic_range:
        reasons.append("isotonic dynamic range below threshold")
    if slope <= 0:
        reasons.append("nonpositive logistic slope")
    if delta < config.min_logistic_bic_improvement:
        reasons.append("insufficient logistic BIC improvement")
    passed = not reasons
    return {"status": "supported" if passed else "unsupported_abstention", "passed": passed,
            "reason": "supported monotone response structure" if passed else "; ".join(reasons),
            "n_valid_bins": int(len(curve)), "isotonic_dynamic_range": dynamic,
            "logistic_slope": slope, "logistic_bic_improvement": delta}


def _weighted_fit(x, y, w):
    sw = np.sqrt(w)
    beta, _, _, _ = np.linalg.lstsq(x * sw[:, None], y * sw, rcond=None)
    residual = y - x.dot(beta)
    return beta, float(np.sum(w * residual ** 2))


def structural_candidates(curve, config):
    x = curve.score.to_numpy(float)
    y = curve.isotonic_rate.to_numpy(float)
    w = curve["count"].to_numpy(float)
    n = len(x)
    _, null_wsse = _weighted_fit(np.column_stack([np.ones(n), x]), y, w)
    null_bic = n * np.log(null_wsse / max(w.sum(), 1) + 1e-12) + 2 * np.log(n)
    positions = list(range(config.min_bins_per_segment - 1,
                           n - config.min_bins_per_segment,
                           config.cp_candidate_stride))
    rows = []
    for n_cp in range(1, config.max_selected_changepoints + 1):
        for idxs in combinations(positions, n_cp):
            bounds = [-1] + list(idxs) + [n - 1]
            if any(bounds[i + 1] - bounds[i] < config.min_bins_per_segment for i in range(len(bounds) - 1)):
                continue
            wsse, slopes = 0.0, []
            for left, right in zip(bounds[:-1], bounds[1:]):
                take = np.arange(left + 1, right + 1)
                beta, part = _weighted_fit(np.column_stack([np.ones(len(take)), x[take]]), y[take], w[take])
                slopes.append(float(beta[1])); wsse += part
            bic = n * np.log(wsse / max(w.sum(), 1) + 1e-12) + (2 * (n_cp + 1)) * np.log(n)
            standardized = max(abs(np.diff(slopes))) * max(np.ptp(x), 1e-6) / max(np.ptp(y), 1e-6)
            rows.append({"n_cp": n_cp, "cps": tuple(float(x[i]) for i in idxs), "BIC": bic,
                         "BIC_improvement_vs_linear": float(null_bic - bic),
                         "standardized_slope_change": float(standardized)})
    return pd.DataFrame(rows).sort_values("BIC").reset_index(drop=True) if rows else pd.DataFrame()


def supported_changepoints(curve, candidates, config):
    if candidates.empty:
        return pd.DataFrame(columns=["cp", "bootstrap_support", "isotonic_rate_at_cp", "status"])
    best = candidates.iloc[0]
    if (best.BIC_improvement_vs_linear < config.min_structural_bic_improvement or
            best.standardized_slope_change < config.min_standardized_slope_change):
        return pd.DataFrame(columns=["cp", "bootstrap_support", "isotonic_rate_at_cp", "status"])
    rows = []
    for cp in best.cps:
        rate = float(np.interp(cp, curve.score, curve.isotonic_rate))
        rows.append({"cp": cp, "bootstrap_support": np.nan, "isotonic_rate_at_cp": rate,
                     "status": "point_evidence_pending_bootstrap"})
    return pd.DataFrame(rows)


def _abstention_rows(reason):
    return pd.DataFrame([{"level": level, "selection_priority": SELECTION_PRIORITY[level],
        "anchor_name": None, "anchor_family": None, "absolute_target": np.nan,
        "target_probability": np.nan, "attainability_status": "unreachable",
        "semantic_threshold_raw": np.nan, "semantic_threshold_operational": np.nan,
        "selected_threshold": np.nan, "selected_type": "abstention",
        "structural_status": "not_evaluated_after_abstention", "cp_corroborated": False,
        "corroborating_cp": np.nan, "provenance_tier": "E",
        "provenance_label": PROVENANCE["E"], "reason": reason,
        "operational_representative": False} for level in ["Low", "Mid", "High"]])


def derive_semantic_anchors(curve, observed_scores, response_prevalence,
                            changepoints, bin_width, gate, config):
    if not gate["passed"]:
        return _abstention_rows(gate["reason"])
    p_min, p_max = float(curve.isotonic_rate.min()), float(curve.isotonic_rate.max())
    rows = []
    for level, name, absolute, fraction in [
            ("Low", "T_pi_response", float(response_prevalence), None),
            ("Mid", "T50_response", 0.50, 0.50),
            ("High", "T80_response", 0.80, 0.80)]:
        attainable = p_min - 1e-12 <= absolute <= p_max + 1e-12
        family, target, tier = "absolute", absolute, "A"
        if not attainable:
            if level == "Low":
                rows.append({"level": level, "selection_priority": SELECTION_PRIORITY[level],
                    "anchor_name": name, "anchor_family": "absolute", "absolute_target": absolute,
                    "target_probability": absolute, "attainability_status": "unreachable",
                    "semantic_threshold_raw": np.nan, "semantic_threshold_operational": np.nan,
                    "selected_threshold": np.nan, "selected_type": "abstention",
                    "structural_status": "not_corroborated", "cp_corroborated": False,
                    "corroborating_cp": np.nan, "provenance_tier": "E",
                    "provenance_label": PROVENANCE["E"],
                    "reason": "Low absolute anchor unreachable; no relative fallback",
                    "operational_representative": False})
                continue
            family, target, tier = "relative", p_min + fraction * (p_max - p_min), "B"
            name = "T{}_relative_response".format(int(100 * fraction))
        eligible = curve[curve.isotonic_rate >= target - 1e-12]
        raw = float(eligible.iloc[0].score) if len(eligible) else np.nan
        observed = np.sort(numeric_series(pd.Series(observed_scores)).dropna().unique())
        candidates = observed[observed >= raw - 1e-12] if np.isfinite(raw) else []
        operational = float(candidates[0]) if len(candidates) else np.nan
        aligned = pd.DataFrame()
        if np.isfinite(raw) and changepoints is not None and not changepoints.empty:
            required_cp_columns = {"cp", "bootstrap_support", "isotonic_rate_at_cp", "status"}
            if required_cp_columns.issubset(changepoints.columns):
                support = pd.to_numeric(changepoints.bootstrap_support, errors="coerce")
                supported = changepoints[
                    changepoints.status.eq("supported")
                    & support.ge(config.min_cp_bootstrap_support)
                ]
                aligned = supported[(supported.cp >= raw - 1e-12) &
                    (supported.cp - raw <= config.max_alignment_bins * bin_width + 1e-12) &
                    (supported.isotonic_rate_at_cp >= target - 1e-12)]
        corroborated = not aligned.empty
        cp = float(aligned.sort_values("cp").iloc[0].cp) if corroborated else np.nan
        rows.append({"level": level, "selection_priority": SELECTION_PRIORITY[level],
            "anchor_name": name, "anchor_family": family, "absolute_target": absolute,
            "target_probability": float(target),
            "attainability_status": "absolute_attainable" if attainable else "relative_fallback",
            "semantic_threshold_raw": raw, "semantic_threshold_operational": operational,
            "selected_threshold": operational,
            "selected_type": "CP-aligned" if corroborated else ("semantic-only" if tier == "A" else "relative-anchor"),
            "structural_status": "corroborated" if corroborated else "not_corroborated",
            "cp_corroborated": corroborated, "corroborating_cp": cp,
            "provenance_tier": tier, "provenance_label": PROVENANCE[tier],
            "reason": "semantic threshold retained; changepoints are corroborative only",
            "operational_representative": False})
    out = pd.DataFrame(rows)
    low = out.loc[out.level == "Low", "selected_threshold"]
    mid = out.loc[out.level == "Mid", "selected_threshold"]
    high = out.loc[out.level == "High", "selected_threshold"]
    low_t = float(low.iloc[0]) if len(low) else np.nan
    mid_t = float(mid.iloc[0]) if len(mid) else np.nan
    high_t = float(high.iloc[0]) if len(high) else np.nan
    for level, bad in [("Mid", np.isfinite(low_t) and np.isfinite(mid_t) and mid_t < low_t - 1e-12),
                       ("High", np.isfinite(high_t) and np.isfinite(mid_t if np.isfinite(mid_t) else low_t) and
                        high_t < (mid_t if np.isfinite(mid_t) else low_t) - 1e-12)]:
        if bad:
            idx = out.index[out.level == level][0]
            out.loc[idx, ["selected_threshold", "semantic_threshold_operational"]] = np.nan
            out.loc[idx, "attainability_status"] = "unavailable_ordering"
            out.loc[idx, "selected_type"] = "abstention"
            out.loc[idx, "provenance_tier"] = "E"
            out.loc[idx, "provenance_label"] = PROVENANCE["E"]
            out.loc[idx, "reason"] = "semantic ordering inversion; no replacement permitted"
    used = []
    for idx in out.sort_values("selection_priority").index:
        threshold = out.loc[idx, "selected_threshold"]
        if np.isfinite(threshold) and not any(np.isclose(threshold, old) for old in used):
            out.loc[idx, "operational_representative"] = True
            used.append(float(threshold))
    return out.sort_values("level", key=lambda x: x.map({"Low": 0, "Mid": 1, "High": 2})).reset_index(drop=True)


def fit_behavior_thresholds(data: pd.DataFrame, score_col: str, response_col: str,
                            config: Optional[Module2Config] = None) -> Module2Result:
    config = config or Module2Config()
    validate_columns(data, [score_col, response_col])
    d = data[[score_col, response_col]].copy()
    d[score_col] = numeric_series(d[score_col])
    d[response_col] = binary_series(d[response_col], response_col)
    d = d.dropna(subset=[score_col, response_col])
    binning = choose_bin_width(d[score_col], config)
    use, curve, iso = build_response_curve(d, score_col, response_col, binning["bin_width"], config)
    gate = behavior_evidence_gate(use, curve, score_col, response_col, config)
    models = structural_candidates(curve, config) if gate["passed"] else pd.DataFrame()
    cps = supported_changepoints(curve, models, config) if gate["passed"] else pd.DataFrame()
    anchors = derive_semantic_anchors(curve, use[score_col], float(use[response_col].mean()),
                                      cps, binning["bin_width"], gate, config)
    clean_binning = dict(binning)
    candidates = clean_binning.pop("candidate_table")
    clean_binning["candidate_table"] = candidates
    return Module2Result(
        input_summary={"N_complete": int(len(use)), "response_prevalence": float(use[response_col].mean())},
        binning=clean_binning, response_curve=curve, evidence_gate=gate,
        structural_candidates=models, supported_changepoints=cps, anchors=anchors,
        config=config.snapshot(), isotonic_model=iso)
