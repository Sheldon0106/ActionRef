"""
ratio_recommender.py -- picking the cost ratio R when no cost study exists.
==========================================================================
The optional cost-governance layer needs one decision-specific number:
``R = c_FN / c_FP``. Deriving it from a literature cost build is expensive and has
to be redone per setting, which puts it out of reach for many framework users.

This module gives a low-confidence, scenario-based route. Under constant relative
FP/FN consequences and the usual expected-loss assumptions, it rests on the standard
threshold identity
(Pauker & Kassirer, NEJM 1975/1980; Vickers & Elkin decision curve analysis):

    pt = c_FP / (c_FP + c_FN) = 1 / (1 + R)        <=>        R = (1 - pt) / pt

Thus R need not be expressed in currency: it can be read as the risk threshold at
which a decision maker is indifferent, expressed as odds. A prespecified scenario R
can therefore be read from a published threshold probability for a comparable
decision, without a monetary cost build.

Two properties make a coarse default good enough, and both are checkable:

1. R is set by two things a clinician can judge quickly -- how bad the miss is,
   and how burdensome or risky the response is. Time-critical harm with a low-burden
   response is high-R; slower harm with an invasive response is low-R.
   :data:`RATIO_TIERS` turns that into three literature-anchored cells.
2. The cost-optimal threshold is piecewise constant in R, so over wide bands the
   choice of R changes nothing. :func:`ratio_invariance` measures that band on the
   user's own data, and :func:`recommend_ratio` reports whether the default sits
   inside it. When it does, refining R will not move the selected cutoff on that
   discrete grid and at those capacities; this does not validate the tier clinically.

Nothing here reads treatment or behaviour data. The tier defaults come from
published thresholds for other decisions; the invariance band comes from the
score-by-outcome distribution alone. A ratio chosen this way is therefore
independent of the clinician-behaviour anchors it may later be compared against.

Reporting convention follows the decision-curve literature (Vickers et al., Eur Urol
2018): prespecify a reasonable RANGE of threshold probabilities rather than a point,
and report results across it.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from typing import Iterable, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd

from .module3b import _select_minimum
from .results import ThresholdTableResult


ConfusionInput = Union[pd.DataFrame, ThresholdTableResult]

# ---------------------------------------------------------------------------
# Scalar conversions between the ratio and its equivalent readings
# ---------------------------------------------------------------------------


def implied_ratio(pt: float) -> float:
    """R implied by a threshold probability: R = (1 - pt) / pt (the odds against)."""
    if not 0.0 < pt < 1.0:
        raise ValueError(f"Threshold probability must lie in (0, 1); got {pt!r}.")
    return (1.0 - pt) / pt


def implied_pt(ratio: float) -> float:
    """Threshold probability implied by a ratio: pt = 1 / (1 + R)."""
    if not np.isfinite(ratio) or ratio <= 0:
        raise ValueError(f"Cost ratio must be positive; got {ratio!r}.")
    return 1.0 / (1.0 + ratio)


def alerts_per_case(ratio: float) -> float:
    """Break-even alerts per outcome-positive case at the indifference risk: N = 1 + R.

    The clinician-facing reading of R. "R = 20" means little at the bedside;
    "about 21 workups per outcome-positive case at the decision margin" is easier
    to elicit, and :func:`ratio_from_alerts_per_case` converts the answer back. This
    is a threshold-odds interpretation, not the observed PPV or a causal NNT.
    """
    implied_pt(ratio)
    return 1.0 + ratio


def ratio_from_alerts_per_case(n: float) -> float:
    """Invert :func:`alerts_per_case`: R = N - 1."""
    if not np.isfinite(n) or n <= 1:
        raise ValueError(f"Alerts per case must exceed 1; got {n!r}.")
    return n - 1.0


# ---------------------------------------------------------------------------
# Literature-anchored tier table
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RatioTier:
    """One row of the default table: a decision profile, worked examples, and a default R.

    Pick a tier by describing the decision, not the condition label. The same condition
    can sit in different tiers when the triggered action changes from a low-burden test
    to an invasive intervention.
    """

    key: str
    label: str
    miss_profile: str
    response_profile: str
    pick_if: str
    examples: Tuple[str, ...]
    not_this_tier_if: str
    pt_low: float
    pt_high: float
    default_ratio: float
    conservative_ratio: float
    aggressive_ratio: float
    anchor: str

    @property
    def ratio_low(self) -> float:
        """Low end of the tier's ratio band (from the HIGH threshold probability)."""
        return implied_ratio(self.pt_high)

    @property
    def ratio_high(self) -> float:
        """High end of the tier's ratio band (from the LOW threshold probability)."""
        return implied_ratio(self.pt_low)

    def contains(self, ratio: float) -> bool:
        return self.ratio_low <= ratio <= self.ratio_high

    def options(self) -> List[Tuple[str, float, str]]:
        """Three usable R values inside the tier: (name, R, what it means in practice)."""
        return [
            (
                "cautious about over-alerting",
                self.conservative_ratio,
                f"about {alerts_per_case(self.conservative_ratio):.0f} break-even alerts per case at the margin",
            ),
            (
                "typical (start here)",
                self.default_ratio,
                f"about {alerts_per_case(self.default_ratio):.0f} break-even alerts per case at the margin",
            ),
            (
                "cautious about misses",
                self.aggressive_ratio,
                f"about {alerts_per_case(self.aggressive_ratio):.0f} break-even alerts per case at the margin",
            ),
        ]

    def describe(self) -> str:
        """Plain-language explanation of the tier, for a user choosing between them."""
        lines = [
            f"TIER {self.key} -- {self.label}",
            f"  Pick this if:  {self.pick_if}",
            f"  A miss means:  {self.miss_profile}",
            f"  Responding costs: {self.response_profile}",
            f"  Not this tier if: {self.not_this_tier_if}",
            "",
            "  Decisions that fit:",
        ]
        lines.extend(f"    - {example}" for example in self.examples)
        lines += [
            "",
            f"  Default R = {self.default_ratio:g}"
            f"  (act at {100 * implied_pt(self.default_ratio):.1f}% risk;"
            f" ~{alerts_per_case(self.default_ratio):.0f} break-even alerts per case at the margin)",
            f"  Sensible range: R = {self.ratio_low:.0f} to {self.ratio_high:.0f}",
        ]
        for name, ratio, meaning in self.options():
            lines.append(f"    R = {ratio:<5g} {name:<28} {meaning}")
        lines += ["", f"  Anchored to: {self.anchor}"]
        return "\n".join(lines)


