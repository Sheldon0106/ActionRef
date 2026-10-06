# Build and check the repository

Use Python 3.11 or newer for documentation. Figure drawing uses R 4.4 or newer;
see [figure reproduction](figures.md) for its separate dependencies.

```bash
python -m pip install -e ".[test]"
python -m pip install -r requirements-docs.txt build
python -m pytest
python examples/synthetic_walkthrough.py
python examples/reference_states.py
python examples/reproduce_paper.py
Rscript scripts/build_figures.R
python scripts/check_publication.py
python -m mkdocs build --strict
python -m build
```

The public-repository check inspects local Markdown links, private path patterns,
likely credential patterns, aggregate CSV headers, and figure-source checksums.
It complements review of the content; it does not certify clinical validity.

The CI workflow runs package tests, the synthetic example, the documentation build,
the aggregate paper reproduction and the repository check. The documentation
deployment workflow publishes from `main`.

Software tests use synthetic encounters and the shared aggregate data. The
clinical runner's `--verify-reported` option checks concordance with the reported
analysis when the specified authorized tables are supplied.

Package source and analytical configurations retain their own versioning.
Documentation and figures can be revised without changing the scientific defaults.
