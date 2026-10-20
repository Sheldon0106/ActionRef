# Analysis and reproduction scope

The repository accompanies the **JAMIA submission, October 2026**. It provides
analysis scripts, configurations, synthetic examples and saved aggregate results.
Patient-level MIMIC-IV-ED, MIMIC-IV and MC-MED data must be obtained from
[PhysioNet](https://physionet.org/) under its credentialing and data-use requirements.
Patient records and identifiers are not redistributed.

## Use the public aggregate entry point

```bash
python -m pip install -e ".[test,research]"
python examples/reproduce_paper.py
python examples/reproduce_paper.py --early-warning-scores
```

This command recalculates sepsis operating rates, recorded-action yields and the
fixed 31-versus-27 loss comparison from saved aggregate counts. Action-probability
point estimates and some uncertainty intervals are read from saved summaries;
this entry point does not re-estimate those intervals or rebuild the patient-level
cohorts. Outputs are written to ignored `output/paper/`.

The optional flag adds Figure 4: ESRP, NEWS, MEWS and REMS at the fixed MIMIC
references in both evaluation cohorts. It checks recalculated alert rates and
sepsis sensitivity against saved rates. MIMIC denominators are **127,528 for
ESRP** and **127,533 for the other scores**; Stanford uses **118,385**.
The manuscript's recorded-action yield excludes flagged encounters with missing
action labels from its denominator.

The original output stems beginning `etable35_`, `etable36_` and `etable37_`
are retained for compatibility. Their current manuscript locations are eTable 9B,
eTable 6C and eTable 5B, respectively. They are not current table numbers.

## Supplement source map

Paths below are relative to the repository root. `S/` means
`results/sepsis_primary/`, `E/` means `results/early_warning_scores/`.
Each added aggregate bundle has a README with manuscript checks and a manifest
with portable provenance and source/public-copy hashes. Original CSV field names
and numerical values are preserved.

**Recalculated** means arithmetic on saved aggregate counts; it does not mean
rerunning a clinical analysis. **Saved** means reading previously estimated
values, including uncertainty intervals. **Protocol** identifies methods,
configuration or explanatory material rather than an estimated result.

| Supplement item | Repository source | Reproduction scope |
|---|---|---|
| eTable 1: defaults | `configs/sepsis_primary.json`; `src/universal_cutoff/`; [reference rules](references.md) | Protocol; defaults unchanged |
| eTable 2: support/target sensitivity | `S/reference_sensitivity/semantic_gate_one_factor_sensitivity.csv`, `semantic_target_selection.csv` | Saved settings, thresholds and support summaries |
| eTable 3: K/R specification | [R guidance](R_GUIDANCE.md); [capacity and consequences](operating-candidates.md); `configs/sepsis_primary.json` | Protocol and declared scenario inputs |
| eTable 4: action components | `S/components/component_definition_registry.csv`, `component_missingness_prevalence.csv`, `component_thresholds_point.csv`, `leave_one_component_out_sensitivity.csv`, `threshold_action_workload_matrix.csv` | Saved component definitions, counts, proportions and references |
| eTable 5A: consequence inputs | `configs/sepsis_primary.json`; [R guidance](R_GUIDANCE.md) | Declared totals 11,299 / 804; the component cost assumptions and literature sources are in the Supplement |
| eTable 5B: fixed 31 versus 27 | `S/operating_counts.csv`, `fixed_candidate_R_sensitivity.csv` | Recalculated FP + R × FN and equality values 17.19 / 22.51 |
| eTable 5C: minimax scenario | `S/consequence_scenarios/paper_minimax_behavior_budget.csv` | Saved secondary cohort-specific scenario; separate from learning-selected candidate 31 |
| eTable 6A: ESRP outcome assessment | `S/score_assessment/paper_module1_point.csv`, `paper_module1_bootstrap_ci.csv` | Saved discrimination, calibration and intervals |
| eTable 6B: other scores | `E/default/module1_current_points.csv`, `module1_current_intervals.csv` | Saved score performance and intervals |
| eTable 6C: action probability | `S/sepsis_action_points.json`, `sepsis_action_intervals.json`, `sepsis_action_reliability.json` | Saved estimates and 200-resample conditional intervals |
| eTable 6D: logistic comparison | `S/logistic_comparison/analysis3_curve_comparison.csv`, `analysis3_logistic_crossings.csv`, `analysis3_paired_Brier_interval.csv` | Saved; High first native score = 55, first supported bin = 57 |
| eTable 7: Stanford components | `S/components/stanford_component_local_thresholds.csv`, `stanford_component_local_bootstrap_summary.csv`, `component_local_vs_transport_comparison.csv`, `mimic_component_frozen_stanford_operating.csv` | Saved local references and separate transported evaluations |
| eTable 8A-B: reference uncertainty | `S/reference_bootstrap/reference_summary.csv`, `joint_reference_summary.json`, `reference_pair_stability.csv` | Saved 500-resample summaries; primary site rows also supply Table 2 |
| eTable 8C: absolute/relative families | `S/reference_bootstrap/analysis4_separated_provenance_summary.csv` | Saved family-specific availability and intervals |
| eTable 9A-B: operating/action counts | `S/operating_counts.csv`, `observed_action_yield.csv` | Recalculated rates and yields; also supplies Table 3 |
| eTable 9C: operating uncertainty | `S/operating_uncertainty/operating_summary.csv`, `paired_FAE_difference.json` | Saved 1,000-resample intervals and paired loss-difference intervals |
| eTable 10: action definitions/windows | `S/action_definition_sensitivity/`; `S/reference_bootstrap/reference_summary.csv` (window rows) | Saved point references, component counts, curves and 500-resample intervals |
| eTable 11: transport/era | `S/era_and_transport/paper_transport_decomposition.csv`, `v7_cell56_temporal_drift.csv`, `v7_cell56_temporal_operating.csv` | Saved local estimates, matching rules and fixed-reference evaluation |
| eTable 12: subgroups | `S/subgroups/v7_subgroup_paper_summary_reconstructed.csv`, `subgroup_predictive_calibration_detail.csv` | Saved subgroup sensitivity ranges, discrimination and calibration |
| eTable 13A-B, D-E: other scores | `E/default/reference_point_anchors.csv`, `reference_bootstrap_summary.csv`, `fixed_reference_operating_points.csv`, `score_formula_definition.csv`, `score_component_implementation.csv` | Saved references, intervals and implementation; Figure 4 rates recalculated with the optional flag |
| eTable 13C: short-scale qSOFA | `E/qsofa_short_scale/reference_point_anchors.csv`, `fixed_reference_operating_points.csv` | Saved separate short-scale setting; defaults unchanged |
| eTable 14A-B: eight-scenario simulation | `simulations/eight_scenarios/` | Saved summaries and unchanged runner/configuration, seed 20260802 |
| eTable 14C: paired support simulation | `simulations/support_gate/condition_error_summary.csv` and its runner/configuration | Saved summaries, seed 2026101101 |
| eTable 15: conventional rules | `S/conventional_rules/comparator_operating_results_extended.csv`, `comparator_selection_bootstrap_summary.csv`, `comparator_contracts_extended.csv` | Saved rule thresholds, operating metrics and selection uncertainty |

| Supplement figure | Repository input | Reproduction scope |
|---|---|---|
| eFigure 1: loss and net benefit | `S/consequence_scenarios/comparator_development_selection_curve.csv`; `S/operating_counts.csv`; [R guidance](R_GUIDANCE.md) | Saved learning score-bin/confusion counts; fixed-pair loss is recalculated; the full learning-curve figure is not rendered by this entry point |
| eFigure 2: windows/components | `S/action_definition_sensitivity/`; `S/reference_bootstrap/reference_summary.csv`; `S/components/threshold_action_workload_matrix.csv` | Saved curves, intervals and component yields |
| eFigure 3: capacity/era | `S/era_and_transport/V7_13_K_operationalization_capacity.csv`, `v7_cell56_temporal_capacity.csv`, `v7_cell56_temporal_drift.csv` | Saved standardized capacity scenarios and era estimates |
| eFigure 4: subgroup sensitivity | `S/subgroups/v7_subgroup_paper_summary_reconstructed.csv` | Saved descriptive ranges |
| eFigure 5: other-score curves | `E/default/action_curves.csv`, `reference_point_anchors.csv`; corresponding files in `E/qsofa_short_scale/` | Saved curves and references; qSOFA short-scale rows remain separate |
| eFigure 6: output states | `S/reference_bootstrap/reference_point_anchors.csv`; `S/components/component_thresholds_point.csv`; `E/default/` and `E/qsofa_short_scale/` reference tables; `simulations/eight_scenarios/structural_abstention_summary.csv` | Saved state definitions and output summaries, not newly fitted curves |
| eFigure 7: fixed-pair loss | `S/operating_counts.csv`, `fixed_candidate_R_sensitivity.csv`, `operating_uncertainty/paired_FAE_difference.json` | Point loss components and R sensitivity recalculated; paired interval read from its saved summary |

The main Figure 2 uses `S/semantic_response_curve.csv` and the action-evaluation
JSON files; Figure 3 uses the same counts and paired interval as eFigure 7.
Figure 4 is checked by the optional aggregate command above. See
[figure sources](figures.md) for the distinction between numerical reproduction
and the exact manuscript artwork.

## Scope of the saved materials

The release supplies saved aggregates for each supplementary results section.
Some source tables also contain historical comparison columns, including loss
values at R = 15. Their READMEs identify those columns; they are not substituted
for the primary R = 11,299/804 results.

No patient-level cohorts, individual predictions or exact raw-EHR construction
pipeline are redistributed. The two final Python figure-rendering scripts and
the journal-layout R rendering sources were not present in the supplied local
materials and are not included. Numerical figure inputs are available as mapped
above; the exact final figure images are not regenerated by this entry point.

## Analyze authorized clinical inputs

```bash
python examples/sepsis_paper_analysis.py --mimic data/mimic-analysis.csv --stanford data/stanford-analysis.csv --verify-reported
```

The runner accepts prepared analysis tables described in the [data contract](paper-data.md).
It performs the specified split, reference learning, candidate comparison and
fixed-threshold evaluation. Raw-EHR cohort and variable construction precedes this
entry point; it does not rerun every analysis or uncertainty calculation in the
manuscript.

The existing simulation runners, configurations, seeds and saved condition-level
error summaries are in [simulations](https://github.com/Sheldon0106/ActionRef/tree/v1.0.3-jamia/simulations).
COPD, AERT/HEART, pneumonia and AKI materials are exploratory, not reported in
the manuscript. See the [material roles](evidence.md).
