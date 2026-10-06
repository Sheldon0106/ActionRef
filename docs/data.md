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
on learning data, then evaluate their fixed values on held-out or external data.
Fit any outcome calibrator on development data and evaluate it separately when
a held-out calibration claim is needed.

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
