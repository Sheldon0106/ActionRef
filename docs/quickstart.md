# A complete synthetic walkthrough

This example demonstrates the software using **synthetic data**. No patient data,
clinical estimates, or disease-specific parameters are needed.

```bash
python examples/synthetic_walkthrough.py --output-dir output/synthetic
```

The script creates 12,000 rows, each representing a different synthetic person,
with a score from 0 to 100, a binary recorded-action label, and a separate binary
outcome. A fixed split assigns 8,400 rows to learning and 3,600 to evaluation.

## 1. Learn from the score–action relationship

The learning call is:

```python
behavior = fit_behavior_thresholds(learning, "score", "response")
```

The resulting references are Low = 45, Mid = 45, and High = 60. The two references
at 45 share an operating threshold but retain distinct probability targets. The
output identifies the unique operating representatives; it does not manufacture
three distinct score values.

## 2. Apply a declared alert budget

```python
learning_table = build_threshold_table(learning, "score", "response", "outcome")
capacity = apply_capacity(
    learning_table, behavior.anchors,
    CapacityConfig(K=1680, period="8,400 synthetic learning encounters"),
)
```

Here, 1,680 alerts means 20% of the learning cohort. All available references map
to an operating candidate of 81, while the original references remain 45 / 45 / 60.
`K` counts flagged encounters, not observed actions, staff hours, or admissions.

## 3. Evaluate the same thresholds on separate data

The script passes the learned reference values and the candidate of 81 to
`evaluate_frozen_thresholds`. No reference is learned from the evaluation rows.

| Fixed threshold | Alerts / 1,000 | Recorded-action yield | Outcome recall |
|---|---:|---:|---:|
| Low and Mid: 45 | 555.3 | 88.3% | 90.4% |
| High: 60 | 407.5 | 94.1% | 79.2% |
| Capacity candidate: 81 | 194.4 | 96.4% | 44.3% |

These are synthetic example outputs. The candidate reduces alert burden and
outcome coverage. Its held-out alert fraction is measured anew; a learning-cohort
budget does not guarantee the same count in another cohort or time period.

![Synthetic action curve and held-out operating results.](assets/figures/synthetic-example.png)

## 4. Read the saved files

| File | What to inspect |
|---|---|
| `references.csv` | Targets, selected thresholds, absolute/relative provenance, unavailable outputs |
| `learning_curve.csv` | Binned observed rates, counts, and the weighted isotonic fit |
| `capacity.csv` | Original reference, capacity floor, adjusted operating threshold |
| `heldout.csv` | Alert burden, action yield, and outcome metrics at fixed thresholds |
| `summary.json` | Seeds, sample sizes, full Module 2 configuration, evidence support |

For your own data, first read the [data contract](data.md), then the
[reference interpretation guide](references.md). Partial outputs and abstention
are valid results, even though this synthetic example has three available labels.
