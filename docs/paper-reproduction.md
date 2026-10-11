# Analysis and reproduction scope

The repository accompanies JAMIA submission manuscript **v10**. It provides
analysis scripts, configurations, synthetic examples and saved aggregate results.
Patient-level MIMIC-IV-ED, MIMIC-IV and MC-MED data must be obtained from
[PhysioNet](https://physionet.org/) under its credentialing and data-use requirements.
Patient records and identifiers are not redistributed.

## Use the public aggregate entry point

```bash
python -m pip install -e ".[test,research]"
python examples/reproduce_paper.py
```

This command recalculates sepsis operating rates, observed-action yields and the
fixed 31-versus-27 loss comparison from saved aggregate counts. Action-probability
point estimates and some uncertainty intervals are read from saved summaries;
this entry point does not re-estimate those intervals or rebuild the patient-level
cohorts. Outputs are written to ignored `output/paper/`.

## Analyze authorized clinical inputs

```bash
python examples/sepsis_paper_analysis.py --mimic data/mimic-analysis.csv --stanford data/stanford-analysis.csv --verify-reported
```

The runner accepts prepared analysis tables described in the [data contract](paper-data.md).
It performs the specified split, reference learning, candidate comparison and
fixed-threshold evaluation. Raw-EHR cohort and variable construction precedes this
entry point; it does not rerun every analysis or uncertainty calculation in the
manuscript.

The existing simulation runners, configurations, seeds and saved condition-level
error summaries are in [simulations](https://github.com/Sheldon0106/ActionRef/tree/v1.0.2-jamia/simulations).
COPD, AERT/HEART, pneumonia and AKI materials are exploratory, not reported in
the manuscript. See the [material roles](evidence.md).
