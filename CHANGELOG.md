# Changelog

## 1.1.0 - 2026-10-25

- Updated the sepsis aggregate evidence for the complete MIMIC ED cohort,
  patient-disjoint learning/evaluation split, clinical-only sepsis endpoint,
  and corrected supplied Stanford scores.
- Updated reference thresholds, fixed-candidate comparisons, saved uncertainty
  summaries and the corresponding analysis configurations and reproduction entry
  point. The primary ESRP references are 27/39/54 and the modeled candidate is 34.
- Refreshed the existing documentation illustrations and numerical examples from
  the current aggregate evidence.
- Algorithms, package defaults, synthetic examples, simulations and exploratory
  nonsepsis materials are unchanged. Clinical records are not distributed.
- Fixed release: `v1.1.0-jamia`.

## 1.0.4 - 2026-10-21

- Focused the figure guide on the available scientific inputs and the R sources
  for documentation illustrations.
- Clarified that the aggregate entry point recalculates operating rates and
  fixed-candidate loss comparisons and reads saved estimates and uncertainty
  intervals.
- Documentation and release metadata update. Algorithms, defaults, analysis
  scripts and reported numerical results are unchanged.
- Fixed release: `v1.0.4-jamia`.

## 1.0.3 - 2026-10-20

- Aligned the README and documentation with the final JAMIA submission,
  October 2026, including eTables 1-15 and eFigures 1-7.
- Added saved aggregate materials for NEWS, MEWS, REMS and two-criterion qSOFA,
  reference uncertainty, score assessment, logistic comparison, action components,
  action windows, era/transport, subgroups, conventional rules and simulations.
  Added the saved joint-reference and paired loss-difference intervals.
- Extended the aggregate entry point with optional Figure 4 rate checks,
  preserving score-specific denominators and unchanged MIMIC thresholds at Stanford.
- Standardized reader-facing terminology: recorded-action yield, sepsis sensitivity,
  estimated references and reporting only supported levels. Original data keys,
  API names and historical output stems remain unchanged.
- Clarified the logistic High crossing: the manuscript reports the first native
  score, 55; the saved supported-bin crossing is 57. Both original values are retained.
- Mapped the numerical figure inputs and the sources for documentation
  illustrations.
- Updated author citation metadata and copyright. No clinical analyses or
  simulations were rerun; algorithms, defaults, random seeds and reported
  numerical values are unchanged.
- Fixed release: `v1.0.3-jamia`.

## 1.0.2 - 2026-10-12

- Aligned documentation with the earlier JAMIA submission structure, focused on
  emergency sepsis assessment; COPD, AERT/HEART, pneumonia and AKI are retained
  as exploratory materials not reported in the manuscript.
- Removed obsolete supplementary-table mappings and clarified that the aggregate
  entry point reads saved uncertainty summaries rather than re-estimating them.
- Added the existing eight-scenario and paired support-gate simulation runners,
  configurations, seeds and saved condition-level error summaries. Only source
  and output path handling was adapted for the public repository; simulations
  were not rerun. Algorithms, defaults and reported numerical values are unchanged.
- Clarified that changepoint functionality was not used in the manuscript.
- Fixed release: `v1.0.2-jamia`.

## 1.0.1 - 2026-10-09

- Aligned evidence roles with the manuscript: COPD is the additional main-text
  application; AERT is a supplementary exploratory example.
- Replaced the removed Table 4 mappings and reproduction output names with
  the corresponding supplementary tables. Scientific values and historical
  result files are unchanged.
- Clarified H02's attainable, shared Low/Mid threshold at score 3 and the
  retained Mid operational representative.
- Updated release links and software citation metadata.

## 1.0.0 - 2026-10-09

- Aligned the paper-evidence route with primary sepsis ESRP and additional COPD
  and exploratory HEART-derived AERT applications. Retained AKI, pneumonia and
  combined historical results as development records with their original hashes.
- Added corrected COPD action/reference summaries, bootstrap summaries and
  supplemental score-fit-patient-excluded evaluation, with portable provenance.
