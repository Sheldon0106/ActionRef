# Exploratory HEART-derived AERT materials

These materials are **exploratory, not reported in the manuscript**. AERT comprises age, ECG, coded risk factors and troponin, with a native
theoretical range of 0–8 and no measured History component. Fixed H=1 is a separate
arithmetic-shift sensitivity.

| Material | Aggregate source |
|---|---|
| Component and cohort summaries | `component_coverage.csv`, `component_score_distributions.csv`, `cohort_summary.csv`, `included_vs_excluded.csv`, `candidate_protocol.json` and `population_registry.json` |
| Development reference summaries | `models_frozen.json`, `development_curves.json`, `development_anchor_summary.json` and `development_stability_summary.json` |
| Operating summaries | `test_operating_point.json`, `test_operating_intervals.json` and `score_response_distribution.json` |
| Action-probability summaries | Strict three-hour baseline rows of `action_calibration_points.json` and `action_calibration_intervals.json` |
| All operating settings | All settings in `test_operating_point.json` and `test_operating_intervals.json`: 55 native operating points (31 research-policy and 24 default-policy), paired with 55 fixed-H=1 points |
| All action-probability settings | All 16 settings and three support scopes in `action_calibration_points.json`, with `action_calibration_intervals.json`, `action_models_evaluated.json` and `action_reliability_bins.json` |

The strict three-hour baseline construction has 2,489 complete encounters
(1,704 development; 785 previously inspected patient-disjoint test encounters).
The exploratory ADMITTED/HOME setting **H02** has 756 test
encounters. Low and Mid coincide at score **3**: their targets are **41.42%** and
**50%**, and the fitted action probability is **30.92%** at score 2 and **53.62%**
at score 3. The shared-threshold rule retains **Mid = 3** as the operational
representative, with **High = 6** and no distinct Low operating point. Low is
attainable and shares Mid's threshold. Hospitalization linkage is a separate
response, with retained Low **3**. The diagnostic endpoint is index-encounter
ACS/MI, not 30-day MACE.

The unchanged eight-bin policy abstains in these strict three-hour baseline
settings. The short-discrete research extension is separate from that default and
includes support, evidence, ordering and terminal-tail safeguards. It does not
replace unavailable levels with bootstrap medians. AERT has no K, R, FAE or
monetary-cost analysis.

## Executable reproduction

```bash
python examples/reproduce_aert.py
```

The command checks hashes, replays both policies on development score-level counts,
recalculates operating counts from test score-level aggregates, and checks action
probability summaries against fixed curves. It writes table-oriented CSV files to
ignored `output/aert/`, including all All operating settings–2 rows. Reference
uncertainty and evaluation intervals are assembled from the supplied 200-draw
patient-bootstrap summaries. Their exact patient resampling cannot be replayed
from aggregate bins because patient ordering is not distributed.

The reference implementation is `examples/aert_reference_policy.py`; settings
are in `configs/aert.json`. No patient identifiers are needed for this aggregate
entry point. Score construction summaries and the protocol are included; the entry
point begins from the reported score-level aggregates, rather than raw ECG reports
or raw EHR tables.

## Public and restricted scope

Public: score/bin counts, component/population summaries, probability maps,
reference/output states, point estimates, bootstrap summaries, configuration and
the reference-policy/reproduction code. All saved exploratory settings are retained.

Not distributed: patient/encounter records and identifiers, clinical note text
or excerpts, private annotation cards, linkage packs, individual predictions,
patient-order vectors and source offsets identifying records. These require
authorized source-data access. No independent clinical History adjudication is
represented by the fixed-H=1 sensitivity.

`manifest.json` identifies the original sources and public-copy hashes using
portable placeholders. No numerical result values are changed.
