# Sepsis aggregate results

These tables summarize the primary sepsis analysis. Behavioral references
were estimated from recorded actions. The revised threshold 34 was selected on the MIMIC derivation set
with Low 27 as the workload comparator and R = 11,299/804.

## Table 3 and eTable 7: reference and revised thresholds

Unflagged counts refer to outcome-positive encounters below the threshold.

**MIMIC internal validation set**

| Threshold | Alerts /1,000 | Recorded-action yield | Sepsis sensitivity | Unflagged /1,000 | FAE /1,000 |
|---:|---:|---:|---:|---:|---:|
| 27 | 363.4 | 46.5% | 74.1% | 10.06 | 476.12 |
| 34 | 189.0 | 55.6% | 53.4% | 18.08 | 422.31 |
| 39 | 115.0 | 61.6% | 40.0% | 23.30 | 426.83 |
| 54 | 16.6 | 84.0% | 11.4% | 34.40 | 495.53 |

**Stanford external validation cohort**

| Threshold | Alerts /1,000 | Recorded-action yield | Sepsis sensitivity | Unflagged /1,000 | FAE /1,000 |
|---:|---:|---:|---:|---:|---:|
| 27 | 360.6 | 48.9% | 81.8% | 5.87 | 416.79 |
| 34 | 162.4 | 61.7% | 59.2% | 13.14 | 327.96 |
| 39 | 92.7 | 70.4% | 43.9% | 18.06 | 332.37 |
| 54 | 12.8 | 92.4% | 11.7% | 28.42 | 408.43 |


Recorded-action yield uses flagged encounters with known action status. Sepsis sensitivity uses
outcome-positive encounters. Per-1,000 rates use 134,146 MIMIC internal validation or
118,385 Stanford encounters. FAE is
false-alarm-equivalent loss, FP + R × FN. It is a scenario-weighted count.

## eTable 3: action-probability evaluation

Evaluation uses 132,878 encounters from 64,278 patients. The derivation curve and
constant derivation-rate comparator are held fixed. Intervals use 200 patient-cluster
resamples and quantify evaluation uncertainty conditional on those predictions.

| Metric | Continuous interpolation | 95% interval | Bin-assignment sensitivity |
|---|---:|---|---:|
| Observed action rate | 0.30776 | 0.30364 to 0.31266 | 0.30776 |
| Mean prediction | 0.31748 | 0.31516 to 0.31951 | 0.30871 |
| Predicted minus observed | 0.00973 | 0.00619 to 0.01364 | 0.00095 |
| Brier score | 0.19000 | 0.18875 to 0.19127 | 0.19023 |
| Constant-rate Brier score | 0.21304 | 0.21148 to 0.21491 | 0.21304 |
| Paired Brier difference | -0.02304 | -0.02427 to -0.02170 | -0.02281 |
| Brier skill | 0.10816 | 0.10231 to 0.11372 | 0.10707 |
| Log loss | 0.56366 | Not estimated | 0.56420 |
| Calibration intercept | -0.09085 | Not estimated | -0.02518 |
| Calibration slope | 0.94479 | Not estimated | 0.97361 |

Calibration intercept and slope are descriptive fits to fixed predictions.
The bin-assignment sensitivity is reported as a point estimate.

## eTable 8: fixed 34-versus-27 comparison

| R | MIMIC ΔFAE /1,000 | Stanford ΔFAE /1,000 |
|---:|---:|---:|
| 5 | -126.37 | -154.61 |
| 10 | -86.30 | -118.28 |
| 14.053 | -53.82 | -88.84 |
| 15 | -46.23 | -81.96 |
| 20 | -6.16 | -45.64 |
| 25 | 33.90 | -9.32 |
| 30 | 73.97 | 27.01 |

ΔFAE = L(34) − L(27). Negative values favor 34 within this fixed pair.
Equality occurs at R = 20.76930 in MIMIC and 26.28256 in Stanford.
Candidates are not reselected on evaluation data. These crossings describe
this pair, not an optimum over all possible thresholds.

This is a fixed-pair comparison. Derivation-data re-selection and
R-setting are described in the Supplementary methods and the [R guide](R_GUIDANCE.md).

