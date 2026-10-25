# Two-criterion qSOFA: short-scale sensitivity

This separate sensitivity analysis lowers the minimum supported-bin requirement
to three; package defaults remain unchanged. It requests 500 patient-bootstrap
resamples at each site.

At both sites, the full-data Low and Mid candidates coincide at score 1. The
shared-threshold rule retains Mid 1 as their operating representative, together
with High 2. Low is not independently retained; its target is attainable. The
summary distinguishes candidate availability from independent retention and
absolute from relative probability targets.

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

Source labels, row selections and file checksums are recorded in
[manifest.json](manifest.json). All shared observations are aggregates; patient
records and identifiers are not included.

Completed resample counts and interval denominators are in
`reference_bootstrap_summary.csv`. The status in the point diagnostics describes
the planned bootstrap analysis.
