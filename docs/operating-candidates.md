# Compare operating candidates

A behavioral reference retains its meaning when a team considers another operating
threshold. The candidate comparison asks what workload and outcome coverage follow
under the proposed conditions.

## Capacity: Module 3A

`CapacityConfig(K=..., period=...)` declares an absolute alert budget in the supplied
cohort or planning period. The capacity floor is the smallest represented threshold
whose alert count is no greater than `K`.

For each available reference, `apply_capacity` selects an operating threshold at
or above both the reference and the capacity floor. Both values are reported.
An unavailable reference remains unavailable. Discrete-score ties can leave some
budget unused; `K=0` allows a zero-alert strategy.

Match the task, team, period, and cohort to the planning problem. Using a reference's
alert count as a comparison ceiling is a workload scenario, not a measurement of
hospital staffing capacity.

## Consequences: optional Module 3B

With an outcome label, compare thresholds by `loss = FP + R × FN`, where `R`
assigns a consequence to one missed outcome-positive encounter relative to one
flagged outcome-negative encounter. Report alerts and recall alongside the loss.

`audit_cost_governance(thresholds, behavior_threshold, R)` compares a named reference
with candidates at the same or lower workload, and reports an unconstrained
comparator. It does not redefine Low, Mid, or High.

```python
import pandas as pd
from universal_cutoff import audit_cost_governance

# behavior and learning_table come from the walkthrough's learning step.
low = behavior.anchors.loc[behavior.anchors.level == "Low", "selected_threshold"].iloc[0]
if pd.notna(low):
    comparison = audit_cost_governance(learning_table, float(low), R=10)
    print(comparison.summary)
```

`R=10` illustrates a declared scenario. The automatic comparison in
`run_framework(..., cost=...)` uses the first available operating representative
in priority order (Mid, Low, High). Use the direct API when a particular reference,
such as Low, is the intended comparator.

The [primary paper recipe](paper-reproduction.md) makes that Low comparison
explicit, using R = 11,299/804 and the learning alert count at Low as its ceiling.

## Where R comes from

Specify the triggered workflow, outcome, perspective, and time horizon. Prefer a
relevant local consequence analysis or stakeholder elicitation. Low-confidence tier
scenarios are also available for sensitivity exploration. See
[R elicitation](R_GUIDANCE.md) and [tier scenarios](RATIO_RECOMMENDER_FINDINGS.md).

The relation `R = (1 − p_t) / p_t` uses a decision-threshold probability under the
stated consequence model, not the Module 2 action probability. Loss is in
false-positive-equivalent units unless its components have independently defined
monetary values. Capacity analysis can be used without R.

## Carry choices into evaluation

Choose candidates on learning data, fix their values, and compare them on separate
data. Sensitivity analyses can compare those same candidates across R values.
Reselecting the best candidate in evaluation data is a separate analysis.