## Figure 5: four-score comparison

MIMIC references are applied unchanged at both sites. Stanford local
reference estimates describe local practice and are not used in these rows.

| Cohort | Score | Level | Threshold | Encounters | Alerts /1,000 | Sepsis sensitivity |
|---|---|---|---:|---:|---:|---:|
| MIMIC internal validation set | ESRP | Low | 27 | 134,146 | 363.4 | 74.1% |
| MIMIC internal validation set | ESRP | Mid | 39 | 134,146 | 115.0 | 40.0% |
| MIMIC internal validation set | ESRP | High | 54 | 134,146 | 16.6 | 11.4% |
| Stanford external validation cohort | ESRP | Low | 27 | 118,385 | 360.6 | 81.8% |
| Stanford external validation cohort | ESRP | Mid | 39 | 118,385 | 92.7 | 43.9% |
| Stanford external validation cohort | ESRP | High | 54 | 118,385 | 12.8 | 11.7% |
| MIMIC internal validation set | NEWS2 | Low | 2 | 134,146 | 187.5 | 42.9% |
| MIMIC internal validation set | NEWS2 | Mid | 3 | 134,146 | 78.3 | 26.9% |
| MIMIC internal validation set | NEWS2 | High | 7 | 134,146 | 1.7 | 1.6% |
| MIMIC internal validation set | MEWS | Low | 2 | 134,146 | 236.0 | 45.1% |
| MIMIC internal validation set | MEWS | Mid | 4 | 134,146 | 32.3 | 13.2% |
| MIMIC internal validation set | MEWS | High | 6 | 134,146 | 3.3 | 2.3% |
| MIMIC internal validation set | REMS | Low | 3 | 134,146 | 569.6 | 84.1% |
| MIMIC internal validation set | REMS | Mid | 11 | 134,146 | 4.2 | 1.4% |
| MIMIC internal validation set | REMS | High | 12 | 134,146 | 1.0 | 0.5% |
| Stanford external validation cohort | NEWS2 | Low | 2 | 118,385 | 227.4 | 61.1% |
| Stanford external validation cohort | NEWS2 | Mid | 3 | 118,385 | 115.9 | 43.4% |
| Stanford external validation cohort | NEWS2 | High | 7 | 118,385 | 3.9 | 4.7% |
| Stanford external validation cohort | MEWS | Low | 2 | 118,385 | 288.8 | 63.8% |
| Stanford external validation cohort | MEWS | Mid | 4 | 118,385 | 54.3 | 24.8% |
| Stanford external validation cohort | MEWS | High | 6 | 118,385 | 6.1 | 6.0% |
| Stanford external validation cohort | REMS | Low | 3 | 118,385 | 579.7 | 84.5% |
| Stanford external validation cohort | REMS | Mid | 11 | 118,385 | 7.1 | 4.0% |
| Stanford external validation cohort | REMS | High | 12 | 118,385 | 2.4 | 2.2% |

The MIMIC denominator is 134,146 for all four scores; Stanford uses
118,385. Alerts and sensitivity are recalculated
from TP, FP, FN and TN and checked against the saved comparator rates.
The REMS High reference uses a relative probability target.
Default qSOFA returns no references and is omitted from the four-score comparison.


## Conventional rules and ESRP tiers

The remaining Table 3 and eTable 6 operating rows are supplied in
`results/sepsis_primary/conventional_rules/rule_operating_rows.csv` and
`esrp_tier_boundaries.csv`. The latter applies the ESRP derivation-study
boundaries 21/31/45 unchanged. Run `python examples/reproduce_extended.py`
to check these count-based rates and the 101-point derivation FAE curve.

See the [manuscript result map](evidence.md#manuscript-result-map) for every table and figure.

## Reproduction

Run `python examples/reproduce_paper.py --early-warning-scores` from the repository root.
It recomputes operating rates, action yields and R sensitivity from shared counts.
The action-probability estimates and intervals are restored from the reported
aggregate outputs; recomputing them requires encounter-level action and score data.

This aggregate entry point does not rebuild patient-level cohorts or
re-estimate every manuscript result. See the [reproduction scope](paper-reproduction.md).
