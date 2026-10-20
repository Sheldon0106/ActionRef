# Early warning scores: default settings

Manuscript locations: **Figure 4; eTables 6B and 13A, B, D, E; eFigure 5**.

NEWS is the manuscript display name. The original score key in these CSVs is retained for compatibility; the aggregate reader maps it to NEWS. Saved column names for recorded-action yield and sepsis sensitivity are also preserved. All operating rows apply MIMIC references unchanged. Stanford local reference estimates must not be substituted into those evaluations. Default qSOFA returns no references because the minimum supported-bin requirement is not met.

## Checks against the final manuscript

NEWS MIMIC references: 2 / 3 / 6. MEWS: 2 / 4 / 6. REMS: 3 / 11 / 13. Each reference bootstrap requests 500 replicates.

## Sources

Existing aggregate outputs only. No patient records or identifiers are included.
Numbers and original data fields are preserved. No analyses were rerun.

The [manifest](manifest.json) records portable source labels, generation-date provenance,
row selections, and SHA-256 hashes for the originals and public copies.

- [action_curves.csv](action_curves.csv)
- [cohort_denominators.csv](cohort_denominators.csv)
- [reference_point_anchors.csv](reference_point_anchors.csv)
- [reference_point_diagnostics.csv](reference_point_diagnostics.csv)
- [reference_bootstrap_summary.csv](reference_bootstrap_summary.csv)
- [reference_bootstrap_reasons.csv](reference_bootstrap_reasons.csv)
- [reference_pair_joint_stability.csv](reference_pair_joint_stability.csv)
- [fixed_reference_operating_points.csv](fixed_reference_operating_points.csv)
- [fixed_reference_operating_intervals.csv](fixed_reference_operating_intervals.csv)
- [score_formula_definition.csv](score_formula_definition.csv)
- [score_component_implementation.csv](score_component_implementation.csv)
- [score_component_missingness.csv](score_component_missingness.csv)
- [score_formula_regression.csv](score_formula_regression.csv)
- [primary_action_definition.csv](primary_action_definition.csv)
- [module1_current_points.csv](module1_current_points.csv)
- [module1_current_intervals.csv](module1_current_intervals.csv)
- [module1_frozen_calibration_maps.csv](module1_frozen_calibration_maps.csv)
