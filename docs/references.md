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
improvement at least 6. An unsupported monotone relationship produces abstention
labels. Insufficient bins or an unusable score range instead raise explicit
input/support errors.

Available anchors must maintain their semantic order. An ordering inversion leaves
the affected reference unavailable. Coincident references keep their labels, with
one marked as the unique operating representative. A result can therefore contain
a full set, a partial set, or no supported references.

Read `selected_threshold`, `target_probability`, `anchor_family`,
`attainability_status`, `provenance_tier`, and `reason` together.

Run the [output-state examples](output-states.md) to see full, relative, partial
and abstention results with the same API.

## Curve probability and action yield

An absolute Mid target of 0.5 describes the fitted action probability near that
score. Recorded-action yield describes the proportion with an action among
**all flagged encounters** with an observed action label. They need not be equal.

References describe how practice relates to the supplied score. They do not imply
that clinicians historically used those score cutoffs or that each observed action
was the correct decision.

## Structural and bootstrap analyses

Changepoints can corroborate a reference after the required support checks; they
cannot move it. Bootstrap re-estimation describes reference stability and is
disabled by default. It is separate from held-out operating evaluation.
See the [API reference](API_REFERENCE.md) for output objects.
