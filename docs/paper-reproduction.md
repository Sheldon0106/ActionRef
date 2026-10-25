# Analysis and reproduction scope

The repository provides analysis scripts, configurations, synthetic examples and
saved aggregate results for the ActionRef sepsis analysis. Patient-level MIMIC-IV-ED,
MIMIC-IV and MC-MED data must be obtained from [PhysioNet](https://physionet.org/)
under its credentialing and data-use requirements. Patient records and identifiers
are not redistributed.

## Use the public aggregate entry point

```bash
python -m pip install -e ".[test,research]"
python examples/reproduce_paper.py
python examples/reproduce_paper.py --early-warning-scores
```

This command recalculates sepsis operating rates, recorded-action yields and the
fixed 34-versus-27 loss comparison from saved aggregate counts. Action-probability
point estimates and some uncertainty intervals are read from saved summaries;
this entry point does not re-estimate those intervals or rebuild the patient-level
cohorts. Outputs are written to ignored `output/paper/`.

The optional flag adds ESRP, adapted NEWS2, adapted MEWS and adapted REMS at the
fixed MIMIC references in both evaluation cohorts. It checks recalculated alert
rates and sepsis sensitivity against saved rates. All four scores use **134,146**
MIMIC held-out encounters and **118,385** Stanford encounters. Recorded-action
yield excludes flagged encounters with missing action labels from its denominator.
The [data contract](paper-data.md) specifies the clinical-only outcome and partitions.

## Saved analysis materials

| Location | Contents |
|---|---|
| `results/sepsis_primary/` | Primary ESRP action curves, reference summaries, operating counts, action-probability evaluation, consequence comparisons and supplementary analysis summaries |
| `results/early_warning_scores/` | Adapted-score definitions, curves, references and fixed-reference evaluation; the separate short-scale qSOFA setting is identified explicitly |
| `simulations/` | Eight-scenario and paired support-gate runners, configurations, seeds and saved condition-level error summaries |

The [aggregate results](paper-results.md) distinguish count-based calculations
from previously estimated curves and intervals. Reference-relearning intervals,
fixed-policy operating intervals and action-probability intervals represent
separate resampling analyses. They are supplied as saved results rather than
re-estimated by the aggregate entry point. Documentation illustration inputs and
build instructions are described in the [figure guide](figures.md).

## Analyze authorized clinical inputs

```bash
python examples/sepsis_paper_analysis.py --mimic data/mimic-analysis.csv --stanford data/stanford-analysis.csv --verify-reported
```

The runner accepts prepared analysis tables described in the [data contract](paper-data.md).
It performs the specified patient-disjoint split, reference learning, candidate
comparison and fixed-threshold evaluation. Raw-EHR cohort and variable construction
precedes this entry point; it does not rerun every analysis or uncertainty
calculation in the manuscript.

The current MIMIC population, patient assignment and clinical-only outcome differ
from historical releases. Historical results remain available through Git history
and release tags; they should not be combined with current point estimates or
intervals. COPD, AERT/HEART, pneumonia and AKI materials are exploratory, not
reported in the manuscript. See the [material roles](evidence.md).
