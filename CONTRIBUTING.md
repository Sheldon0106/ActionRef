# Contributing

Use a separate branch and describe the change in a pull request. Software bug
reports should include a small synthetic example. Keep clinical records,
credentials and private paths out of commits and issues.

## Checks

```bash
python -m pip install -e ".[test,research]" -r requirements-docs.txt build
python -m pytest
python examples/synthetic_walkthrough.py
python examples/reference_states.py
python examples/reproduce_paper.py --early-warning-scores
python examples/reproduce_extended.py
python scripts/check_publication.py
python -m mkdocs build --strict
python -m build
```

Tests cover method behavior, synthetic inputs and shared aggregate results.
Changes to action definitions, reference semantics or candidate selection should
explain their scientific effect. Source data and analysis configurations should
remain consistent with the study.

## Documentation

Edit the Markdown files in `docs/` and update `mkdocs.yml` when navigation changes.
Preview the site with `python -m mkdocs serve`. GitHub Pages publishes from `main`.

The software workflow and synthetic tutorial illustrations use R/grid. With R 4.4
or newer and `jsonlite`, `svglite` and `ragg` installed, run
`Rscript scripts/build_figures.R`. Use `--workflow-only` to update just the software
diagram. Inspect exports before committing the corresponding R sources and images.
