# Manuscript and exploratory materials

The manuscript examines emergency sepsis assessment. ESRP is the primary score;
NEWS2, MEWS, REMS and qSOFA are additional scores in the same setting. Public
materials contain aggregate summaries, analysis code and synthetic examples.
Clinical records require authorized source access.

## Cohorts and analysis roles

| Role | Cohort | Encounters | Use |
|---|---|---:|---|
| Derivation set | MIMIC, 70% patient split | 314,658 | Learn reference thresholds and select the revised threshold |
| Internal validation set | MIMIC, 30% patient split | 134,146 | Evaluate fixed references and revised threshold |
| External validation cohort | Stanford | 118,385 | Apply the MIMIC thresholds unchanged |
| Stanford local estimation | The same full Stanford cohort | 118,385 | Estimate local reference thresholds separately |

MIMIC reference thresholds are **27 / 39 / 54**; Stanford local estimates are
**26 / 36 / 50**. The revised threshold **34** was selected in the derivation set
with the Low-27 workload ceiling and **R = 11,299/804**. Local estimation does not
replace the fixed thresholds used in external validation.

The fixed ESRP study-tier boundaries **21 / 31 / 45** originate in the ESRP
derivation study by Jin et al. (manuscript reference 29). They correspond to the
sensitivity-target, Youden and specificity-target boundaries, fixed in that
study and applied unchanged here. Their original selection targets do not
prescribe the achieved performance in the ActionRef cohorts.

## Manuscript result map

`S/` = `results/sepsis_primary/`, `W/` = `results/early_warning_scores/`,
`X/` = `results/supplement_extended/`. A filename following a directory entry
uses that same directory. **P** = `examples/reproduce_paper.py`,
**E** = `examples/reproduce_extended.py`, **A** = `examples/sepsis_paper_analysis.py`.
P and E use public aggregates. A requires authorized prepared clinical inputs.
Saved summaries retain the original estimation and resampling results; the table
identifies scientific inputs and analysis code, not journal artwork generation.

| Display item | Content | Aggregate inputs or definitions | Analysis entry point and scope |
|---|---|---|---|
| Table 1 | Cohort characteristics | S/cohort_characteristics.csv | Saved descriptive table; E checks action denominators |
| Table 2 | Reference thresholds and uncertainty | S/reference_bootstrap/reference_summary.csv; reference_point_anchors.csv | A estimates references; saved bootstrap summaries |
| Table 3 | References, revised threshold and comparators | S/operating_counts.csv; observed_action_yield.csv; conventional_rules/rule_operating_rows.csv; conventional_rules/esrp_tier_boundaries.csv | P + E: counts to operating rates |
| Figure 1 | Framework | docs/references.md; docs/operating-candidates.md; configs/sepsis_primary.json | A: analysis workflow; conceptual illustration |
| Figure 2 | Action curve and probability evaluation | S/semantic_response_curve.csv; sepsis_action_reliability.json; sepsis_action_points.json | A: curve/evaluation; P: saved probability summaries |
| Figure 3 | Workload and consequences of threshold revision | S/learning_fae_curve.csv; operating_counts.csv; operating_uncertainty/paired_FAE_difference.json | E: derivation curve count checks; P: fixed comparison; saved paired interval |
| Figure 4 | Role of R | S/learning_R_selection.csv; learning_R_invariance.csv; fixed_candidate_R_sensitivity.csv | P: derivation-grid selections and fixed-pair sensitivity |
| Figure 5 | Alerts and sepsis sensitivity across four scores | W/default/fixed_reference_operating_points.csv; S/operating_counts.csv | P --early-warning-scores: fixed-reference rates |
| eTable 1 | Default settings | src/universal_cutoff/config.py | src/universal_cutoff/module2.py |
| eTable 2 | Triage-score implementations | W/default/score_formula_definition.csv; score_component_implementation.csv | Saved score definitions; A accepts supplied ESRP inputs |
| eTable 3 | Score and action-probability performance | S/score_assessment/; S/sepsis_action_points.json; S/sepsis_action_intervals.json; S/logistic_comparison/ | P: saved action estimates; A: score/action evaluation; saved intervals |
| eTable 4 | Action components and component references | S/components/ | A: primary composite construction; saved component analyses |
| eTable 5 | Reference uncertainty | S/reference_bootstrap/; S/action_definition_sensitivity/reference_bootstrap_summary.csv | src/universal_cutoff/bootstrap.py; saved resampling summaries |
| eTable 6 | Conventional rules | S/conventional_rules/rule_operating_rows.csv; esrp_tier_boundaries.csv; comparator_contracts_extended.csv; S/learning_fae_curve.csv | E: operating/count checks; saved selection contracts |
| eTable 7 | References and revised threshold 34 | S/operating_counts.csv; observed_action_yield.csv; learning_fae_curve.csv; operating_uncertainty/ | P + E: count-based rates; saved operating intervals |
| eTable 8 | Consequence scenario and R sensitivity | configs/sepsis_r_scenario.yaml; S/fixed_candidate_R_sensitivity.csv; docs/R_GUIDANCE.md | P: fixed-pair calculation; src/universal_cutoff/r_guidance.py |
| eTable 9 | Action definitions and windows | S/action_definition_sensitivity/ | src/universal_cutoff/module2.py; saved window-specific analyses |
| eTable 10 | Support criteria and targets | S/reference_sensitivity/ | src/universal_cutoff/module2.py; saved parameter sensitivity summaries |
| eTable 11 | External and era-based reference assessment | S/reference_bootstrap/; S/era_and_transport/v7_cell56_temporal_drift.csv; S/era_and_transport/v7_cell56_temporal_operating.csv | A: fixed transport and local estimation; saved era summaries |
| eTable 12 | Subgroup diagnostics | S/subgroups/; X/subgroup_diagnostics.csv | E: join saved subgroup operating/calibration results |
| eTable 13 | Early warning scores | W/default/; W/qsofa_short_scale/ | P --early-warning-scores; saved reference/short-scale summaries |
| eTable 14 | Paired support-criteria simulation | simulations/support_gate/condition_error_summary.csv; config.json | simulations/support_gate/runner.py (seed 2026101101); saved results |
| eFigure 1 | Weighted loss and net benefit | S/learning_fae_curve.csv; operating_counts.csv; fixed_candidate_R_sensitivity.csv | P + E: loss arithmetic; net benefit = TP/N - FP/(R*N) |
| eFigure 2 | Uniform windows and action components | S/action_definition_sensitivity/corrected_action_window_thresholds.csv; S/components/threshold_action_workload_matrix.csv | Saved window-specific references and component counts |
| eFigure 3 | Local references by MIMIC era | S/era_and_transport/v7_cell56_temporal_drift.csv | Saved era estimates; src/universal_cutoff/module2.py |
| eFigure 4 | Subgroup sensitivity ranges | S/subgroups/v7_subgroup_paper_summary_reconstructed.csv; X/subgroup_diagnostics.csv | E: saved subgroup operating values; sensitivity = TP/(TP+FN) |
| eFigure 5 | Early warning action curves and references | W/default/action_curves.csv; reference_point_anchors.csv; W/qsofa_short_scale/action_curves.csv; reference_point_anchors.csv | Saved curves/reference outputs; src/universal_cutoff/module2.py |

