# R guidance schema

`R = C_FN / C_FP` — modeled relative consequence of one missed outcome-positive case versus one false alert.

- Never estimated from prevalence.
- Never selected to favor a preferred cutoff.

## Primary route: natural-frequency elicitation

### Frame (required first)

`ElicitationFrame` enforces all four. `build_r_guidance` raises if a frequency elicitation omits them.

| Field | Question |
|---|---|
| `intended_action` | What action does crossing the threshold trigger? |
| `target_outcome` | What is the target outcome, as the score identifies it? |
| `stakeholder_perspective` | Whose perspective is being elicited? |
| `time_horizon` | Over what time horizon is the outcome assessed? |

### Trade-off question

```text
Suppose lowering the threshold identifies 1 additional patient who experiences Sepsis-3,
while also triggering clinical reassessment for 9 additional patients who do not
experience Sepsis-3. Considering the expected benefits, harms, workload, and a time
horizon of 6 hours, would you accept this tradeoff?
```

- No causal treatment effect is estimated.
- No patient is described as benefiting.
- No action is described as unnecessary.
- Field names follow the same rule: `additional_outcome_positive`, `additional_outcome_negative`, `accepted`.

### Point estimate

```text
R_primary = sqrt(R_largest_accepted * R_smallest_rejected)
```

- Accepted scenario sets the lower bound. Rejected sets the upper bound.
- Report as the geometric (log-scale) midpoint of the elicited switch interval.
- Not an estimate of the true R. `point_estimate_basis` states this in the output.
- The interval carries the uncertainty. The grid spans it.
- Confidence is forced to low whenever elicitation determines the primary value.

Example: accept 13, reject 19 → range `13`–`19`, primary `15.72`, `scenario_assumption`, low confidence.

### Unbracketed and inconsistent responses

Ladder: opens at 9. Tests 19 after an acceptance, 4 after a rejection. Then targets the geometric midpoint.

| `bracketing_status` | Condition | Result |
|---|---|---|
| `bracketed` | Accepted and rejected straddle R | Primary R, range, grid |
| `one_sided_lower` | All accepted | No primary R; warning gives the floor |
| `one_sided_upper` | All rejected | No primary R; warning gives the ceiling |
| `inconsistent` | Harder accepted, easier rejected | No primary R; warning requests review |

- Last three return `insufficient_basis`, `recommended_R_primary = None`.
- None raises.
- The ladder halts on `inconsistent`.

## Alternate routes

**Published-threshold tier recommender.** When Module 3B is required but no local
cost build or elicitation is available, `recommend_ratio()` offers a prespecified,
low-confidence scenario value from one of three decision tiers. The tier is chosen
from the consequence of a miss and the burden/risk of the triggered action, not from
the disease name. `ratio_invariance()` and `ratio_band_impact()` then test the tier
band on the local threshold-level confusion table. See
[`RATIO_RECOMMENDER_FINDINGS.md`](RATIO_RECOMMENDER_FINDINGS.md).

- It is not an estimate of the true R and does not establish clinical utility.
- Its invariance band is a discrete-grid sensitivity result, not a confidence interval.
- `1 + R` is a break-even threshold-odds interpretation, not empirical PPV or causal NNT.
- If local stakeholders are available, the framed natural-frequency route above remains
  the stronger setting-specific justification.
- Capacity-only Module 3A users do not need R.

**Independently valued consequences.** One commensurate unit across FN and FP. Mixed units and duplicate names rejected.

```text
R      = sum(FN components) / sum(FP components)
R_low  = sum(FN lower) / sum(FP upper)
R_high = sum(FN upper) / sum(FP lower)
```

**Elicited action threshold probability.** `p_t` = outcome probability at which the action becomes worthwhile.

```text
R      = (1 - p_t) / p_t
R_low  = (1 - p_high) / p_high
R_high = (1 - p_low) / p_low
```

- `p_t = 0.10` implies `R = 9`.
- This is an action threshold probability. Not a score threshold. Not a Low/Mid/High candidate.

**Direct R entry.** Available for prespecified analyses such as the sepsis `R=15` scenario.

## Outputs

Returns:

`recommended_R_primary`, `recommended_R_range`, `recommended_R_grid`,
`point_estimate_basis`, status, provenance, confidence, warnings, rationale

- Status values: `evidence_based`, `consensus_based`, `locally_costed`, `scenario_based`, `insufficient_basis`.
- Source types: expert elicitation, Delphi elicitation, published evidence, local costing, stakeholder preference, policy, scenario assumption.
- Module 3B decision-transition R values may extend the grid after primary and range are fixed. Out-of-range values excluded. They cannot change the primary R.

## Optional minimax regret

```text
loss(t, r)   = FP(t) + r * FN(t)
regret(t, r) = loss(t, r) - min_s loss(s, r)
```

- Selects the feasible threshold with the smallest maximum regret over a fixed R grid.
- Does not choose or estimate R.
- Cannot define, relabel, or replace Low/Mid/High.

## Safeguards

- Prevalence-based and threshold-tuned rationales rejected.
- Primary value without uncertainty bounds warns.
- Scenario assumptions set to low confidence.
- Currency interpretation requires both FP and FN monetary consequences independently defined.
- Expected binding capacity triggers the budget-bound-retention warning.
- K is context and binding audit only. It does not enter either R equation.
- R guidance is separate from Module 2. It cannot define, replace, or relabel Low/Mid/High.

## Method sources

- Vickers and Elkin 2006 — action threshold probability versus relative FP/FN harms.
- Pauker and Kassirer 1980 — testing and treatment thresholds.
- Bojke et al. 2021 — structured expert elicitation reference protocol.
- Soares et al. 2024 — ISPOR report; SHELF, Cooke, IDEA, modified Delphi, MRC.
- Valentine et al. 2023 — direct, threshold-technique, and discrete-choice methods gave materially different results.
- Manski 2007 — adaptive minimax-regret treatment choice.
- Hoffrage et al. 2015 — natural frequencies beat probability presentations.
- Jacobs et al. 2023 — no gold standard exists.
