from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import pandas as pd


@dataclass
class Module2Result:
    input_summary: Dict[str, Any]
    binning: Dict[str, Any]
    response_curve: pd.DataFrame
    evidence_gate: Dict[str, Any]
    structural_candidates: pd.DataFrame
    supported_changepoints: pd.DataFrame
    anchors: pd.DataFrame
    config: Dict[str, Any]
    isotonic_model: Any = field(repr=False, default=None)


@dataclass
class ThresholdTableResult:
    table: pd.DataFrame
    policy_N: int


@dataclass
class CapacityResult:
    table: pd.DataFrame
    K: int
    K_fraction: float


@dataclass
class LambdaResult:
    value: Optional[float]
    boundary_risk: Optional[float]
    status: str
    reason: str


@dataclass
class CostAuditResult:
    summary: Dict[str, Any]
    cost_sweep: pd.DataFrame
    lambda_result: LambdaResult


@dataclass
class MinimaxRegretResult:
    selected_threshold: float
    selected_alert_count: int
    maximum_regret_FAE: float
    maximum_regret_FAE_per_1000: float
    status: str
    R_grid: list
    strategy_summary: pd.DataFrame
    regret_matrix: pd.DataFrame
    interpretation_guard: str = (
        "Secondary Module 3B comparator only; cannot define, relabel, or replace Low/Mid/High."
    )


@dataclass
class FrozenThresholdDiagnosticResult:
    table: pd.DataFrame
    frozen_thresholds: Dict[str, float]
    interpretation_guard: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TemporalDiagnosticResult:
    frozen_performance: pd.DataFrame
    local_diagnostic_thresholds: pd.DataFrame
    era_mapping: pd.DataFrame
    overlap_audit: Dict[str, Any]
    config: Dict[str, Any]
    interpretation_guard: str


@dataclass
class TransportDiagnosticResult:
    frozen_performance: pd.DataFrame
    local_diagnostic_thresholds: pd.DataFrame
    status: Dict[str, str]
    interpretation_guard: str


@dataclass
class BootstrapResult:
    status: str
    anchors: pd.DataFrame
    validated_full_anchors: pd.DataFrame
    stability_summary: pd.DataFrame
    threshold_frequencies: pd.DataFrame
    joint_tier_audit: pd.DataFrame
    joint_summary: Dict[str, Any]
    adjacent_gap_summary: pd.DataFrame
    provenance_frequencies: pd.DataFrame
    binning_stability: pd.DataFrame
    changepoint_support: pd.DataFrame
    failures: pd.DataFrame
    config: Dict[str, Any]


@dataclass
class FrameworkResult:
    validation: Dict[str, Any]
    module2: Optional[Module2Result]
    threshold_table: ThresholdTableResult
    capacity: Optional[CapacityResult]
    cost_audit: Optional[CostAuditResult]
    bootstrap: Optional[BootstrapResult] = None
