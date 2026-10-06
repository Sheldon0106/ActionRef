# API reference

| Function | Purpose |
|---|---|
| `validate_score` / `evaluate_score` | Score completeness, optional outcome performance and calibration. |
| `fit_behavior_thresholds` | V7 binning, weighted isotonic curve, evidence gate, structural corroboration, semantic Low/Mid/High. |
| `bootstrap_module2` | Optional encounter or grouped re-estimation. `BootstrapConfig(enabled=False)` is the runtime default. |
| `build_threshold_table` | Per-observed-score alert, response, and optional outcome table plus zero-alert strategy. |
| `apply_capacity` | Absolute-K mapping preserving semantic thresholds and provenance. |
| `audit_cost_governance` | Same-or-lower-workload and unconstrained comparators, binding classification, near-optimal regions, lambda status. |
| `minimax_regret_cost_audit` | Secondary comparator minimizing worst-case FAE regret over a fixed R grid. |
| `build_simple_r_guidance` | Natural-frequency, action-probability, or direct-R route. Result carries `point_estimate_basis`. |
| `build_r_guidance` | Typed R scenario with component-cost or action-threshold derivation, provenance, warnings, safeguards. |
| `recommend_ratio` | Low-confidence decision-tier scenario for R plus a same-cutoff invariance verdict on the supplied threshold table. |
| `ratio_invariance` | Widest contiguous R-grid band selecting the same cutoff as a reference R at each capacity. |
| `ratio_band_impact` | Recall and alert-fraction spread across a prespecified R band and capacity set. |
| `tier_table` / `explain_tiers` | Machine-readable and plain-language views of the three published-threshold decision tiers. |
| `next_natural_frequency_question` | Adaptive 2-to-3-question generator. Requires `ElicitationFrame`; halts on inconsistent answers. |
| `r_guidance_frame_questions` | The four framing questions required before elicitation. |
| `evaluate_frozen_thresholds` | Frozen operating evaluation without learning or mutation. |
| `predict_action_probability` | Fixed action-curve interpolation with endpoint clipping. |
| `evaluate_action_curve` | Held-out action-probability metrics, reliability bins and optional paired patient-cluster intervals. |
| `audit_subgroups` | Subgroup evaluation with demographic, operational-proxy, or custom role. |
| `audit_temporal` | Era-normalized evaluation, subject-overlap audit, optional local Module 2 drift. |
| `audit_transport` | Frozen external evaluation plus optional local diagnostic re-estimation. |
| `run_framework` | One-score, one-response, optional-outcome orchestration. |

## Contracts

- Every Module 2 result serializes its full configuration snapshot.
- Outcome and response are separate inputs. They are never substituted for one another.
- Only changepoints with `status="supported"` and support at or above `min_cp_bootstrap_support` can corroborate an anchor.
- Corroboration cannot change `selected_threshold`.
- Ratio-tier outputs are optional Module 3B scenario inputs, use no Module 2 behavior
  fields, and cannot create, relabel, or replace Low/Mid/High.
- Ratio invariance is evaluated on the supplied discrete R grid; it is not a confidence interval.

Bootstrap result keys:

`validated_full_anchors`, `threshold_frequencies`, `joint_tier_audit`,
`joint_summary`, `adjacent_gap_summary`, `provenance_frequencies`,
`binning_stability`, `changepoint_support`, `failures`

## Action-curve evaluation

`predict_action_probability(scores, curve)` interpolates a fixed monotone curve
(`score`, `isotonic_rate`) and clips at its supported endpoints. It does not fit
or recalibrate probabilities. Missing/nonfinite scores return NaN.

`evaluate_action_curve(data, score_col, response_col, curve, learning_action_rate,
group_col=None, n_bootstrap=0, random_state=2026100288)` returns an
`ActionCurveEvaluation` with `points`, `intervals`, `reliability`, and `metadata`.
The comparator predicts the supplied learning action rate for each complete
evaluation row. Intervals require a group column and use paired resampling of
whole patient clusters conditional on the learned curve. Returned summaries
exclude patient identifiers and individual predictions.

Calibration intercept and slope are descriptive logistic fits to the fixed
predictions. They require at least 100 complete rows, 20 observations in each
action class, and 3 distinct predicted probabilities. The probability/logit clip
is 1e-6. A diagnostic fit is not used to update predictions.

See [independent evaluation](evaluation.md) for a complete example and
[paper reproduction](paper-reproduction.md) for the primary analysis protocol.
