# Saved operating intervals

Manuscript locations: **eTable 9C**.

These are saved fixed-threshold patient-cluster intervals. The saved paired 31-minus-27 FAE intervals are -29.0 to -13.3 in MIMIC and -57.0 to -42.3 in Stanford (rounded). They use 1,000 paired resamples; they are not derived from marginal intervals. Original source hashes match the precision-addendum outputs.

## Checks against the final manuscript

MIMIC fixed thresholds 27, 31, 36 and 51 are each evaluated with 1,000 requested resamples. At 31, FAE per 1,000 rounds to 478.51; at 27 it rounds to 499.67. Stanford at 31 rounds to 385.34.

## Sources

Existing aggregate outputs only. No patient records or identifiers are included.
Numbers and original data fields are preserved. No analyses were rerun.

The [manifest](manifest.json) records portable source labels, generation-date provenance,
row selections, and SHA-256 hashes for the originals and public copies.

- [operating_points.csv](operating_points.csv)
- [operating_summary.csv](operating_summary.csv)
- [paired_FAE_difference.json](paired_FAE_difference.json)
