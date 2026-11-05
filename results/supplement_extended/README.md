# Additional aggregate analyses

These summaries accompany the study and contain no clinical records or identifiers.

| File | Analysis |
|---|---|
| [minimax_regret.csv](minimax_regret.csv) | Six cohort-specific workload scenarios across a fixed consequence-ratio grid |
| [transfer_target_sensitivity.csv](transfer_target_sensitivity.csv) | Fixed-score, workload-matched, risk-matched and local-reference comparisons |
| [subgroup_diagnostics.csv](subgroup_diagnostics.csv) | Operating and calibration summaries by sex, age, race and insurance |
| [original_eight_scenarios.csv](original_eight_scenarios.csv) | Condition-level reference errors in the eight-scenario simulation |
| [conventional_selection_uncertainty.csv](conventional_selection_uncertainty.csv) | Threshold-selection uncertainty for six conventional rules |

The cohort-specific minimax and transfer scenarios address separate questions
from external evaluation of threshold 34, which was selected in the MIMIC
derivation set. Subgroup calibration entries are point estimates and repeat
across reference levels within each subgroup. Rule-selection uncertainty is
separate from operating uncertainty conditional on a fixed threshold.

The [simulation runner](../../simulations/eight_scenarios/runner.py) uses seed
20260802. The separate paired support-criteria simulation uses seed 2026101101.
See [study materials](../../docs/paper-reproduction.md) for the aggregate assembly
command and the [K/R guide](../../docs/R_GUIDANCE.md) for scenario inputs.
