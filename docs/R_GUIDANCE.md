# Setting K and R for a specified workflow

K is an alert budget for a named task, team and period. R is the relative
consequence of one missed outcome-positive encounter compared with one
false-positive alert. Specify these inputs for the proposed workflow before
comparing operating thresholds.

## Capacity

`CapacityConfig(K=..., period=...)` declares an absolute alert limit. The capacity
floor is the smallest represented threshold whose alert count is no greater
than K. `apply_capacity` maps each available reference to a threshold at or above
both the reference and this floor, retaining the original reference value.
Discrete-score ties can leave capacity unused; K = 0 permits a zero-alert strategy.

For example, 50 additional assessments per week is a capacity input. In the study,
the alert count at Low serves as a comparison ceiling, rather than a measurement
of staffing capacity. Capacity analysis can be used without R.

## Five-step consequence workflow

1. **Define the decision:** triggered action, target outcome, stakeholder
   perspective and time horizon. The proposed action may differ from the recorded
   action used to estimate references.
2. **Choose a source:** independently valued consequences in commensurate units,
   structured stakeholder elicitation, or a relevant published decision threshold.
   The optional tier recommender supplies scenario values.
3. **Specify a reference value and plausible range:** record sources and
   assumptions independently of the threshold that will be selected.
4. **Compare candidates on derivation data:** minimize `FP + R * FN` across the
   specified R grid and K. Loss ties favor more alerts, then the lower threshold.
5. **Evaluate fixed choices on separate data:** report alert burden, outcome
   coverage and weighted loss together.

A fixed pair's loss crossing and re-selection across an R grid answer different
questions. A grid stability band describes the evaluated grid points; it is
neither a continuous analytical interval nor a confidence interval.

## Natural-frequency elicitation

`ElicitationFrame` specifies `intended_action`, `target_outcome`,
`stakeholder_perspective` and `time_horizon`. For example:

> Would you accept nine additional assessments in outcome-negative encounters
> to identify one additional outcome-positive encounter, for this workflow and
> time horizon?

`next_natural_frequency_question` helps bracket the trade-off. If the largest
accepted ratio and smallest rejected ratio are available, the reported scenario
value is their geometric midpoint:

```text
R_primary = sqrt(R_largest_accepted * R_smallest_rejected)
```

The bracket is the uncertainty range. Accepting 13 and rejecting 19 gives a
range of 13–19 and a scenario value of 15.72. Elicited values carry low confidence.
One-sided or inconsistent responses return `insufficient_basis`, with no primary
R. The accepted and rejected trade-offs remain in the output for review.

## Other input routes

- **Valued consequences:** `R = sum(FN components) / sum(FP components)`;
  range bounds use FN lower / FP upper and FN upper / FP lower. Components must
  use the same unit and distinct names.
- **Action-threshold probability:** `R = (1 - p_t) / p_t`. Here `p_t` is the
  outcome probability at which the proposed action becomes worthwhile, distinct
  from the Module 2 recorded-action probability.
- **Direct R:** a prespecified scenario with documented assumptions and range.

Prevalence and a preferred score cutoff are not sources for R. Monetary
interpretation requires independently defined monetary consequences for both
error types.

## Optional tier scenarios

`recommend_ratio` supplies low-confidence scenarios when a workflow-specific
basis is unavailable. Choose a tier using the consequences of a miss and the
burden of the proposed response.

| Tier | Decision profile | Default R | Evaluated band |
|---|---|---:|---|
| A | Time-critical outcome with a relatively low-burden response | 20 | 15–49 |
| B | Serious outcome with a moderately burdensome response | 10 | 6–13 |
| C | Less time-critical outcome with an invasive or expensive response | 3 | 2–4 |

```python
from universal_cutoff import build_threshold_table, recommend_ratio

thresholds = build_threshold_table(derivation, "score", outcome_col="outcome")
scenario = recommend_ratio(thresholds, tier="A", k_fracs=[0.05, 0.10, None])
print(scenario.summary())
```

`ratio_invariance` identifies tested R values selecting the same threshold;
`ratio_band_impact` reports changes in workload and outcome coverage. `tier_table`
and `explain_tiers` expose the scenario definitions and source assumptions.
These inputs do not redefine Low, Mid or High.

## Study example

The sepsis scenario uses R = 11,299/804 for a proposed diagnostic and short-course
antibiotic workflow. The Low-reference workload ceiling is 116,236 alerts in
314,658 derivation encounters. Threshold 34 minimizes derivation-set weighted
loss at this R both with and without that ceiling. The recorded-action composite
used to estimate references has a separate definition.

The fixed 34-versus-27 loss comparison crosses at R approximately 20.77 in MIMIC
internal validation and 26.28 at Stanford. [Study materials](paper-reproduction.md)
provides the corresponding aggregate calculations and input requirements.

## Output interpretation

`build_r_guidance` returns the primary value, range, grid, basis, source,
confidence, status and warnings. Status values include `evidence_based`,
`consensus_based`, `locally_costed`, `scenario_based` and `insufficient_basis`.
K supplies workload context and does not enter the R derivation equations.

For a prespecified grid, `minimax_regret_cost_audit` compares the maximum regret
of each feasible threshold, where `regret(t, r) = loss(t, r) - min_s loss(s, r)`.
This is a separate scenario comparison; it neither estimates R nor replaces
the reference thresholds.

Method sources include Pauker and Kassirer (1980), Vickers and Elkin (2006),
Bojke et al. (2021), and Manski (2007); the study bibliography and package tier
metadata provide the relevant decision-theory and elicitation context.
