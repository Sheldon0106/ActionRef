# Saved consequence-scenario summaries

The minimax summaries compare thresholds over a specified R grid separately
within each evaluation cohort. They describe cohort-specific secondary scenarios;
the primary operating candidate is selected on MIMIC learning data and then
applied unchanged to evaluation data.

The development selection curve provides aggregate confusion counts across
learning thresholds. The parent directory contains the corresponding learning
R-grid selections and the fixed 34-versus-27 evaluation comparison.

## Current files

- `paper_minimax_behavior_budget.csv`
- `comparator_development_selection_curve.csv`

Source labels, row selections and file checksums are recorded in
[manifest.json](manifest.json). All shared observations are aggregates; patient
records and identifiers are not included.
