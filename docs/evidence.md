# Evidence and analysis roles

The paper uses sepsis ESRP as the primary application, followed by COPD and an
exploratory HEART-derived AERT application. Public research outputs contain
aggregate summaries. Each result belongs to a specified score, cohort, split and
recorded-action definition.

| Material | Role in the paper |
|---|---|
| MIMIC sepsis 27 / 36 / 51 | Primary behavioral references |
| Stanford sepsis 26 / 36 / 50 | Local reference re-estimation, separate from transport of MIMIC thresholds |
| `results/sepsis_primary/` | Primary operating/action counts, action-probability evaluation and fixed 31-versus-27 R sensitivity: Table 3 and eTables 35–37 |
| `results/copd/validation_v2_corrected/` | Additional COPD application with corrected recorded actions: Table 4 and eTables 21, 22, 39 and 41 |
| `results/aert/` | Exploratory HEART-derived AERT application: Table 4, eTables 32–34 and 38, and Supplementary Data 1–2 |
| `results/copd/validation_v1/` | Earlier COPD action definition; retained for comparison and software regression, not the corrected paper application |
| `results/aki/` and the corresponding configurations | Software development and compatibility records; not reported in the paper |
| `results/pneumonia/` and the corresponding configurations | Software development and compatibility records; not reported in the paper |
| `results/cross_disease_validation_v1/` and its configuration | Historical combined development summaries and provenance; retained for manifest and test compatibility |
| Earlier compatibility and R-tier reports | Development records under their stated settings; current paper scenarios are identified separately |

## Primary sepsis application

MIMIC behavioral references retain their recorded-action meanings. Candidate 31
was selected on learning data under the Low-27 workload ceiling and R = 11,299/804,
then evaluated unchanged. Stanford transport uses the MIMIC thresholds; the
26 / 36 / 50 local references answer a separate practice-description question.
Begin with the [sepsis illustration](clinical-example.md) and
[reported tables](paper-results.md).

eTable 37 contains the fixed 31-versus-27 comparison only. Learning-data
re-selection and the R-setting procedure are described in Supplement eMethods 3;
see the [R guide](R_GUIDANCE.md). The Supplement contains six eFigures: its
additional-application reference display includes COPD and AERT, and its output
state matrix includes primary sepsis, the one-hour sepsis window, COPD, AERT and
the flat-zero simulation.

## Additional applications

### COPD

The corrected action combines documented bronchodilator administration/start
within 24 hours with the **legacy Pyxis steroid-record proxy**. The bronchodilator
definition excludes records without documented administration/start. The steroid
field retains its historical first-record and missing-to-zero conventions; actual
administration, dose, route and indication are not established by that proxy.

The full-learning references are Low 17.7798 and Mid 55.0719. Relative High targets
0.4278 at bin 50, below Mid's bin 55, so the ordering rule leaves High unavailable
without replacement. See [the real-data partial-output example](output-states.md#real-data-partial-output-copd).

The evaluation is **conditional on the supplied score**. The subset excluding all
score-fitting patients contains 13,978 patients and 15,221 encounters, with AUROC
0.894 (eTable 41). Earlier preprocessing and score rescaling used the source
population; this subset is a supplemental within-data evaluation. Sources and
denominators are documented in [the corrected aggregate bundle](https://github.com/Sheldon0106/ActionRef/blob/v1.0.0-jamia-submission/results/copd/validation_v2_corrected/README.md).

### HEART-derived AERT

AERT contains age, ECG, coded risk factors and troponin, with a native theoretical
range of 0–8 and no measured History component. The strict three-hour construction
has 2,489 complete encounters: 1,704 development and 785 previously inspected,
patient-disjoint test encounters. The ADMITTED/HOME analysis used in Table 4 has
756 test encounters and retained Mid 3 and High 6; the separate hospitalization-
linkage analysis retained Low 3. These recorded-action definitions remain distinct.

The unchanged eight-bin policy abstains in the strict three-hour baseline settings.
The short-discrete research extension is provided separately and preserves partial
outputs. The test partition was previously inspected, and the diagnostic endpoint
is index-encounter ACS/MI rather than 30-day MACE. No K, R, FAE or monetary-cost
analysis is applied to AERT. [Public materials](https://github.com/Sheldon0106/ActionRef/blob/v1.0.0-jamia-submission/results/aert/README.md) include
all 16 settings and the native/fixed-H=1 sensitivity.

## Historical score names

`AutoScore` in configuration filenames and column names, such as
`copd_autoscore.yaml` and `score_COPD_AutoScore`, is a historical label. These
scores were constructed locally from binned predictors and logistic-regression
weights; they were not generated by the published R AutoScore workflow. Construction
details are in Supplement eMethods 2. File and column names are retained to preserve
the input data contract.

The supplied COPD column is the balanced-logistic score from `autoscore_copd.ipynb`.
The unweighted `_fixed` score was not stored in the input CSV. The early
[compatibility report](DISEASE_COMPATIBILITY_REPORT.md) and
[regression report](CONTROLLED_REGRESSION_REPORT.md) retain their earlier bin-width
settings and values.

## Reproduction and provenance

Use the [paper reproduction guide](paper-reproduction.md) for commands and the
mapping from reported tables to source aggregates. Clinical inputs are obtained
separately under their data agreements; this repository distributes no patient
records or identifiers.

Saved metadata includes analysis settings and input/output checksums. Personal
filesystem paths are replaced with portable placeholders. The historical
cross-disease manifest retains its original and public-copy hashes; its archived
results and configurations remain unchanged. New COPD and AERT manifests identify
the aggregate files used for the reported applications.
