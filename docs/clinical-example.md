# Sepsis: reference thresholds and a specified revision

The primary MIMIC analysis illustrates two distinct outputs: references estimated
from recorded actions, and a revised threshold evaluated under a declared consequence
scenario. These values belong to this study rather than being package defaults.
The analysis uses a clinical-only Sepsis-3 outcome and patient-disjoint derivation
and internal validation sets; the [data contract](paper-data.md) defines the population
and inputs.

## Behavioral references

The derivation cohort has 311,675 complete score–action rows. The saved curve retains
26 bins containing 311,618 encounters; 57 encounters fall in bins below the support
requirement. The complete-row background action rate is approximately 30.9%.

| Reference | Score | Meaning in this analysis |
|---|---:|---|
| Low | 27 | First fitted bin reaching the background action rate |
| Mid | 39 | First fitted bin reaching action probability 0.50 |
| High | 54 | First fitted bin reaching action probability 0.80 |

The fixed action curve is evaluated on 132,878 internal validation encounters
with complete score and action.

The internal validation action Brier score is 0.1900, compared with 0.2130 for the constant
derivation action rate. Mean predicted action probability is 31.75%, versus 30.78%
observed. This assesses prediction of recorded actions. The Brier score's 95%
patient-cluster interval is 0.1887–0.1913; the paired difference from the constant
comparator is −0.0230 (−0.0243 to −0.0217). These intervals condition on the learned
curve. Full estimates and the bin-assignment sensitivity appear in the
[aggregate results](paper-results.md).

## Define the recorded action

The primary composite contains lactate measurement, a legacy fluid indicator,
vasopressor use, or steroid use. MIMIC source windows differ: lactate and
vasopressors allow up to 48 hours, steroids up to 24 hours, and the fluid indicator
uses a 12-hour definition. Stanford uses a six-hour fluid-volume threshold of
2,000 mL. These are inclusion windows, not estimates of when most actions occurred.
The composite mainly reflects sepsis-related assessment and treatment activity;
it is not a uniform early-ED window or a completed sepsis bundle.

## Revising the operating threshold

In the paper's worked scenario, Low 27 supplies a workload comparison ceiling and
`R = 11,299 / 804 ≈ 14.05` weights a missed outcome relative to a false-positive
alert for a proposed diagnostic and short-course antibiotic workflow.
The revised threshold selected on derivation data is 34; Low remains 27. The derivation-set
ceiling is **116,236** alerts, while 34 produces **59,849**; it is also the
unconstrained minimum-loss threshold in this scenario.

On 134,146 score-complete MIMIC internal validation encounters, moving from 27 to 34 produces
approximately 174 fewer alerts per 1,000 encounters, including 166 fewer alerts
among outcome-negative encounters, while flagging about 8.01 fewer outcome-positive
encounters. The net weighted-loss difference is **−53.8 per 1,000** (34 minus 27),
a decrease of 11.3%, in that scenario. The proposed workflow and the recorded
composite action are different quantities.

This illustrates how the revised threshold's gains and coverage cost can be presented
together. The preferred candidate depends on the specified consequences and
capacity. The action-evaluation sample above is smaller because it additionally
requires an observed action label.

Among flagged encounters with known action, revised threshold 34 has a recorded-action
yield of **55.58%** in the MIMIC internal validation set (14,024/25,234) and **61.72%** in Stanford
(11,867/19,226). These yields summarize the flagged population, rather than the
fitted action probability at score 34.

The fixed 34-versus-27 loss comparison changes sign at R ≈ **20.77** in MIMIC and
**26.28** in Stanford. Above the relevant crossing, 27 has lower weighted loss
within this pair. This is sensitivity of a fixed comparison, with no candidate
reselection in evaluation data. [Check the aggregate calculations](paper-reproduction.md).

## Analysis inputs

The [data contract](paper-data.md) defines the score, outcome, action components
and cohort split. The [aggregate results guide](paper-results.md) identifies
saved counts and estimates; the [reproduction guide](paper-reproduction.md)
describes the calculation and verification commands.
