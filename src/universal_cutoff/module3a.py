import numpy as np
import pandas as pd

from .config import CapacityConfig
from .results import CapacityResult, ThresholdTableResult
from .threshold_table import threshold_row


def apply_capacity(thresholds: ThresholdTableResult, anchors: pd.DataFrame,
                   capacity: CapacityConfig) -> CapacityResult:
    table = thresholds.table
    k = min(int(capacity.K), thresholds.policy_N)
    feasible = table[table.alert_count <= k].sort_values(["threshold", "alert_count"], ascending=[True, False])
    floor = feasible.iloc[0]
    rows = []
    for _, anchor in anchors.iterrows():
        nominal = anchor.get("selected_threshold", np.nan)
        base = {"level": anchor["level"], "semantic_provenance_tier": anchor.get("provenance_tier"),
                "K_absolute": k, "K_fraction": k / float(thresholds.policy_N),
                "capacity_period": capacity.period, "capacity_floor": float(floor.threshold)}
        if not np.isfinite(nominal):
            base.update(status="unavailable_behavior_threshold", nominal_threshold=np.nan,
                        operational_threshold=np.nan, adjusted_alert_count=np.nan,
                        reason="behavior threshold unavailable; capacity cannot create one")
            rows.append(base); continue
        nominal_row = threshold_row(table, float(nominal))
        adjusted_row = threshold_row(table, max(float(nominal), float(floor.threshold)))
        adjusted = not np.isclose(nominal_row.threshold, adjusted_row.threshold)
        base.update(status="adjusted" if adjusted else "not_adjusted",
                    nominal_threshold=float(nominal),
                    nominal_operational_threshold=float(nominal_row.threshold),
                    nominal_alert_count=int(nominal_row.alert_count),
                    operational_threshold=float(adjusted_row.threshold),
                    adjusted_alert_count=int(adjusted_row.alert_count),
                    adjusted_alert_fraction=float(adjusted_row.alert_fraction),
                    adjusted=bool(adjusted),
                    interpretation_guard="capacity changes operational threshold only; semantic provenance is preserved")
        for name in ["response_count", "response_yield", "TP", "FP", "FN", "TN", "recall", "specificity", "PPV", "NPV", "missed_cases"]:
            if name in adjusted_row.index:
                base[name] = adjusted_row[name]
        rows.append(base)
    return CapacityResult(pd.DataFrame(rows), k, k / float(thresholds.policy_N))

