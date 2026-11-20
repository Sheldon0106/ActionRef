# Action-curve evaluation

These summaries compare a logistic action-probability curve with the primary
isotonic curve, using the same recorded-action question. The saved paired Brier
interval evaluates their fixed predictions on internal validation encounters.

Logistic targets are first reached at native integer scores 27/38/58. Their first
supported bins are 27/39/60; continuous crossings are also supplied. These are
different score representations. The primary isotonic references remain 27/39/54.

For the Stanford evaluation, both MIMIC derivation-set curves were applied
unchanged to 118,385 encounters from 70,545 patients. The isotonic predictions
use interpolation, with 21 encounters outside the supported range assigned
the corresponding endpoint probability. The saved intervals use 1,000
patient resamples. The constant comparator uses the MIMIC derivation action
rate.

## Files

- `analysis3_curve_comparison.csv`
- `analysis3_logistic_crossings.csv`
- `analysis3_paired_Brier_interval.csv`
- `analysis3_probability_curves.csv`
- `analysis3_reliability_bins.csv`
- [Stanford point estimates](stanford_action_calibration_points.csv)
- [Stanford isotonic intervals](stanford_action_calibration_intervals.csv)
- [Stanford paired Brier comparison](stanford_action_paired_Brier.csv)
- [Stanford reliability by probability bin](stanford_action_reliability.csv)
