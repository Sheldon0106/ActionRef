# Sepsis: understand practice, then compare candidates

The primary MIMIC analysis illustrates two distinct outputs: references estimated
from recorded actions, and a candidate evaluated under a declared consequence
scenario. These values belong to this study rather than being package defaults.
The analysis uses a clinical-only Sepsis-3 outcome and patient-disjoint learning
and held-out cohorts; the [data contract](paper-data.md) defines the population
and inputs.

## Behavioral references

The learning cohort has 311,675 complete score–action rows. The saved curve retains
26 bins containing 311,618 encounters; 57 encounters fall in bins below the support
requirement. The complete-row background action rate is approximately 30.9%.

| Reference | Score | Meaning in this analysis |
|---|---:|---|
| Low | 27 | First fitted bin reaching the background action rate |
| Mid | 39 | First fitted bin reaching action probability 0.50 |
| High | 54 | First fitted bin reaching action probability 0.80 |

![MIMIC learning action curve, bin support, and held-out action reliability.](assets/figures/clinical-action.png)

The left panels show the saved learning curve and bin counts. The right panel
uses the fixed curve on 132,878 held-out encounters with complete score and action.
Points show observed versus mean predicted action probabilities within fixed
0.1-wide probability bins; empty bins are omitted. Point area reflects bin count.

The held-out action Brier score is 0.1900, compared with 0.2130 for the constant
learning action rate. Mean predicted action probability is 31.75%, versus 30.78%
observed. This assesses prediction of recorded actions. The displayed reliability
points are descriptive, without confidence intervals. The Brier score's 95%
patient-cluster interval is 0.1887–0.1913; the paired difference from the constant
comparator is −0.0230 (−0.0243 to −0.0217). These intervals condition on the learned
curve. Full estimates and the bin-assignment sensitivity appear in the
[primary result tables](paper-results.md).

## Define the recorded action

The primary composite contains lactate measurement, a legacy fluid indicator,
vasopressor use, or steroid use. MIMIC source windows differ: lactate and
vasopressors allow up to 48 hours, steroids up to 24 hours, and the fluid indicator
uses a 12-hour definition. Stanford uses a six-hour fluid-volume threshold of
2,000 mL. These are inclusion windows, not estimates of when most actions occurred.
The composite mainly reflects sepsis-related assessment and treatment activity;
it is not a uniform early-ED window or a completed sepsis bundle.

## A separate candidate-comparison question

In the paper's worked scenario, Low 27 supplies a workload comparison ceiling and
`R = 11,299 / 804 ≈ 14.05` weights a missed outcome relative to a false-positive
alert for a proposed diagnostic and short-course antibiotic workflow.
The candidate selected on learning data is 34; Low remains 27. The learning-sample
ceiling is **116,236** alerts, while 34 produces **59,849**; it is also the
unconstrained minimum-loss threshold in this scenario.

On 134,146 score-complete MIMIC held-out encounters, moving from 27 to 34 produces
approximately 174 fewer alerts per 1,000 encounters, including 166 fewer alerts
among outcome-negative encounters, while flagging about 8.01 fewer outcome-positive
encounters. The net weighted-loss difference is **−53.8 per 1,000** (34 minus 27),
a decrease of 11.3%, in that scenario. The proposed workflow and the recorded
composite action are different quantities.

This illustrates how a candidate's gains and coverage cost can be presented
together. The preferred candidate depends on the specified consequences and
capacity. The action-evaluation sample above is smaller because it additionally
requires an observed action label.

Among flagged encounters with known action, candidate 34 has a recorded-action
yield of **55.58%** in MIMIC held-out data (14,024/25,234) and **61.72%** in Stanford
(11,867/19,226). These yields summarize the flagged population, rather than the
fitted action probability at score 34.

The fixed 34-versus-27 loss comparison changes sign at R ≈ **20.77** in MIMIC and
**26.28** in Stanford. Above the relevant crossing, 27 has lower weighted loss
within this pair. This is sensitivity of a fixed comparison, with no candidate
reselection in evaluation data. [Rebuild the tables](paper-reproduction.md).

## Sources and analysis role

The curve and action-evaluation figure use saved aggregate research outputs,
described in [figure sources](figures.md). The [aggregate results](paper-results.md)
report the primary evaluation. The separate Stanford local diagnostic estimates
26 / 36 / 50; transported evaluation retains the MIMIC references 27 / 39 / 54.
Local re-estimation and transport evaluation answer different questions.
