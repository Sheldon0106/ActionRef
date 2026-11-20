# Sepsis consequence scenarios

Scenario A uses the resource-cost ratio R = 11,299/804. Scenario B adds a
modeled mortality cost per unflagged sepsis-positive encounter, assuming a
four-hour treatment delay for those encounters. It uses baseline mortality
from the MIMIC derivation set and age- and sex-specific remaining life
expectancy from the 2024 United States life tables. The central valuation
of $100,000 per quality-adjusted life-year gives R = 29.78 (rounded).
The revised threshold is selected in the MIMIC derivation set. Evaluations
at MIMIC and Stanford use fixed thresholds at the ratio for each scenario.

| Saved results | Contents |
|---|---|
| [Workload bounds](workload_bound_selection.csv) and [threshold switch points](low_bound_switchpoints.csv) | Full-sample selections under the reported workload and R settings |
| [Selection uncertainty](selection_bootstrap_summary.csv) and [threshold frequencies](selection_bootstrap_frequencies.csv) | Selections in 500 derivation-set patient resamples, each using its own Low workload bound |
| [Default strategies](default_strategy_results.csv) and [paired comparisons](default_strategy_paired_differences.csv) | Alert-none and alert-all comparisons at the Scenario A ratio |
| [Mortality scenario inputs and variations](mortality_scenario_inputs.csv) | Scenario B inputs, costs, and derivation selections with and without the Low bound |
| [Fixed operating results](mortality_scenario_fixed_results.csv) and [paired differences](mortality_scenario_paired_differences.csv) | FAE at the three Scenario B valuations, with intervals from 1,000 patient resamples per evaluation cohort |
| [Mortality by cohort](sepsis_mortality_rate_summary.csv) and [by threshold](threshold_sepsis_mortality.csv) | In-hospital mortality among sepsis-positive encounters with known vital status |
| [Recorded action below fixed thresholds](unflagged_sepsis_recorded_action.csv) | Recorded-action counts among unflagged sepsis-positive encounters with known action status |

The minimax summaries compare thresholds over a specified R grid separately
within each evaluation cohort. They describe cohort-specific secondary scenarios;
the primary operating candidate is selected on MIMIC derivation set data and then
applied unchanged to evaluation data.

The development selection curve provides aggregate confusion counts across
learning thresholds. The parent directory contains the corresponding learning
R-grid selections and the fixed 34-versus-27 evaluation comparison.

## Files

- `paper_minimax_behavior_budget.csv`
- `comparator_development_selection_curve.csv`
