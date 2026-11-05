# Conventional threshold rules

These tables compare conventional threshold-selection rules with the behavioral
references and the consequence-based candidate. Rule contracts distinguish
derivation-selected thresholds, supplied fixed thresholds and capacity conditions.

Selection uncertainty uses 100 requested resamples for the six selection rules;
fixed-policy operating uncertainty uses 200 resamples. The two analyses condition
on different quantities. Fixed operating intervals use the score-evaluable
resampling population; intervals for the base cohort size and all-encounter alert
rate are recorded as not estimated.

## Fixed operating rows

`rule_operating_rows.csv` supplies thresholds 26, 34, 40 and 45 at both evaluation
sites for Table 3 and eTable 6. The named rules retain their original derivation
selection. Policies that share a threshold have identical point counts.

`esrp_tier_boundaries.csv` supplies fixed thresholds 21, 31 and 45 at both sites.
They originate in the ESRP derivation study by Jin et al. (manuscript reference
29): sensitivity-target, Youden and specificity-target boundaries, respectively.
They were fixed in that study's internal validation cohort and applied unchanged
here. The original targets do not guarantee the same operating performance in
these clinical-only ActionRef outcome cohorts.

Both files report exact TP/FP/FN/TN and action counts, with inclusive `score >= t`.
Rates are proportions except fields named `per_1000`; recorded-action yield uses
known action status among flagged encounters. FAE uses exact R = 11,299/804.
No intervals have been inferred for the additional ESRP tier rows.
hashes. `examples/reproduce_extended.py` checks arithmetic and shared policy rows.

The [extended bundle](../../supplement_extended/README.md#conventional-rule-selection-uncertainty)
provides conventional-rule selection uncertainty separately.

## Files

- `rule_operating_rows.csv`
- `esrp_tier_boundaries.csv`
- `comparator_operating_results_extended.csv`
- `comparator_selection_bootstrap_summary.csv`
- `comparator_contracts_extended.csv`
