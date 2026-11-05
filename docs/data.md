# Prepare your data

Supply a pandas DataFrame with one row per encounter. The package uses a
precomputed score; it does not train the underlying clinical prediction model.

| Field | Required for | Definition |
|---|---|---|
| `score` | All paths | Finite numeric score; higher values indicate greater concern. |
| `response` | Behavioral references | Binary 0/1 record of a defined action or composite, within a declared window. |
| `outcome` | Outcome evaluation and Module 3B | Separate binary outcome with a declared ascertainment horizon. |
| Patient identifier | Group splitting / grouped bootstrap | A local grouping field, kept out of public outputs. |

Column names are configurable. Numeric strings are coerced to numbers; nonnumeric
values become missing. Validate the source schema so that miscoded labels are
detected. Observed binary values other than 0 and 1 raise an input error. A
descending score should be reoriented explicitly before use.

## Define the action before fitting

Record each component, its observation window, eligibility rules, and missingness
handling. For an OR composite, distinguish a measured absence from an unobserved
component. A positive composite dominated by a test primarily describes assessment
activity; it need not represent completed treatment.

Keep the observed action and a proposed alert-triggered workflow separate. Their
relationship belongs in the interpretation, not in a silent relabeling of inputs.

## Keep learning and evaluation separate

`run_framework` does not create a data split. Split upstream, using patient groups
when people contribute repeated encounters. Learn references and choose candidates
on derivation data, then evaluate their fixed values on internal validation or external data.
Fit any outcome calibrator on development data and evaluate it separately when
an internal validation calibration claim is needed.

## Denominators and missing data

- **Module 2:** complete score–response rows determine the background action rate.
  Bins below `min_bin_n` are excluded from the fitted curve.
- **Alert burden:** all valid-score rows form the policy denominator.
- **Recorded-action yield:** action positives among flagged rows with an observed
  response label, divided by flagged rows with an observed response label.
- **Outcome metrics:** valid-score rows with an observed outcome label.

These denominators can differ. Report relevant complete-case counts alongside the
results. A blank yield or unavailable reference must not be replaced by zero.

Clinical encounter datasets are not distributed here. Keep local datasets under
ignored directories and export aggregate summaries for sharing. The
[synthetic walkthrough](quickstart.md) needs no clinical database.

## Sepsis study inputs

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

### MIMIC analysis columns

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

### Stanford analysis columns

Supply `score_corrected`, `sepsis3_new`, `lactate_flag`, `fluid_6h`,
`vasopressor_flag` and `steroid_flag`. The fluid component is 1 when observed
six-hour fluid volume is at least 2,000 mL, 0 below it, and missing when volume is
missing. Combine the four components with the same missing-aware OR.

The MIMIC references 27/39/54 and selected revised threshold 34 are transported unchanged.
Stanford local estimation yields 26/36/50 in the reported cohort;
it does not replace the transported thresholds.

### Triage-score definition

The supplied qSOFA implementation is `I(respiratory rate >= 22/min) +
I(systolic blood pressure <= 100 mmHg)`, ranging from 0 to 2; the mental-status
component is omitted. Missing component comparisons contribute zero under the
existing implementation. The score definition files list the components and
missingness rules for NEWS2, MEWS and REMS as well.

### Study cohorts

| Cohort | Encounters | Patients | Outcome-positive encounters | Action-known encounters |
|---|---:|---:|---:|---:|
| MIMIC derivation set | 314,658 | 151,699 | 12,099 | 311,675 |
| MIMIC internal validation set | 134,146 | 65,015 | 5,206 | 132,878 |
| Stanford external validation cohort | 118,385 | 70,545 | 3,809 | 118,385 |

The split uses `GroupShuffleSplit(train_size=0.70, random_state=2026)` on the complete
MIMIC analysis population, grouped by patient. All five evaluated scores and the
outcome are complete in these cohorts. The internal validation action subset contains 64,278
patients. The derivation action rate is 96,415/311,675. Supported derivation bins
contain 311,618 encounters; 57 complete rows fall in bins below the support limit.

See [study materials](paper-reproduction.md) for the analysis commands.