def _load_ratio_tiers() -> Tuple[RatioTier, ...]:
    """Load decision examples from package data to keep the Python core generic."""
    with resources.open_text(
        "universal_cutoff.data", "ratio_tiers.json", encoding="utf-8"
    ) as handle:
        rows = json.load(handle)
    tiers = []
    for row in rows:
        values = dict(row)
        values["examples"] = tuple(values["examples"])
        tiers.append(RatioTier(**values))
    return tuple(tiers)


RATIO_TIERS = _load_ratio_tiers()


def get_tier(key: str) -> RatioTier:
    """Look up a tier by key ('A', 'B', 'C'); case-insensitive."""
    wanted = str(key).strip().upper()
    for tier in RATIO_TIERS:
        if tier.key == wanted:
            return tier
    raise KeyError(f"Unknown tier {key!r}; expected one of {[t.key for t in RATIO_TIERS]}.")


def explain_tiers() -> str:
    """The whole tier guide as text. Print this when a user asks 'what R should I use?'."""
    header = [
        "CHOOSING R -- the decision-specific number used by the optional cost layer",
        "=" * 78,
        "",
        "R encodes the relative consequence of a miss versus a false alert.",
        "R = 20 corresponds to a 4.8% action threshold, or about 21 break-even",
        "alerts per outcome-positive case at the decision margin.",
        "This is not observed PPV and not a causal number needed to treat.",
        "",
        "You do not need a cost study to set it. Answer two questions about the",
        "DECISION your alert triggers -- not about the disease:",
        "",
        "  1. If we miss this, how fast and how badly does the patient suffer?",
        "  2. If we act on someone who turns out to be well, what did that cost them?",
        "",
        "Fast harm plus a cheap response pushes R up. Slow harm plus an invasive",
        "response pushes R down. Then read off the tier below.",
        "",
        "If you would rather answer one question instead: how many patients would you",
        "work up to catch one case? Subtract one -- that is your R.",
        "",
        "=" * 78,
        "",
    ]
    body = "\n\n".join(tier.describe() for tier in RATIO_TIERS)
    footer = [
        "",
        "",
        "=" * 78,
        "",
        "Then check whether the choice even matters. Run recommend_ratio() on your own",
        "threshold table: it reports the range of R that produces the SAME cutoff on your",
        "data. That range is usually wide, and when your alert capacity is the binding",
        "constraint it covers everything -- the model alerts the highest-risk patients until",
        "the budget runs out no matter what R you picked. In that case any tier value does,",
        "and you can say so in your write-up instead of defending a number.",
        "",
        "Where the range is narrow, report your results across the tier band rather than",
        "at a single R (standard practice in decision curve analysis).",
    ]
    return "\n".join(header) + body + "\n".join(footer)


