# Extended aggregate results

These materials accompany the manuscript and supplement in release **v1.1.1**.
They contain cohort, subgroup, threshold and simulation summaries, with no
clinical records or identifiers. From the repository root, run:

```bash
python examples/reproduce_extended.py
```

The [assembly script](../../examples/reproduce_extended.py) reads saved public
summaries, checks their correspondence and writes copies to `output/extended/`.
It does not refit models, re-estimate intervals or rerun simulations. The
[manifest](manifest.json) identifies source files, source runs and checksums.

## Minimax regret

[minimax_regret.csv](minimax_regret.csv) contains six cohort-specific workload
scenarios, assembled from
`results/sepsis_primary/consequence_scenarios/paper_minimax_behavior_budget.csv`
by `examples/reproduce_extended.py`. The source analysis run is
`run_20261023T104445170533Z_5e79d9b15f84`. The saved scenarios use the existing
R grid and each cohort's reference workload; they are separate from external
evaluation of the revised threshold 34 selected in the MIMIC derivation set.

## Transfer-target sensitivity

[transfer_target_sensitivity.csv](transfer_target_sensitivity.csv) contains
three reference-level comparisons of fixed-score, workload-matched, risk-matched
and locally estimated thresholds. It is assembled from
`results/sepsis_primary/era_and_transport/paper_transport_decomposition.csv`
by `examples/reproduce_extended.py`, using saved results from
`run_20261023T104445170533Z_5e79d9b15f84`. The matching targets describe different
transfer questions; they do not replace the fixed-threshold external validation.

## Subgroup-level operating and calibration diagnostics

[subgroup_diagnostics.csv](subgroup_diagnostics.csv) joins 96 fixed-reference
operating rows with 32 subgroup calibration summaries across sex, age, race and
insurance. `examples/reproduce_extended.py` joins the two saved source tables in
`results/sepsis_primary/subgroups/` by cohort, subgroup variable and subgroup,
checking shared counts. The source run is
`run_20261023T104445170533Z_5e79d9b15f84`. Calibration values are point estimates
and repeat across the three reference levels within a subgroup. Eligibility,
unknown-category and requested-resample fields remain explicit; no interval is
inferred from these point estimates.

## Original eight-scenario simulation

[original_eight_scenarios.csv](original_eight_scenarios.csv) contains the 192
saved condition/method/reference error summaries from
`simulations/eight_scenarios/analysis2_existing_summary.csv`. The original
[runner](../../simulations/eight_scenarios/runner.py) uses seed **20260802**.
The original simulation run is `run_20260913T092841426893Z_727eb2dd9311`; the
error-summary run is `run_20261011T111658280658Z_d76a23f3bb9d`.
`examples/reproduce_extended.py` assembles the saved summaries. The separate
paired support-criteria simulation (seed **2026101101**) supplies eTable 14.

## Conventional-rule selection uncertainty

[conventional_selection_uncertainty.csv](conventional_selection_uncertainty.csv)
contains the saved threshold-selection summaries for six conventional rules,
with 100 requested resamples per rule. It is assembled from
`results/sepsis_primary/conventional_rules/comparator_selection_bootstrap_summary.csv`
by `examples/reproduce_extended.py`; source run
`run_20261023T104445170533Z_5e79d9b15f84`. Threshold-selection uncertainty and
operating uncertainty conditional on a fixed threshold are separate analyses.

## K/R specification guide

The [K/R guide](../../docs/R_GUIDANCE.md), linked from supplement eMethods 2,
defines workflow-specific capacity, consequence elicitation, scenario sources
and sensitivity analysis. Its stable public path is `docs/R_GUIDANCE.md`.
