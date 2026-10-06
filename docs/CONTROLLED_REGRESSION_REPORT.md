# Controlled V7 regression report

- Contract: Universal Cutoff Framework v0.3 Final
- Executable reference: completed-bootstrap V7 notebook
- Clinical inputs read from an ignored private directory. Not copied into this repository.

| Check | MIMIC | Stanford |
|---|---:|---:|
| Full cohort N | 425,011 | 118,385 |
| Learning N | 297,478 | not applicable |
| Outcome-positive N | not applicable | 5,262 |
| Selected bin width | 3 | 2 |
| Valid response bins | 26 | 32 |
| Low / Mid / High | 27 / 36 / 51 | 26 / 36 / 50 |
| Provenance | A/A/A | A/A/A |
| CP corroboration | none | none |

**Result: PASS.** Both fixtures match the frozen v0.3 targets.

Method:

- MIMIC response: missing-aware OR over lactate, ICU fluid, vasopressor, steroid, then `legacy_v7_primary_eligible`.
- Split: `GroupShuffleSplit(train_size=0.70, random_state=2026)`.
- Learning N is the split row count. Module 2 complete-case N is 294,713.
- Stanford local diagnostic response: lactate, substantial fluid (`fluid_6h >= 2000 mL` when observed), vasopressor, steroid.
- `mimic_analysis.csv` and `stanford_analysis.csv` not required. The supplied cohorts carry the authoritative `outcome_sepsis3` fields and Stanford's positive count matches 5,262.

## Verification history

**2026-08-20**

- 37 tests passed on the local interpreter and the reference stack (Python 3.8.20, NumPy 1.23.5, pandas 1.2.5, SciPy 1.10.1, scikit-learn 1.3.0).
- Wheel and source distribution built.

**2026-08-23**, after the R-guidance revisions

- 47 tests passed on the same reference stack.
- The regression above reproduced.
- COPD compatibility run reproduced exactly: bin width 2.5, 29 valid bins, Low/Mid/High of 17.78, 55.04, abstention.
- pandas 1.2.5 emits its known NumPy percentile-argument deprecation warning during bootstrap quantiles. No test failed.
