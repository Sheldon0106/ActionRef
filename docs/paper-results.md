# Reported paper results

These tables summarize the primary sepsis analysis. Behavioral references
were learned from recorded actions. Candidate 31 was selected on MIMIC learning
data with Low 27 as the workload comparator and R = 11,299/804.

## Fixed operating results (Table 3)

Unflagged counts refer to outcome-positive encounters below the threshold.

**MIMIC held-out**

| Threshold | Alerts /1,000 | Action yield | Recall | Unflagged /1,000 | FAE /1,000 |
|---:|---:|---:|---:|---:|---:|
| 27 | 365.5 | 48.6% | 77.5% | 12.66 | 499.67 |
| 36 | 156.9 | 60.5% | 51.7% | 27.24 | 510.65 |
| 51 | 21.5 | 88.6% | 14.8% | 48.01 | 687.80 |
| 31 | 242.7 | 54.8% | 65.6% | 19.41 | 478.51 |

**Stanford transport**

| Threshold | Alerts /1,000 | Action yield | Recall | Unflagged /1,000 | FAE /1,000 |
|---:|---:|---:|---:|---:|---:|
| 27 | 355.7 | 49.2% | 81.5% | 8.24 | 435.40 |
| 36 | 127.0 | 66.4% | 51.7% | 21.48 | 405.93 |
| 51 | 19.1 | 89.8% | 15.7% | 37.49 | 538.96 |
| 31 | 216.5 | 57.3% | 68.1% | 14.17 | 385.34 |


Action yield uses flagged encounters with known action status. Recall uses
outcome-positive encounters. Per-1,000 rates use 127,528 MIMIC held-out or
118,385 Stanford encounters. FAE is
false-alarm-equivalent loss, FP + R × FN. It is a scenario-weighted count.

## Action-probability evaluation (eTable 36)

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

## Fixed 31-versus-27 comparison (eTable 37)

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

eTable 37 contains this fixed comparison only. Learning-data re-selection and
R-setting are described in Supplement eMethods 3 and the [R guide](R_GUIDANCE.md).

## COPD: additional main-text application (eTable 22)

COPD is evaluated conditional on the supplied score. Application definition,
references and operating results are documented in eTables 20–22.

| Level | Threshold | Encounters | Alerts /1,000 | Action yield | Outcome recall |
|---|---:|---:|---:|---:|---:|
| Low | 17.7798 | 134,175 | 191.0 | 14.9% | 83.9% |
| Mid | 55.0719 | 134,175 | 3.2 | 51.9% | 9.4% |

COPD action is documented bronchodilator administration/start within 24 hours
OR the legacy Pyxis steroid-record proxy. Its High reference is unavailable:
relative target 0.4278 reaches bin 50 below Mid bin 55, and ordering allows no
replacement. Reference uncertainty is in eTables 21 and 39; operating intervals
are in eTable 22 and the corrected source bundle.

### COPD evaluation excluding score-fitting patients (eTable 41)

The subset contains **13,978 patients / 15,221 encounters**, after excluding
every patient represented in score-fitting rows. AUROC is **0.894**
(95% patient-cluster interval, 0.864–0.921). The score, full-learning
references and historical preprocessing/rescaling remain fixed; this is a
supplemental evaluation conditional on the supplied score.

| Level | Threshold | Flagged / total | Outcome-positive flagged / total | Action yield |
|---|---:|---:|---:|---:|
| Low | 17.7798 | 1,369 / 15,221 | 55 / 91 | 12.1% |
| Mid | 55.0719 | 11 / 15,221 | 3 / 91 | 54.5% |

## AERT: supplementary exploratory example (eTables 33–34)

The ADMITTED/HOME setting H02 uses the previously inspected patient-disjoint
test partition. Other or missing dispositions are excluded.

| Level | Threshold | Encounters | Alerts /1,000 | Action yield | Outcome recall |
|---|---:|---:|---:|---:|---:|
| Mid | 3 | 756 | 449.7 | 61.5% | 81.5% |
| High | 6 | 756 | 46.3 | 82.9% | 15.7% |

In H02, Low and Mid coincide at score 3: their targets are 41.42% and 50%,
and fitted action probability is 30.92% at score 2 and 53.62% at score 3.
The shared-threshold rule retains Mid = 3 as the operational representative,
with High = 6 and no distinct Low operating point. Low is attainable and
shares Mid's threshold. The separate hospitalization-linkage setting retains
Low 3 in 785 test encounters. The unchanged eight-bin policy abstains in both
strict three-hour baseline settings; the reported references use the separate
short-discrete research extension described in eMethods 1–2.
eTables 32–34 and 38 and Supplementary Data 1–2 retain all 16 settings and
their conditional patient-bootstrap summaries. No K, R or FAE is applied to AERT.

See the [evidence guide](evidence.md) for the analysis roles and source-file
mapping. AKI and pneumonia remain development records and are not reported
in the paper.

## Reproduction

Run `python examples/reproduce_paper.py` from the repository root.
It recomputes operating rates, action yields and R sensitivity from shared counts.
The action-probability estimates and intervals are restored from the reported
aggregate outputs; recomputing them requires encounter-level action and score data.

Run `python examples/reproduce_additional.py` for corrected COPD tables and
`python examples/reproduce_aert.py` for the AERT aggregate replay, eTables
32–34 and 38 and Supplementary Data 1–2. Their saved bootstrap intervals are
assembled without reading patient records.
