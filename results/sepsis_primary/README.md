# Sepsis analysis results

These cohort-, score- and threshold-level summaries describe the clinical-only
Sepsis-3 analysis. MIMIC includes 314,658 derivation and 134,146 internal-validation
encounters; Stanford includes 118,385 encounters.

MIMIC ESRP references are 27/39/54. Revised threshold 34 was selected in the
derivation set at R = 11,299/804 under the Low-reference workload ceiling.
Stanford local estimates are 26/36/50; external evaluation retains the MIMIC
thresholds.

The top-level files provide cohort characteristics, action curves, reference
workload, operating counts and consequence comparisons. Subdirectories contain
score assessment, reference uncertainty, action-component and observation-window
analyses, conventional rules, subgroup results, and era/transport comparisons.

Operating metrics use the denominators specified in each file. Recorded-action
yield uses action-known flagged encounters; it is distinct from fitted action
probability at a reference. Derivation-set R-grid selection and fixed-pair
sensitivity are separate analyses.

See [study materials](../../docs/paper-reproduction.md) for calculation commands
and [data inputs](../../docs/data.md) for definitions.
