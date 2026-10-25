# ESRP outcome-score assessment

These tables assess ESRP discrimination and outcome-probability calibration
against the clinical-only Sepsis-3 outcome. The learning calibration map is fixed
before held-out and Stanford evaluation. Uncertainty summaries use 200 requested
patient-cluster resamples.

Outcome-risk assessment is separate from prediction of recorded actions, whose
saved estimates and intervals are in the parent result directory.

## Current files

- `paper_module1_point.csv`
- `paper_module1_bootstrap_ci.csv`

Source labels, row selections and file checksums are recorded in
[manifest.json](manifest.json). All shared observations are aggregates; patient
records and identifiers are not included.
