# Interpret behavioral references

Module 2 estimates how frequently a recorded action occurs at different score
values. Its curve is an action probability, `P(recorded action | score)`.

## Probability targets

| Reference | Absolute target | If outside the fitted probability range |
|---|---|---|
| Low | Overall action rate in complete learning rows | Unavailable; no relative fallback. |
| Mid | 0.50 | Relative target halfway through the fitted range. |
| High | 0.80 | Relative target at 80% of the fitted range. |

For a range from `p_min` to `p_max`, the relative targets are
`p_min + 0.50 × (p_max − p_min)` and `p_min + 0.80 × (p_max − p_min)`.
They are tagged `provenance_tier="B"` and are not absolute 50% or 80% probabilities.
Absolute references have tier A; unavailable references have tier E.

The selected reference uses the first eligible curve bin reaching the target, then
maps to the first observed score at or above that bin value. Threshold policies
flag `score >= threshold`.

## Evidence support and output states

Defaults require at least 8 bins with at least 40 observations each. The fitted
isotonic range must be at least 0.08, the logistic slope positive, and logistic BIC
improvement at least 6. An unsupported monotone relationship returns no references. Insufficient bins or an unusable score range instead raise explicit
input/support errors.

Available reference thresholds must maintain their semantic order. An ordering inversion leaves
the affected reference unavailable. Coincident references keep their labels, with
one marked as the unique operating representative. A result can therefore contain
a full set, a partial set, or no supported references.

Read `selected_threshold`, `target_probability`, `anchor_family`,
`attainability_status`, `provenance_tier`, and `reason` together.

Run `python examples/reference_states.py` for deterministic synthetic examples
of full, relative, partial and no-reference outputs.

## Curve probability and action yield

An absolute Mid target of 0.5 describes the fitted action probability near that
score. Recorded-action yield describes the proportion with an action among
**all flagged encounters** with an observed action label. They need not be equal.

References describe how practice relates to the supplied score. They do not imply
that clinicians historically used those score cutoffs or that each observed action
was the correct decision.

## Uncertainty and optional corroboration

The manuscript uses semantic reference estimation. The package also supports
optional changepoint corroboration, which cannot move a reference. Bootstrap re-estimation describes reference stability and is
disabled by default. It is separate from internal validation operating evaluation.
See the [API reference](API_REFERENCE.md) for output objects.

## Synthetic output examples

| Scenario | Low | Mid | High | Interpretation |
|---|---|---|---|---|
| Absolute references | 51 (A) | 54 (A) | 87 (A) | All absolute probability targets are attainable |
| Relative references | 51 (A) | 51 (B) | 81 (B) | Absolute 0.50 and 0.80 are outside the fitted range; the prespecified relative targets are used |
| Partial references | 51 (A) | Unavailable (E) | 84 (A) | The absolute Mid crossing falls below Low; the ordering rule leaves Mid unavailable |
| No references | Unavailable (E) | Unavailable (E) | Unavailable (E) | The flat response pattern fails the support criteria |

A denotes an absolute reference, B a relative reference, and E an unavailable
level. The script saves the target probability, family, status and reason for
every row in `output/reference-states/states.csv`.

In the relative example, Mid 51 describes the midpoint of the fitted action-rate
range; it does not mean 50% action probability. In the partial example, keep the
available references and the reason for the unavailable level. Do not fill the
gap with a bootstrap median or an operating candidate.


## Operating candidates and evaluation

`apply_capacity` maps each available reference to a threshold that meets an
absolute alert budget K. The original reference is retained. Optional consequence
analysis compares `FP + R * FN` under the stated conditions; see the
[K/R guide](R_GUIDANCE.md).

Estimate references and select candidates on derivation data, then evaluate their
fixed values on separate data. `evaluate_frozen_thresholds` reports alert burden,
action yield and outcome performance. `evaluate_action_curve` evaluates the fixed
action-probability curve. Bootstrap reference stability and fixed-threshold
operating uncertainty answer different questions. Details and examples are in the
[API reference](API_REFERENCE.md).
