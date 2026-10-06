# Governance diagnostic contracts

These utilities evaluate a fixed threshold policy. They do not learn replacements for frozen thresholds.

## Subgroups

`audit_subgroups()` requires one role label:

- `primary_demographic`
- `exploratory_operational_proxy`
- `custom_descriptive`

Output per subgroup: frozen threshold, operationalization, alert burden, response/outcome metrics.

- Differences are descriptive. They may reflect prevalence or case mix.
- Operational or downstream variables (e.g. disposition-linked insurance coding) require the proxy role.
- They cannot be presented as a demographic effect.

## Time

`audit_temporal()` normalizes spaces, hyphen, Unicode dash, and minus in era ranges.

- `2011 - 2013` becomes `2011-2013`
- `2011–2013` becomes `2011-2013`

- With `subject_col`, output reports subjects appearing in more than one era.
- Frozen metrics are reported by era.
- Optional local Module 2 estimates are labeled `local_diagnostic_reestimation`.
- Those are point diagnostics, not significance tests. They cannot mutate frozen thresholds.

## Transport

`audit_transport()` returns two tables:

- `frozen_performance`, labeled `frozen_transport_evaluation`
- `local_diagnostic_thresholds`, labeled `local_diagnostic_reestimation`, when requested

Rules:

- A local diagnostic estimate cannot replace the transported threshold unless the study declares a new local implementation.
- Capacity operationalization is a separate Module 3A step and preserves semantic provenance.
