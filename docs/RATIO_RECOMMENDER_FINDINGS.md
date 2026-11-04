# Optional consequence-ratio scenarios

The optional `recommend_ratio()` function supplies a prespecified scenario when
workflow-specific consequence estimates or stakeholder elicitation are unavailable.
Use the [K/R specification guide](R_GUIDANCE.md) to define the intended action,
outcome, perspective and time horizon before choosing a scenario.

## Decision tiers

| Tier | Decision profile | Default R | Evaluated band |
|---|---|---:|---|
| A | Time-critical outcome with a relatively low-burden response | 20 | 15–49 |
| B | Serious outcome with a moderately burdensome response | 10 | 6–13 |
| C | Less time-critical outcome with an invasive or expensive response | 3 | 2–4 |

Select a tier by the consequences of a missed outcome and of the triggered action.
These are low-confidence scenario inputs. The package's `explain_tiers()` and
`tier_table()` functions provide the underlying definitions and source assumptions.

## Use the supplied threshold counts

```python
from universal_cutoff import build_threshold_table, recommend_ratio

thresholds = build_threshold_table(df, "score", outcome_col="outcome")
scenario = recommend_ratio(thresholds, tier="A", k_fracs=[0.05, 0.10, None])
print(scenario.summary())
```

`ratio_invariance()` identifies the tested R-grid values that select the same
threshold; `ratio_band_impact()` summarizes changes in alert volume and outcome
coverage. The grid band describes a computational sensitivity analysis.
The recommender does not redefine the Low/Mid/High reference thresholds.

## Manuscript scenario

The sepsis analysis uses the declared ratio **R = 11,299/804** and the Low-reference
workload ceiling. The saved derivation selections and fixed 34-versus-27
comparison are described in the [aggregate results guide](paper-results.md).
The optional tier values above are package inputs for users specifying other
workflow scenarios.