def tier_table() -> pd.DataFrame:
    """The default table as a DataFrame, for dropping into a paper or a README."""
    return pd.DataFrame(
        [
            {
                "tier": t.key,
                "decision_profile": t.label,
                "pick_if": t.pick_if,
                "miss": t.miss_profile,
                "response": t.response_profile,
                "examples": "; ".join(t.examples),
                "pt_low": t.pt_low,
                "pt_high": t.pt_high,
                "ratio_low": round(t.ratio_low, 2),
                "ratio_high": round(t.ratio_high, 2),
                "default_ratio": t.default_ratio,
                "alerts_per_case_at_default": round(alerts_per_case(t.default_ratio), 1),
                "published_anchor": t.anchor,
            }
            for t in RATIO_TIERS
        ]
    )


# ---------------------------------------------------------------------------
# How much the ratio actually matters on THIS dataset
# ---------------------------------------------------------------------------

DEFAULT_RATIO_GRID: Tuple[float, ...] = tuple(
    round(float(r), 2) for r in np.unique(np.concatenate([np.arange(1.0, 20.5, 0.5), np.arange(21.0, 101.0, 1.0)]))
)


def _prepare_confusion(conf: ConfusionInput) -> Tuple[pd.DataFrame, int]:
    """Normalize either this package's threshold result or a confusion DataFrame.

    The update that introduced the recommender used a stand-alone cost-layer table.
    ``universal_cutoff`` instead exposes :class:`ThresholdTableResult`; accepting both
    keeps the public helper convenient without adding a second threshold engine.
    """
    if isinstance(conf, ThresholdTableResult):
        table = conf.table.copy()
        policy_n = int(conf.policy_N)
    elif isinstance(conf, pd.DataFrame):
        table = conf.copy()
        policy_n = 0
    else:
        raise TypeError("conf must be a pandas DataFrame or ThresholdTableResult")

    required = {"threshold", "TP", "FP", "FN"}
    missing = required.difference(table.columns)
    if missing:
        raise ValueError("confusion table is missing required columns: {}".format(sorted(missing)))
    if table.empty:
        raise ValueError("confusion table is empty")

    numeric = ["threshold", "TP", "FP", "FN"]
    if "alert_count" not in table:
        table["alert_count"] = table["TP"] + table["FP"]
    numeric.append("alert_count")
    for column in numeric:
        table[column] = pd.to_numeric(table[column], errors="coerce")
    if table[numeric].isna().any().any() or np.any(~np.isfinite(table[numeric].to_numpy(float))):
        raise ValueError("confusion table columns must contain finite numeric values")
    if (table[["TP", "FP", "FN", "alert_count"]] < 0).any().any():
        raise ValueError("confusion counts and alert_count must be nonnegative")

    if policy_n <= 0 and "policy_N" in table:
        values = pd.to_numeric(table["policy_N"], errors="coerce").dropna().unique()
        if len(values) == 1:
            policy_n = int(values[0])
    if policy_n <= 0 and "N" in table:
        values = pd.to_numeric(table["N"], errors="coerce").dropna().unique()
        if len(values) == 1:
            policy_n = int(values[0])
    if policy_n <= 0 and "TN" in table:
        totals = table["TP"] + table["FP"] + table["FN"] + pd.to_numeric(
            table["TN"], errors="coerce"
        )
        finite_totals = totals[np.isfinite(totals)]
        if len(finite_totals):
            policy_n = int(finite_totals.max())
    if policy_n <= 0:
        policy_n = int(table["alert_count"].max())
    if policy_n <= 0:
        raise ValueError("could not infer a positive policy cohort size")

    if "alert_fraction" in table:
        table["_alert_fraction"] = pd.to_numeric(table["alert_fraction"], errors="coerce")
    elif "alert_frac" in table:
        table["_alert_fraction"] = pd.to_numeric(table["alert_frac"], errors="coerce")
    else:
        table["_alert_fraction"] = table["alert_count"] / float(policy_n)
    if table["_alert_fraction"].isna().any():
        raise ValueError("alert fractions must be numeric when supplied")
    return table, policy_n


