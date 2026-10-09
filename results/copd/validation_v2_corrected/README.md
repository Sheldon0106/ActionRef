# Corrected COPD application

These aggregates support **Table 4 and Supplement eTables 21, 22, 39 and 41**.
They use the supplied balanced-logistic `score_COPD_AutoScore` without score
refitting. Evaluation is **conditional on the supplied score**.

The recorded action is documented bronchodilator administration/start within
24 hours OR the **legacy Pyxis steroid-record proxy**. The steroid field retains
its historical missing-to-zero convention and does not establish actual
administration, route, dose or indication. See `tables/steroid_proxy_audit.csv`.

Full-learning references are Low **17.7798**, Mid **55.0719**, and unavailable
High. Relative High targets **0.4278** at bin **50**, below Mid's bin **55**;
ordering rejects it without replacement.

| Paper item | Aggregate source |
|---|---|
| eTable 21 | `reference/module2_point_anchors.csv`, `reference/stability_summary_package.csv`, `reference/joint_tier_audit_package.csv` and `reference/adjacent_gap_package.csv` |
| Table 4 and eTable 22 | Corrected rows of `tables/operating_comparison.csv` and `tables/operating_intervals.csv` |
| eTable 39 | `reference/stability_summary_package.csv`, `reference/joint_summary_package.json` and the joint/adjacent-gap summaries |
| eTable 41 | `tables/predictive_point.csv`, `tables/predictive_intervals.csv`, `tables/cohort_summary.csv` and corrected score-fit-excluded operating rows |
| COPD partial-output illustration | `reference/module2_response_curve.csv` and `reference/module2_point_anchors.csv` |
| Action-definition audit | `tables/bronchodilator_status_audit.csv`, `tables/steroid_proxy_audit.csv` and `tables/response_correction_by_cohort.csv` |

The full evaluation contains **65,015 patients / 134,175 encounters**. Excluding
every patient represented in score-fitting rows leaves **13,978 patients /
15,221 encounters**, with **AUROC 0.894**. Earlier source-population preprocessing
and score rescaling remain part of the supplied score. Reference re-estimation
uses 500 patient-cluster draws; fixed-score/fixed-reference operating and predictive
intervals use 200 draws.

`manifest.json` retains portable source provenance, original file hashes and
public-copy hashes. CSV result values are unchanged. JSON missing thresholds use
`null`. There are no patient records or identifiers in this bundle.

The earlier `results/copd/validation_v1/` results use the old action definition
and are retained as a historical comparison. They do not supply the corrected
paper results.

From the repository root:

```bash
python examples/reproduce_additional.py
```

This verifies the aggregate sources and writes table-oriented summaries to ignored
`output/copd/`. It assembles the supplied intervals rather than rerunning patient
resampling. Configuration: `configs/copd_corrected.json`.
