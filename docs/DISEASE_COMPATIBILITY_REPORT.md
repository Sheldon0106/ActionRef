# COPD and pneumonia compatibility run

Validation of the frozen v0.3 package on two non-sepsis diseases.

- Frozen Module 2 and evidence-gate parameters.
- No disease-specific override. The runner raises if a config supplies one.
- Bootstrap disabled. Module 3B unavailable in both.

```bash
python examples/disease_compatibility.py --config configs/copd_autoscore.yaml --data PATH --out-dir results/copd
```

## Definitions

| | COPD | Pneumonia |
|---|---|---|
| Notebook | `autoscore_copd_final_universal_fixed.ipynb` | `autoscore_pneumonia_final_universal.ipynb` |
| Score | `score_COPD_AutoScore` | `score_pneumonia_auto` |
| Outcome | `outcome_copd_exac` | `outcome_all_pne` |
| Primary response | bronchodilator_flag_24h OR steroid_flag | antibiotic_flag OR blood_culture_flag |
| Sensitivity response | none | primary plus lactate, vasopressor, ICU fluid |

Cohort: all ED encounters with a valid AutoScore value. N = 448,804 both datasets.

## Module 1

| | Prevalence | AUROC | AUPRC | Brier |
|---|---|---|---|---|
| COPD | 0.0104 | 0.904 | 0.142 | 0.0095 |
| Pneumonia | 0.0393 | 0.802 | 0.199 | 0.0342 |

Calibration is `apparent_in_sample`. A single labelled dataset was supplied.

## Module 2

Both passed the evidence gate under frozen parameters.

| | Response prev. | Bin width | Valid bins | Isotonic range | CPs | Low | Mid | High |
|---|---|---|---|---|---|---|---|---|
| COPD, primary | 0.0610 | 2.5 | 29 | 0.518 | 2 | 17.78 | 55.04 | abstention |
| Pneumonia, primary | 0.2715 | 1.0 | 34 | 0.751 | 0 | 5 | 14 | 24 |
| Pneumonia, broad | 0.3548 | 1.0 | 34 | 0.710 | 0 | 5 | 11 | 24 |

- All thresholds are `semantic-only`.
- No changepoint replaced a semantic anchor, including the COPD fit with two supported changepoints.
- COPD High abstains: the isotonic curve peaks near 0.53, so the 80% target is unreachable.
- That abstention propagates into Module 3A as `unavailable_behavior_threshold` at every capacity level.

## Module 3A

K fractions 0.01 to 0.30. For COPD:

- Low (17.78) is below the floor through 10% and is raised to it.
- Mid (55.04) is above every floor and is never adjusted.
- High propagates its abstention.

## Comparison against supplied reference anchors

Reference anchors from `*_module2_operational_anchors.csv`, produced by the earlier notebooks.

Pneumonia, `score_pneumonia_auto`:

| Bundle | Level | Reference | Source | Package |
|---|---|---|---|---|
| primary | Low | 5 | CP_aligned | 5 |
| primary | Mid | 14 | semantic_only | 14 |
| primary | High | 24 | CP_aligned | 24 |
| broad | Low | 6 | CP_aligned | 5 |
| broad | Mid | 11 | CP_aligned | 11 |
| broad | High | 24 | CP_aligned | 24 |

- Five of six reproduce exactly.
- Broad-bundle Low differs by one bin.
  - Scores 5.0 and 6.0 sit in the same pooled isotonic block at rate 0.377424.
  - The package returns the infimum. Fitted response probability is identical at both.

COPD, `score_COPD_AutoScore`, primary bundle:

| Level | Reference | Source | Package |
|---|---|---|---|
| Low | 14.886 | CP_aligned | 17.780 |
| Mid | 55.098 | CP_aligned | 55.041 |
| High | 57.009 | structural_fallback | abstention |

- Mid reproduces within 0.057.
- Low differs on bin width: reference 2.0, package 2.5 under the frozen rule. The anchor sits in the steep part of the curve.
- High differs by design.
  - Reference row is `structural_fallback_above_primary`: nearest stable changepoint substituted when semantic High was unreachable.
  - v0.3 prohibits this. The package abstains.

Data notes:

- Reference headline rows use `score_COPD_AutoScore_fixed`, absent from the dataset. `score_COPD_AutoScore` was used instead, compared against matching reference rows.
- Reference response column is `response_copd_primary`; the dataset provides `response_copd_directed`. Both report prevalence 0.061040.

## Findings

**1. The pneumonia primary bundle is circular.**

- Antibiotics and blood cultures also establish the diagnosis.
- V7 excluded both from the sepsis primary bundle for this reason.
- No circularity-aware bundle exists here. The notebook bundle was used as specified.
- The broad bundle inherits the issue.
- A COPD-style disease-directed bundle would be the closer analogue.

**2. COPD Mid is above every capacity floor tested.**

- At 30% capacity the floor is 13.82 and Mid is 55.04.
- Most capacity goes unused.
- This follows from the low response ceiling.

**3. Both AUROC values are in-sample.** Neither run used a split.

## Not performed

- Bootstrap. Compatibility run only.
- Module 3B. No disease-specific R elicited or costed.
- AKI. Data, notebook, and reference anchors available.

## Committed outputs

Aggregate only. Largest table 34 rows. No encounter identifiers.

```
results/copd/        summary.json, module2_anchors_primary.csv,
                     module2_response_curve_primary.csv, module3a_capacity.csv
results/pneumonia/   summary.json, module2_anchors_{primary,sensitivity}.csv,
                     module2_response_curve_{primary,sensitivity}.csv,
                     module3a_capacity.csv
```
