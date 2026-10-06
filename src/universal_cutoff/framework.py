from typing import Optional

import pandas as pd

from .bootstrap import bootstrap_module2
from .config import BootstrapConfig, CapacityConfig, CostConfig, Module2Config
from .module1 import evaluate_score
from .module2 import fit_behavior_thresholds
from .module3a import apply_capacity
from .module3b import audit_cost_governance
from .results import FrameworkResult
from .threshold_table import build_threshold_table
from .validation import binary_series


def run_framework(data: pd.DataFrame, score_col: str, response_col: Optional[str] = None,
                  outcome_col: Optional[str] = None, module2: Optional[Module2Config] = None,
                  capacity: Optional[CapacityConfig] = None,
                  cost: Optional[CostConfig] = None,
                  bootstrap: Optional[BootstrapConfig] = None) -> FrameworkResult:
    validation, calibrator = evaluate_score(data, score_col, outcome_col)
    if response_col:
        response = binary_series(data[response_col], response_col)
        validation.update(
            N_response_complete=int(response.notna().sum()),
            N_response_missing=int(response.isna().sum()),
            response_prevalence=float(response.mean()) if response.notna().any() else None,
        )
    behavior = fit_behavior_thresholds(data, score_col, response_col, module2) if response_col else None
    bootstrap_result = (
        bootstrap_module2(data, score_col, response_col, module2, bootstrap, behavior)
        if response_col and bootstrap is not None else None
    )
    thresholds = build_threshold_table(data, score_col, response_col, outcome_col)
    capacity_result = apply_capacity(thresholds, behavior.anchors, capacity) if capacity and behavior else None
    cost_result = None
    if cost and cost.enabled:
        if outcome_col is None:
            raise ValueError("Module 3B requires outcome_col")
        if behavior is None:
            raise ValueError("Module 3B workflow requires behavior thresholds or direct audit call")
        representatives = behavior.anchors[behavior.anchors.operational_representative]
        if len(representatives):
            threshold = float(representatives.sort_values("selection_priority").iloc[0].selected_threshold)
            cost_result = audit_cost_governance(thresholds, threshold, cost.R, calibrator)
    return FrameworkResult(validation, behavior, thresholds, capacity_result, cost_result, bootstrap_result)
