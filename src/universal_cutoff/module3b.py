from typing import Any, Optional

import numpy as np
import pandas as pd

from .results import (CostAuditResult, LambdaResult, MinimaxRegretResult,
                      ThresholdTableResult)
from .threshold_table import threshold_row


MODULE2_OWNED_FIELDS = {"level", "selected_threshold", "anchor_name", "provenance_tier"}


def _select_minimum(table):
    minimum = float(table.cost_FAE.min())
    tied = table[np.isclose(table.cost_FAE, minimum, atol=1e-12, rtol=0)]
    return tied.sort_values(["alert_count", "threshold"], ascending=[False, True]).iloc[0]


def _predict(calibrator: Any, threshold: float):
    if hasattr(calibrator, "predict"):
        value = calibrator.predict([float(threshold)])
    else:
        value = calibrator([float(threshold)])
    return float(np.asarray(value).reshape(-1)[0])


def lambda_fae_at_threshold(threshold: float, calibrator: Any, R: float,
                            binding: bool, marginal_reference: str = "selected_boundary") -> LambdaResult:
    if not binding:
        return LambdaResult(0.0, None, "available_nonbinding",
                            "capacity is nonbinding; marginal capacity value is zero")
    if calibrator is None:
        return LambdaResult(None, None, "unavailable_missing_calibrator",
                            "binding audit has no outcome calibrator; zero would be misleading")
    try:
        p_m = _predict(calibrator, threshold)
    except Exception as exc:
        return LambdaResult(None, None, "unavailable_invalid_calibration",
                            "boundary prediction failed: {!r}".format(exc))
    if not np.isfinite(p_m) or p_m < 0 or p_m > 1:
        return LambdaResult(None, None, "unavailable_invalid_calibration",
                            "boundary prediction must lie in [0,1]")
    value = max(0.0, p_m * float(R) - (1 - p_m))
    return LambdaResult(float(value), float(p_m), "available_binding",
                        "threshold-level marginal-value proxy at {}".format(marginal_reference))


def _near_region(table, optimum_cost, policy_n):
    tolerances = {"abs1_FAE_per_1000": policy_n / 1000.0,
                  "abs5_FAE_per_1000": 5 * policy_n / 1000.0,
                  "rel1pct": 0.01 * abs(float(optimum_cost))}
    result = {}
    for name, epsilon in tolerances.items():
        region = table[table.cost_FAE - optimum_cost <= epsilon + 1e-12]
        result[name + "_threshold_min"] = float(region.threshold.min())
        result[name + "_threshold_max"] = float(region.threshold.max())
        result[name + "_strategy_N"] = int(len(region))
    return result


