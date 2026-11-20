# Study materials

The repository provides the ActionRef implementation, sepsis analysis scripts,
configurations, simulation runners, and aggregate study results. The clinical
analysis uses ESRP, NEWS2, MEWS, REMS and qSOFA for emergency sepsis assessment.

## Data access

Patient-level MIMIC-IV-ED, MIMIC-IV and MC-MED data require credentialed access
through [PhysioNet](https://physionet.org/) and the applicable data-use agreements.
The [input guide](data.md#sepsis-study-inputs) describes the prepared analysis
variables, action definitions and patient split. The public repository contains
synthetic examples and aggregate results, without patient records or identifiers.

## Clinical analysis

```bash
python -m pip install -e ".[research]"
python examples/sepsis_paper_analysis.py --mimic data/mimic-analysis.csv --stanford data/stanford-analysis.csv
```

This entry point takes prepared analysis tables and performs reference estimation,
workload and consequence comparison, and fixed-threshold evaluation. Raw-record
extraction and construction of the input variables precede this entry point.

## Aggregate results

| Location | Contents |
|---|---|
| [Primary sepsis results](https://github.com/Sheldon0106/ActionRef/tree/main/results/sepsis_primary) | References, action curves, operating counts, and sensitivity analyses |
| [Consequence scenarios](https://github.com/Sheldon0106/ActionRef/tree/main/results/sepsis_primary/consequence_scenarios) | Workload bounds, threshold selection, and fixed evaluations under the resource and mortality scenarios |
| [Action-curve evaluation](https://github.com/Sheldon0106/ActionRef/tree/main/results/sepsis_primary/logistic_comparison) | Evaluation of the MIMIC action curves in internal validation and at Stanford |
| [Early warning scores](https://github.com/Sheldon0106/ActionRef/tree/main/results/early_warning_scores) | Score definitions, references and evaluation summaries |
| [Additional analyses](https://github.com/Sheldon0106/ActionRef/tree/main/results/supplement_extended) | Subgroup diagnostics, eight-scenario simulation, rule-selection uncertainty, minimax regret and transfer-target sensitivity |

The following commands calculate operating rates and weighted losses from shared
counts, and assemble the additional summaries:

```bash
python examples/reproduce_paper.py --early-warning-scores
python examples/reproduce_extended.py
```

The mortality comparisons, selection resampling, and Stanford action-curve
evaluation are available as saved aggregate results. The commands also reuse
saved estimates and intervals for some of their summaries. Numerical outputs
are written to the ignored `output/` directory.

## Simulations and scenario guidance

[Simulation materials](https://github.com/Sheldon0106/ActionRef/tree/main/simulations)
include the eight-scenario study (seed 20260802) and the paired support-criteria
study (seed 2026101101), with their configurations and condition-level summaries.
The [K/R guide](R_GUIDANCE.md) describes workflow-specific capacity inputs and
consequence elicitation.