- Added AERT aggregate results across all 16 settings, the short-discrete research
  policy, configurations and executable aggregate reproduction.
- Added the real-data COPD partial-output illustration and unified reference
  colors across the R figures.
- Added the five-step R-setting guide, distinguishing learning-data re-selection
  in Supplement eMethods 3 from the fixed comparison in eTable 37.
- Updated paper-table/source mappings and public-data checks for the new bundles.

## 0.1.0 - 2026-10-05

- Added the ActionRef overview, runnable synthetic learning/evaluation walkthrough,
  MkDocs tutorials, and reproducible workflow, synthetic, and aggregate clinical figures.
- Added package/documentation CI and a main-only Pages deployment workflow.
- Removed personal filesystem paths from public result metadata while retaining
  original and public-copy checksums. Scientific result values are unchanged.
- Added the optional, literature-anchored ratio recommender for analyses without a
  local cost study: three decision tiers, `explain_tiers()`, `recommend_ratio()`,
  `ratio_invariance()`, and `ratio_band_impact()`.
- Integrated the recommender with `ThresholdTableResult` and the existing Module 3B
  inclusive cost-tie rule; plain standardized confusion DataFrames are also accepted.
- Added discrete-grid invariance and recall/alert-fraction sensitivity reporting while
  preserving the Module 2 separation guard. Tier defaults are labeled low-confidence
  scenario values; capacity-only Module 3A remains a valid stopping point without R.
- Added `ElicitationFrame`. Action, target outcome, stakeholder perspective, and time horizon are required before any trade-off question; `build_r_guidance` raises if omitted.
- Neutral trade-off wording. No patient is described as benefiting and no action as unnecessary.
- Renamed `NaturalFrequencyChoice` fields to `additional_outcome_positive`, `additional_outcome_negative`, `accepted`.
- Unbracketed and inconsistent responses return `bracketing_status` of `one_sided_lower`, `one_sided_upper`, or `inconsistent` with `insufficient_basis` and a warning. No longer raises; produces no primary R.
- Added `RGuidanceResult.point_estimate_basis`, describing the primary value as the geometric midpoint of the elicited switch interval and stating it is not an estimate of the true R.
- Confidence forced to low when stakeholder elicitation determines the primary value.
- Added COPD and pneumonia compatibility configs, runner, aggregate summaries, and report.
- Added synthetic disease-agnostic contract tests, including a check that no core module contains a disease or source column name.
- Added primary sepsis aggregate source data, executable Table 3 and eTables 35–37
  reconstruction, and an analysis runner for authorized clinical tables.
- Added action-curve interpolation, held-out evaluation, paired patient-cluster
  intervals, and executable absolute, relative, partial and abstention examples.
- Aligned figure colors with the paper and supplied editable SVG, PDF and 300-dpi PNG
  exports generated in R.
- 88 software tests.

## 0.1.0rc1 - 2026-08-20

- Installable Python 3.8-compatible package structure and public API.
- V7 evidence-gated, semantic-first Module 2 with explicit abstention.
- Shared threshold-table engine and absolute-K Module 3A.
- Disease-agnostic Module 3B: objective, inclusive cost tie rule, same-or-lower-workload audit, unconstrained comparator, binding classification, near-optimal regions.
- Lambda semantics: nonbinding is calculated zero; missing or invalid calibrator is unavailable with a reason.
- Typed R-guidance schemas, provenance, confidence, scenario grids, safeguards.
- Optional Module 2 bootstrap, disabled by default, recording replicate failures and joint-tier invariants, adjacent-gap intervals, provenance frequencies, binning stability, deterministic replay, validated changepoint-support gating.
- Frozen-threshold subgroup, temporal, and transport diagnostics with role, overlap, and interpretation guards.
- Synthetic contracts and controlled MIMIC/Stanford V7 regression script and report.
- 37 tests verified on the Python 3.8.20 reference stack; wheel and source distributions built.
