# Contributing

Use a separate branch and include a small, reproducible example in a pull request.
For software defects, synthetic inputs are preferred. Keep patient-level data,
credentials, and private data paths out of issues, notebooks, and commits.

## Local checks

```bash
python -m pip install -e ".[test]"
python -m pip install -r requirements-docs.txt build
python -m pytest
python examples/synthetic_walkthrough.py
python scripts/check_publication.py
python -m mkdocs build --strict
python -m build
```

Changes to score orientation, action definitions, time windows, reference semantics,
or candidate selection should explain the scientific effect and include a separate
results comparison. Documentation changes should preserve the distinction between
behavioral references, capacity-adjusted candidates, and outcome evaluation.

## Documentation and figures

Edit Markdown under `docs/`, and update the navigation in `mkdocs.yml`. Preview with
`python -m mkdocs serve`. Figures use R/grid and committed aggregate inputs:

```bash
Rscript scripts/build_figures.R
```

See [figure provenance](docs/figures.md) for sources and interpretation. Commit the
R sources and regenerated PNG, SVG, and PDF together. The figure guide includes R
dependency installation and synthetic-data regeneration. Inspect the complete
figure and separate panels in `output/figures/`; keep QA files there and site builds
in the ignored `site/` directory.

The Pages workflow publishes only from `main`, after review and merge. Other
branches run validation without replacing the public documentation site.
