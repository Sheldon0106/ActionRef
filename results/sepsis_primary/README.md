# Sepsis analysis results

These cohort-, score- and threshold-level summaries describe the clinical-only
Sepsis-3 analysis. MIMIC includes 314,658 derivation and 134,146 internal-validation
encounters; Stanford includes 118,385 encounters.

MIMIC ESRP references are 27/39/54. Under the Low workload bound, the
resource-cost scenario selected threshold 34 (R = 11,299/804) and the central
mortality scenario selected 28 (R = 29.78, rounded) in the MIMIC derivation set.
External evaluation applied the MIMIC thresholds as selected. The separate
Stanford local estimates are 26/36/50.

The top-level files provide cohort characteristics, action curves, reference
workload, operating counts and consequence comparisons. Subdirectories contain
score assessment, reference uncertainty, action-component and observation-window
analyses, conventional rules, subgroup results, and era/transport comparisons.

Operating metrics use the denominators specified in each file. Recorded-action
yield uses action-known flagged encounters; it is distinct from fitted action
probability at a reference. Derivation-set R-grid selection and fixed-pair
sensitivity are separate analyses.

The [consequence scenarios](consequence_scenarios/README.md) include threshold
selection by workload bound, resampling results, and fixed evaluations. The
[operating comparisons](operating_uncertainty/README.md) include paired
differences and the added alerts and sepsis-positive encounters when lowering
a threshold. The [action-curve evaluation](logistic_comparison/README.md)
includes internal and external evaluations of the fixed MIMIC curve.

See [study materials](../../docs/paper-reproduction.md) for calculation commands
and [data inputs](../../docs/data.md) for definitions.