def _capacity_limit(k_frac: Optional[float], policy_n: int) -> Optional[int]:
    if k_frac is None:
        return None
    if isinstance(k_frac, bool) or not np.isfinite(k_frac) or k_frac < 0 or k_frac > 1:
        raise ValueError("k_fracs values must be None or finite fractions in [0, 1]")
    return int(np.floor(float(k_frac) * policy_n + 1e-12))


def _cost_optimal_row(
    table: pd.DataFrame, policy_n: int, ratio: float,
    k_frac: Optional[float], c_fp: float,
) -> pd.Series:
    if not np.isfinite(ratio) or ratio <= 0:
        raise ValueError("ratios must be finite and positive")
    if not np.isfinite(c_fp) or c_fp <= 0:
        raise ValueError("c_fp must be finite and positive")
    limit = _capacity_limit(k_frac, policy_n)
    feasible = table if limit is None else table[table["alert_count"] <= limit]
    if feasible.empty:
        raise ValueError("no threshold strategy satisfies capacity fraction {!r}".format(k_frac))
    sweep = feasible.copy()
    sweep["cost_FAE"] = float(c_fp) * (sweep["FP"] + float(ratio) * sweep["FN"])
    return _select_minimum(sweep)


def _optimal_thresholds(
    table: pd.DataFrame, policy_n: int, ratios: Sequence[float],
    k_frac: Optional[float], c_fp: float,
) -> np.ndarray:
    out = np.empty(len(ratios), dtype=float)
    for i, ratio in enumerate(ratios):
        out[i] = float(_cost_optimal_row(table, policy_n, float(ratio), k_frac, c_fp)["threshold"])
    return out


def _band_around(
    ratios: np.ndarray, thresholds: np.ndarray, reference_ratio: float
) -> Tuple[float, float]:
    """Widest contiguous run of ratios whose optimal threshold matches the reference's."""
    idx = int(np.argmin(np.abs(ratios - reference_ratio)))
    target = thresholds[idx]
    lo = idx
    while lo > 0 and thresholds[lo - 1] == target:
        lo -= 1
    hi = idx
    while hi < len(ratios) - 1 and thresholds[hi + 1] == target:
        hi += 1
    return float(ratios[lo]), float(ratios[hi])


