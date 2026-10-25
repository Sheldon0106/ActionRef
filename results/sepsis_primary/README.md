# Primary sepsis aggregate evidence

These bin-level, cohort-level and threshold-level summaries describe the
clinical-only Sepsis-3 analysis. The MIMIC ED 1.0 population contains 314,658
learning and 134,146 held-out encounters; Stanford contains 118,385 encounters.

MIMIC ESRP behavioral references are 27/39/54. Candidate 34 is selected on learning
data at R = 11,299/804 under the 116,236-alert Low-reference ceiling. Stanford
local references are 26/36/50; transport evaluation uses the MIMIC references.

Run `python examples/reproduce_paper.py --early-warning-scores` from the repository
root to recalculate operating rates, action yields and fixed-pair R sensitivity.
Action-probability estimates and uncertainty intervals are read from saved
aggregates. Learning R-grid selection is separate from the fixed 34-versus-27
comparison; its reported band endpoints are evaluated grid values.

## Current files

- `observed_action_yield.csv`
- `fixed_candidate_R_sensitivity.csv`
- `sepsis_action_points.json`
- `sepsis_action_intervals.json`
- `sepsis_action_reliability.json`
- `semantic_response_curve.csv`
- `operating_counts.csv`
- `learning_R_selection.csv`
- `learning_R_invariance.csv`

Source labels, row selections and file checksums are recorded in
[manifest.json](manifest.json). All shared observations are aggregates; patient
records and identifiers are not included.
