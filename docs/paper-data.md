# Data for the primary paper workflow

The public repository shares synthetic examples, bin-level summaries, threshold
counts and evaluation summaries. Patient-level clinical tables are obtained
separately under the source data agreements.

## Source access and population

MIMIC data are available through the official [MIMIC-IV-ED](https://physionet.org/content/mimic-iv-ed/)
and [MIMIC-IV](https://physionet.org/content/mimiciv/) repositories. The Stanford
source is [MC-MED](https://physionet.org/content/mc-med/). These are credentialed-access
resources; follow the source repository's training and data-use requirements.
The primary runner takes derived analysis variables, rather than raw source files.

The MIMIC analysis uses all 448,804 adult encounters in the ED 1.0 analysis
population, with source-matched scores, action records and clinical covariates.
The clinical-only outcome, `sepsis3_new`, uses the four-domain, nonnegative,
baseline-adjusted delta-SOFA rule. It is distinct from an ICD-or-clinical composite.
Stanford uses the corresponding clinical-only outcome and the supplied
`score_corrected` ESRP score. Scores are not retrained or rescaled by this workflow.

## MIMIC analysis columns

| Column | Meaning |
|---|---|
| `subject_id` | Local patient identifier for the patient-disjoint split and cluster resampling |
| `score_ESRP_new` | Supplied ESRP score |
| `sepsis3_new` | Separately defined clinical-only Sepsis-3 outcome |
| `lactate_flag` | Recorded lactate measurement under the primary source definition, allowing events through 48 hours |
| `icu_fluid_flag` | Primary inherited indicator based on `fluid_12h > 0` |
| `vasopressor_flag` | Recorded vasopressor use under the primary source definition, through 48 hours |
| `steroid_flag` | Recorded steroid use under the primary source definition, through 24 hours |

These heterogeneous observation windows define recorded sepsis-related assessment
and treatment activity. They do not specify a uniform early-ED window or completion
of a sepsis bundle. Antibiotics and blood cultures enter outcome ascertainment and
are excluded from the primary action composite.

### Composite and missingness

For the four action indicators, any observed 1 gives a positive composite; four
observed zeros give a negative composite; all other combinations are missing.
Nonbinary component entries are treated as missing in the primary analysis.
Missing action is never encoded as no action.

The primary fluid variable retains the inherited 12-hour definition. Reconstructing
it from raw events requires its source extraction and linkage pipeline. The
separate uniform-window analysis used another event definition and must not be
substituted for the primary variable. This repository entry point starts from
prepared analysis tables; it does not provide a complete raw-EHR extraction pipeline.

## Stanford analysis columns

Supply `score_corrected`, `sepsis3_new`, `lactate_flag`, `fluid_6h`,
`vasopressor_flag` and `steroid_flag`. The fluid component is 1 when observed
six-hour fluid volume is at least 2,000 mL, 0 below it, and missing when volume is
missing. Combine the four components with the same missing-aware OR.

The MIMIC references 27/39/54 and selected candidate 34 are transported unchanged.
The separate Stanford local diagnostic learns 26/36/50 in the reported cohort;
it does not replace the transported thresholds.

## Expected cohort checks

| Cohort | Encounters | Patients | Outcome-positive encounters | Action-known encounters |
|---|---:|---:|---:|---:|
| MIMIC learning | 314,658 | 151,699 | 12,099 | 311,675 |
| MIMIC held-out | 134,146 | 65,015 | 5,206 | 132,878 |
| Stanford evaluation | 118,385 | 70,545 | 3,809 | 118,385 |

The split uses `GroupShuffleSplit(train_size=0.70, random_state=2026)` on the complete
MIMIC analysis population, grouped by patient. All five evaluated scores and the
outcome are complete in these cohorts. The held-out action subset contains 64,278
patients. The learning action rate is 96,415/311,675. Supported learning bins
contain 311,618 encounters; 57 complete rows fall in bins below the support limit.

Use the [reproduction guide](paper-reproduction.md) for commands. Preserve the
population, patient assignment, source definitions and outcome version when
preparing analysis inputs. Differences from historical repository results involve
these analysis choices and cannot be interpreted as score deterioration over time.

## Exploratory inputs (not reported in the manuscript)

COPD, AERT/HEART, pneumonia and AKI materials are **exploratory, not reported in
the manuscript**. Existing code and data contracts are retained.

COPD uses the supplied balanced-logistic `score_COPD_AutoScore` from
`autoscore_copd.ipynb`. `AutoScore` is a historical column/configuration label for
local binned logistic-regression scores, not the published R AutoScore workflow;
the label is retained for compatibility. The unweighted `_fixed` score was not
stored in the input CSV. Existing filenames and column names are retained as data contracts.

The corrected action is documented bronchodilator administration/start within
24 hours OR the legacy Pyxis steroid-record proxy. Evaluation is conditional on
the supplied score. The patient-excluded subset and its AUROC 0.894 are reported
separately from the full threshold-evaluation cohort; both are exploratory materials.

AERT public inputs are score-level counts, component/population summaries, fixed
probability maps, output states and bootstrap summaries. The supplied score is the
four-component HEART-derived AERT proxy; fixed H=1 is a separate shift sensitivity.
ADMITTED/HOME and hospitalization linkage are different action definitions. The
aggregate runner begins after raw component construction, earliest-encounter
selection, reserved-patient exclusion and the original patient-disjoint assignment.
The exact patient-order bootstrap requires restricted analysis records and is
not reconstructed from these public bins.

No patient records, identifiers, notes, annotation/linkage packs, individual
predictions or record-identifying source offsets are distributed. See the
[source mapping](evidence.md) and [AERT scope](https://github.com/Sheldon0106/ActionRef/blob/v1.0.3-jamia/results/aert/README.md).