def ratio_invariance(
    conf: ConfusionInput,
    reference_ratio: float,
    k_fracs: Iterable[Optional[float]] = (None,),
    ratio_grid: Optional[Sequence[float]] = None,
    c_fp: float = 1.0,
) -> pd.DataFrame:
    """For each capacity, the band of R that leaves the cost-optimal threshold unchanged.

    One row per ``K_frac``. ``ratio_band_low``/``ratio_band_high`` bound the widest
    contiguous run of ratios in ``ratio_grid`` that selects the same threshold as
    ``reference_ratio``; ``distinct_thresholds`` counts how many different thresholds
    the whole grid produces, so a value of 1 means R is irrelevant at that capacity.
    Uses only the confusion table -- no behaviour, treatment, or cost data. Bands
    are discrete-grid results, not analytic confidence intervals.
    """
    if not np.isfinite(reference_ratio) or reference_ratio <= 0:
        raise ValueError("reference_ratio must be finite and positive")
    grid = np.asarray(list(ratio_grid) if ratio_grid is not None else DEFAULT_RATIO_GRID, dtype=float)
    if grid.size == 0:
        raise ValueError("ratio_grid is empty.")
    if np.any(~np.isfinite(grid)) or np.any(grid <= 0):
        raise ValueError("ratio_grid must contain finite positive values")
    if not np.isclose(grid, float(reference_ratio), atol=1e-12, rtol=0).any():
        grid = np.append(grid, float(reference_ratio))
    grid = np.unique(grid)
    table, policy_n = _prepare_confusion(conf)
    capacities = list(k_fracs)
    if not capacities:
        raise ValueError("k_fracs is empty")
    rows = []
    for kf in capacities:
        thresholds = _optimal_thresholds(table, policy_n, grid, kf, c_fp)
        lo, hi = _band_around(grid, thresholds, reference_ratio)
        ref_threshold = float(thresholds[int(np.argmin(np.abs(grid - reference_ratio)))])
        rows.append(
            {
                "K_frac": np.nan if kf is None else float(kf),
                "reference_ratio": float(reference_ratio),
                "threshold_at_reference": ref_threshold,
                "ratio_band_low": lo,
                "ratio_band_high": hi,
                "band_covers_grid": bool(lo <= grid.min() and hi >= grid.max()),
                "distinct_thresholds": int(np.unique(thresholds).size),
                "grid_low": float(grid.min()),
                "grid_high": float(grid.max()),
            }
        )
    return pd.DataFrame(rows)


def ratio_band_impact(
    conf: ConfusionInput,
    ratio_low: float,
    ratio_high: float,
    k_fracs: Iterable[Optional[float]] = (None,),
    ratio_grid: Optional[Sequence[float]] = None,
    c_fp: float = 1.0,
) -> pd.DataFrame:
    """What actually changes across a ratio band, in decision terms rather than threshold units.

    Knowing the optimal threshold moves is not enough to know it matters: two adjacent
    cutoffs on a coarse score can be near-identical operating points. This reports the
    spread in recall and alert fraction across ``[ratio_low, ratio_high]``, which is the
    quantity a reader cares about. ``recall_spread_pp`` is in percentage points.
    """
    if (not np.isfinite(ratio_low) or not np.isfinite(ratio_high)
            or ratio_low <= 0 or ratio_high < ratio_low):
        raise ValueError("ratio band must be finite, positive, and ordered low to high")
    grid = np.asarray(list(ratio_grid) if ratio_grid is not None else DEFAULT_RATIO_GRID, dtype=float)
    if np.any(~np.isfinite(grid)) or np.any(grid <= 0):
        raise ValueError("ratio_grid must contain finite positive values")
    grid = np.unique(grid[(grid >= ratio_low) & (grid <= ratio_high)])
    if grid.size == 0:
        raise ValueError(f"No grid ratios fall inside [{ratio_low}, {ratio_high}].")
    table, policy_n = _prepare_confusion(conf)
    capacities = list(k_fracs)
    if not capacities:
        raise ValueError("k_fracs is empty")
    rows = []
    for kf in capacities:
        recalls, fracs, thresholds = [], [], []
        for ratio in grid:
            best = _cost_optimal_row(table, policy_n, float(ratio), kf, c_fp)
            tp, fn = float(best["TP"]), float(best["FN"])
            recalls.append(tp / (tp + fn) if (tp + fn) else np.nan)
            fracs.append(float(best["_alert_fraction"]))
            thresholds.append(float(best["threshold"]))
        rows.append(
            {
                "K_frac": np.nan if kf is None else float(kf),
                "band_low": float(ratio_low),
                "band_high": float(ratio_high),
                "threshold_min": min(thresholds),
                "threshold_max": max(thresholds),
                "recall_min": min(recalls),
                "recall_max": max(recalls),
                "recall_spread_pp": 100.0 * (max(recalls) - min(recalls)),
                "alert_frac_min": min(fracs),
                "alert_frac_max": max(fracs),
                "alert_frac_spread_pp": 100.0 * (max(fracs) - min(fracs)),
            }
        )
    return pd.DataFrame(rows)


