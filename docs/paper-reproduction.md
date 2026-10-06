# Reproduce the paper results

Reproduce the primary sepsis results from shared aggregate data, or run the
analysis on authorized encounter-level tables. The two entry points below cover
their respective inputs and outputs.

## Start with the aggregate results

From a repository checkout with the package installed:

```bash
python examples/reproduce_paper.py
```

The command checks the source manifest and writes five CSV tables plus a readable
report to `output/paper/`. It needs no clinical database. The
[results page](paper-results.md) presents the same tables.

| Paper item | Source | What the command does |
|---|---|---|
| Table 3 | Confusion counts from eTable 4; action counts from eTable 35 | Recalculates alerts, recall, unflagged outcomes, action yield and FAE |
| eTable 35 | `observed_action_yield.csv` | Recalculates yields from action-positive and action-known counts |
| eTable 36 | `sepsis_action_points.json`; `sepsis_action_intervals.json` | Assembles reported point estimates, intervals and bin-assignment sensitivity |
| eTable 37 | eTable 4 confusion counts; exact R grid | Recalculates the fixed 31-versus-27 loss differences and crossing points |
| Figure 2 numerical evidence | Learning curve and held-out reliability bins | Supplies the inputs to the R illustration below |

The canonical input files and their provenance are in `results/sepsis_primary/`.
The protocol is `configs/sepsis_primary.json`. Figure 1 is a conceptual workflow;
the website diagram explains the same sequence for software users. Table 1 cohort
construction, Table 2 reference-relearning intervals, and the complete Supplement
require their corresponding source analyses and are not rebuilt by this command.
Secondary disease analyses have [separate runners](evidence.md).

### Redraw the illustrations in R

```r
install.packages(c("jsonlite", "svglite", "ragg"))
```

```bash
Rscript scripts/build_figures.R --preview
```

This draws the website's workflow, synthetic example and clinical action panels
as editable SVG, PDF and 300-dpi PNG files. The clinical panel uses the same
learning curve and reliability inputs as the paper. Its layout is designed for
the website; see the [figure guide](figures.md) for sources and interpretation.

## Recalculate with authorized analysis data

Prepare the columns described in the [paper data contract](paper-data.md). These
are derived analysis tables; raw database downloads need the preceding cohort,
score, action and outcome construction steps.

```bash
python examples/sepsis_paper_analysis.py --mimic data/mimic-analysis.csv --stanford data/stanford-analysis.csv --verify-reported
```

Omit `--stanford` to run MIMIC alone. The runner:

1. Splits all MIMIC source rows by patient, before score/action complete-case filtering.
2. Learns the behavioral references on the learning partition.
3. Explicitly uses **Low** as the workload comparator and **R = 11,299/804** to select a candidate on learning data.
4. Applies the references and candidate unchanged to evaluation data.
5. Evaluates the learned action curve with linear interpolation and endpoint clipping; computes paired patient-cluster intervals using 200 resamples.
6. Reports the original width-3 bin-assignment sensitivity and fixed-candidate R sensitivity.

Stanford evaluation transports the MIMIC thresholds. Stanford local reference
learning is saved separately. This runner does not estimate Stanford action-curve
calibration or repeat the reference-relearning bootstrap for Table 2.

`--verify-reported` checks cohort sizes, references, the candidate, learning workload,
curve coordinates, operating counts, action-probability metrics and bootstrap
intervals against the reported aggregate results. A mismatch stops execution before
results are written. Without this option, the same workflow can be examined on
another prepared cohort; its outputs are not a reproduction of the reported values.

Only aggregate outputs are written, under `output/sepsis-analysis/`. No patient
identifiers or individual predictions are exported. Reproducing the reported
clinical analysis requires the specified authorized tables and successful
`--verify-reported` checks.

## Keep the learning choices explicit

The paper recipe calls `audit_cost_governance(learning_table, low, R)` directly.
The convenience path `run_framework(..., cost=...)` uses a Mid-first representative
when available, so it is not the command for this particular Low-based comparison.

K is the learning sample's alert count at Low, **109,888**, in this example.
It is a comparison ceiling, not measured service capacity. R concerns a proposed
diagnostic and short-course antibiotic workflow; the observed action composite
has a different definition.

The operating denominator is 127,528 MIMIC held-out encounters. Action-probability
evaluation additionally requires a known action and uses 126,332 encounters.
Action yield uses only flagged encounters with known action status. The scripts
retain these separate denominators.
