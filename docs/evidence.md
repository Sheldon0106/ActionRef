# Evidence and analysis roles

Public research outputs are aggregate summaries. Their role depends on the cohort,
split, action definition, and analysis configuration; sharing a folder does not
make all outputs one analysis.

| Material | Role |
|---|---|
| Sepsis 27 / 36 / 51 | Primary MIMIC behavioral references |
| Stanford 26 / 36 / 50 | Local diagnostic reference learning |
| Saved MIMIC action-curve evaluation | Held-out action-probability assessment; see the sepsis illustration |
| `results/sepsis_primary/` | Primary confusion/action counts, action-probability estimates and intervals, and fixed-candidate R sensitivity |
| `results/*/validation_v1/` | Patient-disjoint secondary disease analyses, with declared primary and sensitivity response definitions |
| `results/cross_disease_validation_v1/` | Combined summaries, configuration, and provenance for those secondary analyses |
| Earlier compatibility and R-tier reports | Software/analysis development records; see their stated settings |

The current secondary-disease configuration is
`configs/cross_disease_validation_v1.yaml`. It declares the split, bootstrap,
response components, sensitivity analyses, capacity fractions, and a shared
low-confidence R scenario. Its results support analysis of procedural portability
and threshold-level performance; clinical utility requires additional evaluation.

## Reproduce an analysis

For the primary paper results, begin with the [paper reproduction guide](paper-reproduction.md).
`python examples/reproduce_paper.py` rebuilds the shared aggregate tables without
clinical data. `examples/sepsis_paper_analysis.py` provides the explicit Low-based
selection and held-out evaluation recipe for authorized analysis tables.

The synthetic example is fully self-contained. Clinical runners require separately
authorized datasets with the specified schema:

```bash
python examples/publication_validation.py --help
python examples/disease_compatibility.py --help
python examples/sepsis_v7_integration.py --help
```

The earlier V7 entry point is a reference-value regression check. It does not
reproduce the complete primary operating and action-probability analyses.

Review the configuration and data lineage before running an analysis. The repository
does not distribute patient-level input files.

## Provenance

Saved result metadata includes settings and input/output checksums. In the public
copy, personal filesystem paths have been replaced with portable placeholders.
The cross-disease manifest retains original output hashes and separately records
the hashes of the public copies. Clinical result values have not been changed.

Earlier reports retain their historical context. For current API behavior, use the
[reference guide](references.md) and executable package. For example, an unreachable
absolute Mid/High target may use a labeled relative target, subject to ordering;
a historical report describing an unavailable High should not be generalized into
a rule that every unreachable 80% target must abstain.
