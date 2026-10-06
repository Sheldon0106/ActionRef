# Sepsis: understand practice, then compare candidates

The primary MIMIC analysis illustrates two distinct outputs: references learned
from recorded actions, and a candidate evaluated under a declared consequence
scenario. These values belong to this study rather than being package defaults.

## Behavioral references

The learning cohort has 294,713 complete score–action rows. The saved curve retains
26 bins containing 294,659 encounters; 54 encounters fall in bins below the support
requirement. The complete-row background action rate is approximately 32.7%.

| Reference | Score | Meaning in this analysis |
|---|---:|---|
| Low | 27 | First fitted bin reaching the background action rate |
| Mid | 36 | First fitted bin reaching action probability 0.50 |
| High | 51 | First fitted bin reaching action probability 0.80 |

![MIMIC learning action curve, bin support, and held-out action reliability.](assets/figures/clinical-action.png)

The left panels show the saved learning curve and bin counts. The right panel
uses the fixed curve on 126,332 held-out encounters with complete score and action.
Points show observed versus mean predicted action probabilities within fixed
0.1-wide probability bins; empty bins are omitted. Point area reflects bin count.

The held-out action Brier score is 0.1943, compared with 0.2192 for the constant
learning action rate. Mean predicted action probability is 33.37%, versus 32.45%
observed. This assesses prediction of recorded actions. The displayed reliability
points are descriptive, without confidence intervals. The Brier score's 95%
patient-cluster interval is 0.1930–0.1956; the paired difference from the constant
comparator is −0.0249 (−0.0264 to −0.0234). These intervals condition on the learned
curve. Full estimates and the bin-assignment sensitivity appear in the
[primary result tables](paper-results.md).

## Define the recorded action

The primary composite contains lactate measurement, a legacy fluid indicator,
vasopressor use, or steroid use. Source windows differ: lactate and vasopressors
allow up to 48 hours, steroids up to 24 hours, and the fluid indicator uses a
12-hour definition. These are inclusion windows, not estimates of when most actions
occurred. The composite mainly reflects sepsis-related assessment and treatment
activity; it is not a uniform early-ED window or a completed sepsis bundle.

## A separate candidate-comparison question

In the paper's worked scenario, Low 27 supplies a workload comparison ceiling and
`R = 11,299 / 804 ≈ 14.05` weights a missed outcome relative to a false-positive
alert for a proposed diagnostic and short-course antibiotic workflow.
The candidate selected on learning data is 31; Low remains 27.

On 127,528 score-complete MIMIC held-out encounters, moving from 27 to 31 produces
approximately 123 fewer alerts per 1,000 encounters, including 116 fewer alerts
among outcome-negative encounters, while flagging about 6.75 fewer outcome-positive
encounters. Weighted loss decreases by 4.2% in that scenario. The proposed workflow
and the recorded composite action are different quantities.

This illustrates how a candidate's gains and coverage cost can be presented
together. It does not assign a universal preference to 31. The action-evaluation
sample above is smaller because it additionally requires an observed action label.

Among flagged encounters with known action, candidate 31 has an observed-action
yield of **54.84%** in MIMIC held-out data (16,909/30,834) and **57.33%** in Stanford
(14,696/25,636). These yields summarize the flagged population, rather than the
fitted action probability at score 31.

The fixed 31-versus-27 loss comparison changes sign at R ≈ **17.19** in MIMIC and
**22.51** in Stanford. Above the relevant crossing, 27 has lower weighted loss
within this pair. This is sensitivity of a fixed comparison, with no candidate
reselection in evaluation data. [Rebuild the tables](paper-reproduction.md).

## Sources and analysis role

The curve and action-evaluation figure use saved aggregate research outputs,
described in [figure sources](figures.md). The [V7 regression record](CONTROLLED_REGRESSION_REPORT.md)
documents the primary reference values and the separate Stanford local diagnostic
(26 / 36 / 50). Local re-estimation and transport evaluation answer different questions.
