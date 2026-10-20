# Paired support-gate simulation

Manuscript locations: **eTable 14C; eFigure 6**.

The existing [runner](runner.py), [configuration](config.json) and
[condition error summaries](condition_error_summary.csv) retain seed **2026101101**.
No simulations or analyses were rerun. The [manifest](manifest.json) identifies
byte-identical source copies using portable labels and SHA-256 hashes.

## Checks against the final manuscript

Seven scenarios use sample sizes 6,000 and 2,000, with 200 datasets per condition.
In the 6,000-row flat-null condition, default output is 0% at all three levels;
removing support criteria gives 95.5%, 76.0% and 100.0% output at Low, Mid and High.
These are synthetic aggregates, with no clinical records or identifiers.
