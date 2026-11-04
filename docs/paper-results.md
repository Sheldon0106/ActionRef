# Aggregate analysis results

The public results contain bin-level, cohort-level and threshold-level summaries
for the sepsis analysis. The [analysis map](evidence.md#manuscript-result-map)
connects these files to the manuscript.

## Primary sepsis analysis

`results/sepsis_primary/` provides cohort characteristics, reference estimates,
recorded-action curves, operating counts, action-probability estimates and
consequence comparisons. The `conventional_rules/` directory includes the fixed
ESRP study-tier boundaries and conventional-rule operating rows.

The [data contract](paper-data.md) defines the MIMIC derivation/internal validation
sets, Stanford external validation cohort, local estimation and action denominators.

## Additional scores and sensitivity analyses

`results/early_warning_scores/` contains the NEWS2, MEWS, REMS and qSOFA score
implementations and saved summaries. The primary sepsis directories also provide
component, time-window, subgroup, era and parameter-sensitivity results.

## Extended results

[Extended aggregate results](https://github.com/Sheldon0106/ActionRef/tree/main/results/supplement_extended)
contain minimax regret, transfer-target sensitivity, subgroup diagnostics,
original simulation summaries and conventional-rule selection uncertainty.
The [K/R guide](R_GUIDANCE.md) describes workflow-specific input choices.

## Calculation and verification

```bash
python examples/reproduce_paper.py --early-warning-scores
python examples/reproduce_extended.py
```

These commands recalculate rates and weighted losses from saved counts, check
source consistency and export numerical CSV summaries. Previously estimated
curves and uncertainty intervals are read from saved results. See the
[reproduction scope](paper-reproduction.md) for input requirements and commands.