@dataclass(frozen=True)
class RatioRecommendation:
    """What :func:`recommend_ratio` returns: a default, and whether it matters."""

    tier: RatioTier
    ratio: float
    threshold_probability: float
    alerts_per_case: float
    invariance: pd.DataFrame
    status: str = "scenario_based"
    confidence: str = "low"
    interpretation_guard: str = (
        "Tier defaults are prespecified scenario values, not estimates of the true R "
        "and not claims of clinical utility."
    )
    module2_separation_guard: str = (
        "Ratio recommendation is an optional Module 3B input and cannot define, "
        "relabel, or replace Low/Mid/High."
    )

    @property
    def default_is_safe(self) -> bool:
        """Whether the whole tier selects one cutoff; this is not a clinical-safety claim."""
        lo, hi = self.tier.ratio_low, self.tier.ratio_high
        return bool(
            (self.invariance["ratio_band_low"] <= lo).all()
            and (self.invariance["ratio_band_high"] >= hi).all()
        )

    def summary(self) -> str:
        lines = [
            self.tier.describe(),
            "",
            "-" * 78,
            f"USING R = {self.ratio:g} ON YOUR DATA",
            "-" * 78,
            f"  Alert once the patient's risk passes {100 * self.threshold_probability:.1f}%,",
            f"  i.e. about {self.alerts_per_case:.0f} alerts per outcome-positive case at",
            "  the decision margin (not observed PPV and not a causal NNT).",
            f"  Status: {self.status}; confidence: {self.confidence}.",
            "",
            "  Where your cutoff would move if you changed R:",
        ]
        for _, row in self.invariance.iterrows():
            cap = "no capacity limit" if np.isnan(row["K_frac"]) else f"capacity {100 * row['K_frac']:g}%"
            if row["band_covers_grid"]:
                verdict = "any R gives this cutoff"
            elif row["ratio_band_low"] <= self.tier.ratio_low and row["ratio_band_high"] >= self.tier.ratio_high:
                verdict = "whole tier gives this cutoff"
            else:
                verdict = "cutoff moves within the tier"
            lines.append(
                f"    {cap:>18}: cutoff {row['threshold_at_reference']:<10.4g} "
                f"holds for R {row['ratio_band_low']:g}-{row['ratio_band_high']:g}"
                f"   ({verdict})"
            )
        lines.append("")
        if self.default_is_safe:
            lines += [
                "  VERDICT: R does not change the selected cutoff over the requested tier",
                "  band, grid, and capacities. Report that discrete-grid invariance together",
                "  with the prespecified tier; it does not validate the tier clinically.",
            ]
        else:
            lines += [
                "  VERDICT: R matters at some capacities. Two options, both defensible:",
                "    1. Report your results across the tier band rather than at one R",
                "       (the usual convention in decision curve analysis), or",
                "    2. Narrow R for your setting -- ask a clinician how many alerts per",
                "       case caught they would accept, and use that answer minus one.",
            ]
        lines += ["", "  " + self.interpretation_guard, "  " + self.module2_separation_guard]
        return "\n".join(lines)


def recommend_ratio(
    conf: ConfusionInput,
    tier: str,
    k_fracs: Iterable[Optional[float]] = (None,),
    ratio: Optional[float] = None,
    ratio_grid: Optional[Sequence[float]] = None,
    c_fp: float = 1.0,
) -> RatioRecommendation:
    """Recommend R for a disease with no cost study, and say whether the choice matters.

    ``tier`` is a key from :data:`RATIO_TIERS` ('A', 'B', 'C') describing the decision,
    not the disease. ``ratio`` overrides the tier default -- pass the user's own number
    (from a cost build, a guideline threshold, or a framed answer about break-even alerts
    per case at the decision margin) to keep the invariance check while replacing the default.
    """
    chosen_tier = get_tier(tier)
    value = float(chosen_tier.default_ratio if ratio is None else ratio)
    invariance = ratio_invariance(
        conf, reference_ratio=value, k_fracs=k_fracs, ratio_grid=ratio_grid, c_fp=c_fp
    )
    return RatioRecommendation(
        tier=chosen_tier,
        ratio=value,
        threshold_probability=implied_pt(value),
        alerts_per_case=alerts_per_case(value),
        invariance=invariance,
    )
