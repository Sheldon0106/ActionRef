# ActionRef

ActionRef is a Python package for estimating practice-based reference thresholds
for existing clinical scores. It relates scores to recorded clinical actions,
then supports threshold comparisons under specified workload and consequence
assumptions.

The package provides score assessment, reference estimation, capacity mapping,
and optional consequence analysis. References describe recorded practice;
operating candidates are evaluated separately for alert burden, action yield,
and outcome coverage.

[Documentation](https://Sheldon0106.github.io/ActionRef/) ·
[API](docs/API_REFERENCE.md) · [MIT license](LICENSE)

![ActionRef workflow: prepare inputs, estimate references, compare candidates and evaluate on separate data.](docs/assets/figures/workflow.png)

## Installation

Python 3.8 or newer is required. The distribution is named `universal-cutoff`
and the Python import is `universal_cutoff`.

```bash
git clone https://github.com/Sheldon0106/ActionRef.git
cd ActionRef
python -m pip install -e .
```

## Quick start

Run the synthetic example without clinical data:

```bash
python examples/synthetic_walkthrough.py --output-dir output/synthetic
```

It estimates references, applies an alert budget, and evaluates the resulting
thresholds on separate synthetic encounters. See the
[walkthrough](docs/quickstart.md) for inputs and outputs.

To use your own prepared data:

```python
from universal_cutoff import fit_behavior_thresholds, evaluate_frozen_thresholds

references = fit_behavior_thresholds(derivation, "score", "response")
print(references.anchors)

if references.anchors.selected_threshold.notna().any():
    evaluation = evaluate_frozen_thresholds(
        validation, "score", references.anchors,
        response_col="response", outcome_col="outcome",
    )
    print(evaluation.table)
```

## Inputs and outputs

Supply one row per encounter, a numeric score, and a binary recorded-action
label. An outcome label enables outcome evaluation and consequence analysis.
Define action windows and missingness before fitting, and split repeated
encounters by patient. See [data preparation](docs/data.md).

Outputs include the estimated action curve, supported Low/Mid/High references,
capacity-adjusted candidates, and evaluation summaries. Partial or unavailable
references are valid outputs. The [method guide](docs/references.md) explains
these states; the [K/R guide](docs/R_GUIDANCE.md) describes workload and
consequence inputs.

## Study materials and data access

The accompanying study, *ActionRef: Learning Reference Thresholds and Guiding
Clinical Risk Threshold Selection*, evaluates ESRP and four early warning
scores for emergency sepsis assessment at BIDMC and Stanford.

Analysis scripts, configurations, simulations, and aggregate results are
provided in this repository. [Study materials](docs/paper-reproduction.md)
describes the available analyses and input requirements. Clinical records
must be obtained separately through authorized
[PhysioNet access](https://physionet.org/). The public examples use synthetic
data; no patient records or identifiers are distributed.

## Repository

| Directory | Contents |
|---|---|
| [src/universal_cutoff](src/universal_cutoff/) | Python implementation |
| [examples](examples/) | Synthetic examples and sepsis analysis |
| [configs](configs/) | Analysis and illustration settings |
| [simulations](simulations/README.md) | Simulation runners and summaries |
| [results](results/) | Aggregate study results |
| [docs](docs/index.md) | Usage and method documentation |
| [tests](tests/) | Software and aggregate-result checks |

## Citation and development

Citation metadata are provided in [CITATION.cff](CITATION.cff). Please also cite
the source datasets when using the clinical analysis materials.

For installation checks and contributions, see [Contributing](CONTRIBUTING.md).
Questions and problems can be reported through
[GitHub Issues](https://github.com/Sheldon0106/ActionRef/issues).