## Extended results

[Extended aggregate results](https://github.com/Sheldon0106/ActionRef/tree/main/results/supplement_extended)
provide minimax regret, transfer-target sensitivity, subgroup-level diagnostics,
the original eight-scenario simulation and conventional-rule selection
uncertainty. The sixth resource is the [K/R specification guide](R_GUIDANCE.md),
linked from supplement eMethods 2. The paired support-criteria simulation remains
in eTable 14; the original eight-scenario simulation is repository material.
The fixed release for these materials is
[v1.1.1](https://github.com/Sheldon0106/ActionRef/releases/tag/v1.1.1).

## Score definitions and output scope

MIMIC NEWS2, MEWS and REMS reference thresholds are **2/3/7**, **2/4/6** and
**3/11/12**. REMS High uses a relative target. Stanford local MEWS Mid is 3,
while external validation retains MIMIC Mid 4. Component definitions, including
omitted inputs and missing-value handling, are recorded in the implementation
files listed for eTable 2.

Default qSOFA has three valid bins, below the required eight, and returns no
references; reference bootstrapping is not run in that setting. The separate
short-scale analysis permits three bins. Low and Mid coincide at 1; the shared
threshold rule retains Mid 1 and High 2. Package defaults are unchanged.
Changepoint functionality remains available for exploratory use and was not used
in the manuscript.

## Compatibility of stored identifiers

Human-readable descriptions use the manuscript terminology. Existing API names,
configuration keys, paths, categorical join keys and saved schema fields are
retained for compatibility: `learning`/`development` identify derivation,
`heldout` identifies internal validation, and `Stanford`/`transport` identify
external validation when the MIMIC thresholds are applied. Stored local-reference
rows have a separate estimation role. Fields such as `anchors`, `anchor_family`,
`evidence_gate`, `candidate` and the `support_gate/` path are software identifiers;
they refer to reference thresholds, support criteria and threshold choices.
MIMIC's `anchor_year` is a source calendar-era variable. These identifiers do not
change the analysis or rename the revised threshold in the manuscript.
Historical exploratory reports retain their original analysis labels and settings.

## Exploratory materials

All materials below are **exploratory, not reported in the manuscript**.

| Material | Repository role |
|---|---|
| `results/copd/validation_v2_corrected/`, `configs/copd_corrected.json` | Corrected COPD action/reference summaries and supplied-score evaluations |
| `results/copd/validation_v1/` and `configs/copd_autoscore.yaml` | Earlier COPD action definition and compatibility records |
| `results/aert/`, `configs/aert.json`, AERT example scripts | HEART-derived AERT exploratory score, reference and action summaries |
| `results/aki/` and its configuration | AKI software-development and compatibility records |
| `results/pneumonia/` and its configuration | Pneumonia software-development and compatibility records |
| `results/cross_disease_validation_v1/` and its configuration | Historical combined development summaries, retained with their manifest hashes |
| Earlier compatibility, regression and R-tier reports | Development records under their stated settings |

The COPD action includes documented bronchodilator administration/start and the
**legacy Pyxis steroid-record proxy**. Its evaluation is conditional on the
supplied score. The [COPD partial-output example](output-states.md#real-data-partial-output-copd)
is retained as an exploratory illustration of the ordering rule.

## Historical score names

`AutoScore` in filenames and column names, such as `copd_autoscore.yaml` and
`score_COPD_AutoScore`, is a historical label. These exploratory scores were
constructed locally from binned predictors and logistic-regression weights;
they were not generated by the published R AutoScore workflow. File and column
names are retained to preserve the input data contract.

The supplied COPD column is the balanced-logistic score from `autoscore_copd.ipynb`.
The unweighted `_fixed` score was not stored in the input CSV. Historical
[compatibility](DISEASE_COMPATIBILITY_REPORT.md) and
[regression](CONTROLLED_REGRESSION_REPORT.md) records retain their original settings
and values. Public result metadata uses portable source placeholders rather than
local absolute paths. Patient records and identifiers are not distributed.
