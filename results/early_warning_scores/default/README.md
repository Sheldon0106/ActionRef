# Adapted early warning scores: default settings

These materials apply ActionRef to adapted NEWS2, adapted MEWS, adapted REMS and
two-criterion qSOFA. MIMIC references are 2/3/7, 2/4/6 and 3/11/12 for the first
three scores, respectively. Adapted REMS High uses a relative probability target.
Each reference bootstrap for these three scores requests 500 resamples per site.

All fixed-reference operating rows use MIMIC thresholds unchanged at both sites.
Stanford local estimates describe local practice and are reported separately.
Default two-criterion qSOFA has three supported bins, below the eight-bin
requirement, so it returns no references and reference bootstrapping is not run.
The non-default short-scale analysis is stored in the sibling directory.

## Current files

- `action_curves.csv`
- `cohort_denominators.csv`
- `reference_point_anchors.csv`
- `reference_point_diagnostics.csv`
- `reference_bootstrap_summary.csv`
- `reference_bootstrap_reasons.csv`
- `reference_pair_joint_stability.csv`
- `fixed_reference_operating_points.csv`
- `fixed_reference_operating_intervals.csv`
- `score_formula_regression.csv`
- `module1_current_points.csv`
- `module1_current_intervals.csv`
- `module1_frozen_calibration_maps.csv`

## Retained historical files

These earlier values or definitions are retained for historical reference and are
not inputs to the current summaries.
- `score_formula_definition.csv`
- `score_component_implementation.csv`
- `score_component_missingness.csv`
- `primary_action_definition.csv`

Source labels, row selections and file checksums are recorded in
[manifest.json](manifest.json). All shared observations are aggregates; patient
records and identifiers are not included.

Completed resample counts and interval denominators are in
`reference_bootstrap_summary.csv`. The status in the point diagnostics describes
the planned bootstrap analysis.
