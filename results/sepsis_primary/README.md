# Primary sepsis aggregate evidence

These bin-level, cohort-level and threshold-level summaries describe the
clinical-only Sepsis-3 analysis. The MIMIC ED 1.0 population contains 314,658
derivation and 134,146 internal validation encounters; Stanford contains 118,385 encounters.

MIMIC ESRP behavioral references are 27/39/54. The revised threshold 34 is selected in the derivation set
at at R = 11,299/804 under the 116,236-alert Low-reference ceiling. Stanford
local references are 26/36/50; transport evaluation uses the MIMIC references.

Run `python examples/reproduce_paper.py --early-warning-scores` from the repository
root to recalculate operating rates, action yields and fixed-pair R sensitivity.
Action-probability estimates and uncertainty intervals are read from saved
aggregates. Derivation R-grid selection is separate from the fixed 34-versus-27
comparison; its reported band endpoints are evaluated grid values.

## Cohort and integer-threshold summaries

`cohort_characteristics.csv` records the Table 1 display values and explicit
recorded-action denominators. Recorded-action prevalence uses action-known
encounters: 137,309/444,553 in MIMIC and 36,197/118,385 in Stanford. The MIMIC
partition counts are supplied separately.

`learning_fae_curve.csv` retains the existing filename convention for the
**derivation-set** curve. It contains 101 inclusive integer thresholds (0–100),
calculated from the saved per-score histogram. The exact ratio is 11,299/804;
threshold 34 has FAE 430.520257025 per 1,000. The additional rounded-ratio column
is a separate sensitivity. No interpolation or model refitting is involved.

The source run is `run_20261023T104445170533Z_5e79d9b15f84`; reporting extracts
come from its saved aggregate record. `examples/reproduce_extended.py` checks
these counts and the curve. See the [result map](../../docs/evidence.md#manuscript-result-map)
for current manuscript locations.

## Current files

- `cohort_characteristics.csv`
- `learning_fae_curve.csv`
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
