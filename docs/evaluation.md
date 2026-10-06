# Evaluate on separate data

Independent evaluation measures how a previously specified reference or candidate
performs in another set of encounters. It does not relearn the threshold.

```python
from universal_cutoff import evaluate_frozen_thresholds

report = evaluate_frozen_thresholds(
    evaluation, "score", references.anchors,
    response_col="response", outcome_col="outcome",
)
```

The input may be an anchors DataFrame or a mapping such as `{"Low": 27, "candidate": 31}`.
At least one finite threshold is required. If a requested value is not observed,
the table uses the next observed value representing the same `score >= threshold`
decision, including the zero-alert strategy when needed. Requested and evaluated
values are both reported.

## Match the evidence to the question

| Question | Evidence |
|---|---|
| Does the curve describe recorded actions? | Observed rates and support; held-out action-probability evaluation |
| Are reference values stable? | Bootstrap distributions and availability |
| What happens when a threshold is applied? | Alerts, action yield, recall, missed outcomes, and scenario loss |
| Does the workflow improve care? | Clinical review or prospective evaluation in its intended setting |

`evaluate_frozen_thresholds` supplies operating metrics, not calibration of the
learned action curve. That assessment requires fixed curve predictions and action
labels on separate data.

Use `evaluate_action_curve` for that separate assessment:

```python
from universal_cutoff import evaluate_action_curve

action_report = evaluate_action_curve(
    evaluation, "score", "response", references.response_curve,
    learning_action_rate=references.input_summary["response_prevalence"],
    group_col="patient_id", n_bootstrap=200, random_state=2026100288,
)
print(action_report.points)
print(action_report.intervals)
```

The curve and learning-rate comparator stay fixed. Prediction uses linear
interpolation with endpoint clipping; intervals resample all eligible encounters
within each sampled patient. They quantify evaluation uncertainty conditional on
the curve, rather than uncertainty from relearning it. The descriptive calibration
fit does not change the predictions. Returned data contain summaries and reliability
bins, without patient identifiers or individual predictions.

`predict_action_probability(scores, curve)` exposes the same interpolation for
local use. Missing or nonfinite scores return missing predictions. The
[paper recipe](paper-reproduction.md) also evaluates the original bin-assignment
sensitivity and records the separate action and policy denominators.

## Calibration and Module 1

`evaluate_score` reports optional outcome discrimination. Its outcome calibrator
is fitted on the supplied rows, so its calibration summaries are labeled
`apparent_in_sample`. Running it on a new cohort fits a local calibrator; it is not
evidence that a development calibrator transported successfully.

## Subgroups, time, and transport

`audit_subgroups`, `audit_temporal`, and `audit_transport` evaluate fixed thresholds.
Optional local reference re-estimation is a separate diagnostic. Differences can
reflect case mix, recording, resources, or workflow and guide further review.
See [diagnostic APIs](GOVERNANCE_DIAGNOSTICS.md).
