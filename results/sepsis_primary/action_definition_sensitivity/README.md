# Action-definition sensitivity

These summaries compare the primary action definition with expanded composites
and uniform 1-, 3- and 6-hour windows. Uniform-window analyses also use the
corresponding fluid definition, so differences reflect both the observation window
and component construction.

Each uniform-window reference analysis requests 500 patient-bootstrap resamples.
Candidate availability and independent retention are separate outputs. Window
operating and component-prevalence results are point estimates.

## Current files

- `sensitivity_response_bundle_thresholds.csv`
- `corrected_action_window_thresholds.csv`
- `corrected_action_window_response_curves.csv`
- `corrected_action_window_component_prevalence.csv`
- `corrected_action_window_evidence_gates.csv`
- `reference_bootstrap_summary.csv`

Source labels, row selections and file checksums are recorded in
[manifest.json](manifest.json). All shared observations are aggregates; patient
records and identifiers are not included.

Completed resample counts and interval denominators are in
`reference_bootstrap_summary.csv`. The status in the point diagnostics describes
the planned bootstrap analysis.
