# Sepsis aggregate results

These tables summarize the primary sepsis analysis. Behavioral references
were estimated from recorded actions. Candidate 31 was selected on MIMIC learning
data with Low 27 as the workload comparator and R = 11,299/804.

## Fixed operating results (Table 3)

Unflagged counts refer to outcome-positive encounters below the threshold.

**MIMIC held-out**

| Threshold | Alerts /1,000 | Recorded-action yield | Sepsis sensitivity | Unflagged /1,000 | FAE /1,000 |
|---:|---:|---:|---:|---:|---:|
| 27 | 365.5 | 48.6% | 77.5% | 12.66 | 499.67 |
| 36 | 156.9 | 60.5% | 51.7% | 27.24 | 510.65 |
| 51 | 21.5 | 88.6% | 14.8% | 48.01 | 687.80 |
| 31 | 242.7 | 54.8% | 65.6% | 19.41 | 478.51 |

**Stanford transport**

| Threshold | Alerts /1,000 | Recorded-action yield | Sepsis sensitivity | Unflagged /1,000 | FAE /1,000 |
|---:|---:|---:|---:|---:|---:|
| 27 | 355.7 | 49.2% | 81.5% | 8.24 | 435.40 |
| 36 | 127.0 | 66.4% | 51.7% | 21.48 | 405.93 |
| 51 | 19.1 | 89.8% | 15.7% | 37.49 | 538.96 |
| 31 | 216.5 | 57.3% | 68.1% | 14.17 | 385.34 |


Recorded-action yield uses flagged encounters with known action status. Sepsis sensitivity uses
outcome-positive encounters. Per-1,000 rates use 127,528 MIMIC held-out or
118,385 Stanford encounters. FAE is
false-alarm-equivalent loss, FP + R × FN. It is a scenario-weighted count.

## Action-probability evaluation (eTable 6C)

Evaluation uses 126,332 encounters from 60,903 patients. The learning curve and
constant learning-rate comparator are held fixed. Intervals use 200 patient-cluster
resamples and quantify evaluation uncertainty conditional on those predictions.

| Metric | Continuous interpolation | 95% interval | Bin-assignment sensitivity |
|---|---:|---|---:|
| Observed action rate | 0.32453 | 0.32059 to 0.32873 | 0.32453 |
| Mean prediction | 0.33370 | 0.33142 to 0.33637 | 0.32445 |
| Predicted minus observed | 0.00918 | 0.00538 to 0.01369 | -0.00008 |
| Brier score | 0.19433 | 0.19299 to 0.19563 | 0.19454 |
| Constant-rate Brier score | 0.21921 | 0.21785 to 0.22067 | 0.21921 |
| Paired Brier difference | -0.02489 | -0.02644 to -0.02340 | -0.02468 |
| Brier skill | 0.11353 | 0.10696 to 0.11988 | 0.11257 |
| Log loss | 0.57323 | Not estimated | 0.57371 |
| Calibration intercept | -0.08610 | Not estimated | -0.01827 |
| Calibration slope | 0.94066 | Not estimated | 0.97332 |

Calibration intercept and slope are descriptive fits to fixed predictions.
The bin-assignment sensitivity is reported as a point estimate.

## Fixed 31-versus-27 comparison (eTable 5B)

| R | MIMIC ΔFAE /1,000 | Stanford ΔFAE /1,000 |
|---:|---:|---:|
| 5 | -82.28 | -103.67 |
| 10 | -48.52 | -74.06 |
| 14.053 | -21.16 | -50.06 |
| 15 | -14.77 | -44.46 |
| 20 | 18.99 | -14.85 |
| 25 | 52.75 | 14.76 |
| 30 | 86.51 | 44.36 |

ΔFAE = L(31) − L(27). Negative values favor 31 within this fixed pair.
Equality occurs at R = 17.18699 in MIMIC and 22.50785 in Stanford.
Candidates are not reselected on evaluation data. These crossings describe
this pair, not an optimum over all possible thresholds.

This is a fixed-pair comparison. Learning-data re-selection and
R-setting are described in Supplement eMethods 3 and the [R guide](R_GUIDANCE.md).

## Four-score comparison (Figure 4; eTable 13E)

MIMIC references are applied unchanged at both sites. Stanford local
reference estimates describe local practice and are not used in these rows.

| Cohort | Score | Level | Threshold | Encounters | Alerts /1,000 | Sepsis sensitivity |
|---|---|---|---:|---:|---:|---:|
| MIMIC held-out | ESRP | Low | 27 | 127,528 | 365.5 | 77.5% |
| MIMIC held-out | ESRP | Mid | 36 | 127,528 | 156.9 | 51.7% |
| MIMIC held-out | ESRP | High | 51 | 127,528 | 21.5 | 14.8% |
| Stanford transport | ESRP | Low | 27 | 118,385 | 355.7 | 81.5% |
| Stanford transport | ESRP | Mid | 36 | 118,385 | 127.0 | 51.7% |
| Stanford transport | ESRP | High | 51 | 118,385 | 19.1 | 15.7% |
| MIMIC held-out | NEWS | Low | 2 | 127,533 | 187.6 | 39.9% |
| MIMIC held-out | NEWS | Mid | 3 | 127,533 | 78.3 | 25.2% |
| MIMIC held-out | NEWS | High | 6 | 127,533 | 4.9 | 3.3% |
| MIMIC held-out | MEWS | Low | 2 | 127,533 | 236.2 | 43.5% |
| MIMIC held-out | MEWS | Mid | 4 | 127,533 | 32.2 | 11.9% |
| MIMIC held-out | MEWS | High | 6 | 127,533 | 3.0 | 1.7% |
| MIMIC held-out | REMS | Low | 3 | 127,533 | 570.3 | 85.3% |
| MIMIC held-out | REMS | Mid | 11 | 127,533 | 3.8 | 1.3% |
| MIMIC held-out | REMS | High | 13 | 127,533 | 0.2 | 0.2% |
| Stanford transport | NEWS | Low | 2 | 118,385 | 227.3 | 58.6% |
| Stanford transport | NEWS | Mid | 3 | 118,385 | 115.8 | 41.2% |
| Stanford transport | NEWS | High | 6 | 118,385 | 10.8 | 8.3% |
| Stanford transport | MEWS | Low | 2 | 118,385 | 288.8 | 61.4% |
| Stanford transport | MEWS | Mid | 4 | 118,385 | 54.2 | 22.4% |
| Stanford transport | MEWS | High | 6 | 118,385 | 6.1 | 4.9% |
| Stanford transport | REMS | Low | 3 | 118,385 | 579.7 | 84.7% |
| Stanford transport | REMS | Mid | 11 | 118,385 | 7.0 | 3.7% |
| Stanford transport | REMS | High | 13 | 118,385 | 1.1 | 1.1% |

The MIMIC denominator is 127,528 for ESRP and 127,533 for the other
scores; Stanford uses 118,385. Alerts and sensitivity are recalculated
from TP, FP, FN and TN and checked against the saved comparator rates.
Default qSOFA returns no references and is omitted from Figure 4.


## Reproduction

Run `python examples/reproduce_paper.py --early-warning-scores` from the repository root.
It recomputes operating rates, action yields and R sensitivity from shared counts.
The action-probability estimates and intervals are restored from the reported
aggregate outputs; recomputing them requires encounter-level action and score data.

This aggregate entry point does not rebuild patient-level cohorts or
re-estimate every manuscript result. See the [reproduction scope](paper-reproduction.md).
COPD, AERT/HEART, pneumonia and AKI materials are exploratory, not reported
in the manuscript; their separate example scripts are retained.
