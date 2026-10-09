# Data for the primary paper workflow

The public repository shares synthetic examples, bin-level summaries, threshold
counts and evaluation summaries. Patient-level clinical tables are obtained
separately under the source data agreements.

## Source access

MIMIC data are available through the official [MIMIC-IV-ED](https://physionet.org/content/mimic-iv-ed/)
and [MIMIC-IV](https://physionet.org/content/mimiciv/) repositories. The Stanford
source is [MC-MED](https://physionet.org/content/mc-med/). These are credentialed-access
resources; follow the source repository's training and data-use requirements.
The primary runner takes the derived analysis variables below, rather than the
raw files supplied by those repositories.

## MIMIC analysis columns

| Column | Meaning |
|---|---|
| `subject_id` | Local patient identifier for the patient-disjoint split and cluster resampling |
| `score_ESRP_new` | Precomputed ESRP score; missing scores remain missing |
| `outcome_sepsis3` | Separately defined binary sepsis outcome |
| `lactate_flag` | Recorded lactate measurement under the primary source definition, allowing events through 48 hours |
| `icu_fluid_flag` | Primary inherited indicator based on `fluid_12h > 0` |
| `vasopressor_flag` | Recorded vasopressor use under the primary source definition, through 48 hours |
| `steroid_flag` | Recorded steroid use under the primary source definition, through 24 hours |
| `legacy_v7_primary_eligible` | Eligibility of the inherited action fields, based on the linkage rule below |

These heterogeneous observation windows define recorded sepsis-related assessment
and treatment activity. They do not specify a uniform early-ED window or completion
of a sepsis bundle. Antibiotics and blood cultures enter outcome ascertainment and
are excluded from the primary action composite.

### Linkage eligibility

The source construction links the inherited analysis fields by `stay_id`, checking
patient and admission identifiers. The eligibility rule is:

```python
eligible = (
    (legacy_data_available == 1)
    & (legacy_subject_id_discordant == 0)
    & (legacy_hadm_id_discordant == 0)
)
```

`legacy_data_available` identifies a matched inherited record. A discordance flag
is set when both the current and inherited identifier are observed and unequal.
This flag is specific to this analytic data integration, not a clinical exclusion
criterion. The runner can derive eligibility from these three columns if
`legacy_v7_primary_eligible` is absent. Keep the source rows for splitting and
policy evaluation; mask their action labels when eligibility is not 1.

### Composite and missingness

For the four action indicators, any observed 1 gives a positive composite; four
observed zeros give a negative composite; all other combinations are missing.
Nonbinary component entries are treated as missing in the primary analysis.
The eligibility mask is applied after this rule. Missing action is never encoded
as no action.

The primary fluid variable retains the inherited 12-hour definition. Reconstructing
it from raw events requires its source extraction and linkage pipeline. The
separate uniform-window analysis used another event definition and must not be
substituted for the primary variable. This repository entry point starts from
prepared analysis tables; it does not provide a complete raw-EHR extraction pipeline.

## Stanford analysis columns

Supply `score_ESRP`, `outcome_sepsis3`, `lactate_flag`, `fluid_6h`,
`vasopressor_flag` and `steroid_flag`. The fluid component is 1 when observed
six-hour fluid volume is at least 2,000 mL, 0 below it, and missing when volume is
missing. Combine the four components with the same missing-aware OR.

The MIMIC references 27/36/51 and selected candidate are transported unchanged.
The separate Stanford local diagnostic learns 26/36/50 in the reported cohort;
it does not replace the transported thresholds.

## Expected cohort checks

| Stage | Encounters |
|---|---:|
| MIMIC source, before complete-case filtering | 425,011 |
| MIMIC learning partition | 297,478 |
| MIMIC held-out partition | 127,533 |
| MIMIC learning score/action complete | 294,713 |
| MIMIC held-out score complete | 127,528 |
| MIMIC held-out score/action complete | 126,332 |
| Stanford evaluation | 118,385 |

The split uses `GroupShuffleSplit(train_size=0.70, random_state=2026)` on the complete
MIMIC source frame, grouped by patient. The held-out action subset contains 60,903
patients. The learning action rate is 96,268/294,713. Supported learning bins
contain 294,659 encounters; 54 complete rows fall in bins below the support limit.

Use the [reproduction guide](paper-reproduction.md) for commands. Record the actual
source releases and preprocessing versions when preparing new analysis tables.

## Additional-application inputs and public scope

COPD uses the supplied balanced-logistic `score_COPD_AutoScore` from
`autoscore_copd.ipynb`. `AutoScore` is a historical column/configuration label for
local binned logistic-regression scores, not the published R AutoScore workflow;
see Supplement eMethods 2. The unweighted `_fixed` score was not stored in the input
CSV. Existing filenames and column names are retained as data contracts.

The corrected action is documented bronchodilator administration/start within
24 hours OR the legacy Pyxis steroid-record proxy. Evaluation is conditional on
the supplied score. The patient-excluded subset and its AUROC 0.894 are reported
separately from the full threshold-evaluation cohort.

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
[source mapping](evidence.md) and [AERT scope](https://github.com/Sheldon0106/ActionRef/blob/v1.0.0-jamia-submission/results/aert/README.md).
