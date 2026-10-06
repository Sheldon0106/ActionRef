# Primary sepsis aggregate evidence

Source data for the primary sepsis analysis include bin-level summaries and
cohort/threshold-level counts. All shared observations are aggregates.

| File | Role |
|---|---|
| `operating_counts.csv` | Exact TP/FP/FN/TN counts reported in Supplement eTable 4 |
| `observed_action_yield.csv` | Flagged, action-known and action-positive counts for eTable 35 |
| `semantic_response_curve.csv` | Supported learning bins, observed rates and isotonic fit |
| `sepsis_action_points.json` | Continuous-interpolation and bin-assignment evaluation estimates |
| `sepsis_action_intervals.json` | Conditional evaluation intervals from 200 patient-cluster resamples |
| `sepsis_action_reliability.json` | Fixed-width probability-bin counts and rates |
| `fixed_candidate_R_sensitivity.csv` | Reported fixed-pair sensitivity for comparison with recalculated values |
| `manifest.json` | Source labels and file checksums |

From the repository root, run `python examples/reproduce_paper.py`. It derives
Table 3 and eTables 35–37 under `output/paper/`. Point estimates and intervals
for action probabilities are assembled from saved outputs; their encounter-level
recalculation has a [separate entry point](../../docs/paper-reproduction.md).

The configuration is [sepsis_primary.json](../../configs/sepsis_primary.json).
The action definition, workload comparator and evaluation denominators retain
their reported meanings. Candidate 31 remains a separate operating choice from
the behavioral reference Low 27.