def audit_cost_governance(thresholds: ThresholdTableResult, behavior_threshold: float,
                          R: float, calibrator: Optional[Any] = None) -> CostAuditResult:
    if R <= 0:
        raise ValueError("R must be positive")
    required = {"FP", "FN", "alert_count"}
    if not required.issubset(thresholds.table.columns):
        raise ValueError("Outcome is required for Module 3B")
    sweep = thresholds.table.copy()
    sweep["R"] = float(R)
    sweep["cost_FAE"] = sweep.FP + float(R) * sweep.FN
    sweep["cost_FAE_per_1000"] = sweep.cost_FAE / thresholds.policy_N * 1000
    behavior = threshold_row(sweep, behavior_threshold)
    constrained_table = sweep[sweep.alert_count <= int(behavior.alert_count)]
    constrained = _select_minimum(constrained_table)
    unconstrained = _select_minimum(sweep)
    binding = bool(int(unconstrained.alert_count) > int(behavior.alert_count))
    same = np.isclose(behavior.threshold, constrained.threshold)
    if binding:
        classification = "budget_bound_retention" if same else "budget_bound_cost_discordance"
    else:
        classification = "nonbinding_exact_alignment" if same else "nonbinding_cost_discordance"
    lambda_result = lambda_fae_at_threshold(float(behavior.threshold), calibrator, R, binding)
    summary = {
        "R": float(R), "behavior_threshold": float(behavior_threshold),
        "behavior_operational_threshold": float(behavior.threshold),
        "behavior_alert_count": int(behavior.alert_count),
        "same_or_lower_workload_threshold": float(constrained.threshold),
        "same_or_lower_workload_alert_count": int(constrained.alert_count),
        "unconstrained_comparator_threshold": float(unconstrained.threshold),
        "unconstrained_comparator_alert_count": int(unconstrained.alert_count),
        "capacity_binding": binding, "audit_classification": classification,
        "behavior_threshold_role": "frozen Module 2 input",
        "same_or_lower_workload_threshold_role": "Module 3B comparator only",
        "unconstrained_threshold_role": "Module 3B comparator only",
        "module2_separation_guard": (
            "Module 3B cannot create, rename, replace, or mutate Low/Mid/High; comparator thresholds remain tier D."
        ),
        "behavior_excess_FAE": float(behavior.cost_FAE - constrained.cost_FAE),
        "interpretation_guard": ("budget-bound retention is not independent cost optimality"
                                 if classification == "budget_bound_retention"
                                 else "conditional retrospective comparator; not a clinical optimum"),
    }
    summary.update({"constrained_near_" + k: v for k, v in
                    _near_region(constrained_table, constrained.cost_FAE, thresholds.policy_N).items()})
    summary.update({"unconstrained_near_" + k: v for k, v in
                    _near_region(sweep, unconstrained.cost_FAE, thresholds.policy_N).items()})
    overlap = MODULE2_OWNED_FIELDS.intersection(summary)
    if overlap:
        raise RuntimeError("Module 3B attempted to emit Module 2-owned fields: {}".format(sorted(overlap)))
    return CostAuditResult(summary, sweep, lambda_result)


def minimax_regret_cost_audit(thresholds: ThresholdTableResult, R_grid,
                              max_alert_count: Optional[int] = None) -> MinimaxRegretResult:
    """Secondary comparator. Not an estimate of R and not a Module 2 threshold."""
    required = {"threshold", "FP", "FN", "alert_count"}
    if not required.issubset(thresholds.table.columns):
        raise ValueError("Outcome is required for minimax regret")
    values = np.asarray(list(R_grid), dtype=float)
    if values.size == 0 or np.any(~np.isfinite(values)) or np.any(values <= 0):
        raise ValueError("R_grid must contain finite positive values")
    values = np.unique(values)
    feasible = thresholds.table.copy()
    if max_alert_count is not None:
        if (isinstance(max_alert_count, bool) or int(max_alert_count) != max_alert_count
                or max_alert_count < 0):
            raise ValueError("max_alert_count must be a nonnegative integer")
        feasible = feasible[feasible.alert_count <= int(max_alert_count)].copy()
    if feasible.empty:
        raise ValueError("no threshold strategy satisfies max_alert_count")

    cost = (feasible.FP.to_numpy(float)[:, None]
            + feasible.FN.to_numpy(float)[:, None] * values[None, :])
    regret = cost - cost.min(axis=0, keepdims=True)
    summary = feasible[["threshold", "alert_count", "FP", "FN"]].reset_index(drop=True)
    summary["maximum_regret_FAE"] = regret.max(axis=1)
    summary["mean_regret_FAE"] = regret.mean(axis=1)
    summary["worst_case_R"] = values[np.argmax(regret, axis=1)]
    ordered = summary.sort_values(
        ["maximum_regret_FAE", "mean_regret_FAE", "alert_count", "threshold"],
        ascending=[True, True, True, False],
    )
    selected = ordered.iloc[0]
    matrix = pd.DataFrame(regret, columns=["R={:g}".format(x) for x in values])
    matrix.insert(0, "threshold", feasible.threshold.to_numpy(float))
    return MinimaxRegretResult(
        selected_threshold=float(selected.threshold),
        selected_alert_count=int(selected.alert_count),
        maximum_regret_FAE=float(selected.maximum_regret_FAE),
        maximum_regret_FAE_per_1000=float(
            selected.maximum_regret_FAE / thresholds.policy_N * 1000
        ),
        status="secondary_minimax_regret_comparator",
        R_grid=values.tolist(),
        strategy_summary=summary,
        regret_matrix=matrix,
    )
