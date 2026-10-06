import re
from dataclasses import asdict
from typing import Dict, Optional

import numpy as np
import pandas as pd

from .config import Module2Config
from .exceptions import InputValidationError
from .module2 import fit_behavior_thresholds
from .results import (FrozenThresholdDiagnosticResult, TemporalDiagnosticResult,
                      TransportDiagnosticResult)
from .threshold_table import build_threshold_table, threshold_row
from .validation import validate_columns


SUBGROUP_ROLES = {
    "primary_demographic",
    "exploratory_operational_proxy",
    "custom_descriptive",
}


def _threshold_mapping(frozen_thresholds) -> Dict[str, float]:
    if isinstance(frozen_thresholds, dict):
        source = frozen_thresholds
    elif isinstance(frozen_thresholds, pd.DataFrame):
        if not {"level", "selected_threshold"}.issubset(frozen_thresholds.columns):
            raise InputValidationError(
                "frozen threshold table requires level and selected_threshold columns"
            )
        source = dict(zip(frozen_thresholds.level, frozen_thresholds.selected_threshold))
    else:
        raise InputValidationError("frozen_thresholds must be a mapping or anchor table")
    result = {}
    for name, value in source.items():
        numeric = float(value)
        if np.isfinite(numeric):
            result[str(name)] = numeric
    if not result:
        raise InputValidationError("no finite frozen thresholds were supplied")
    return result


def evaluate_frozen_thresholds(data: pd.DataFrame, score_col: str, frozen_thresholds,
                               response_col: Optional[str] = None,
                               outcome_col: Optional[str] = None) -> FrozenThresholdDiagnosticResult:
    frozen = _threshold_mapping(frozen_thresholds)
    table = build_threshold_table(data, score_col, response_col, outcome_col)
    rows = []
    for level, requested in frozen.items():
        selected = threshold_row(table.table, requested)
        row = {
            "level": level,
            "frozen_threshold": float(requested),
            "evaluated_threshold": float(selected.threshold),
            "threshold_was_observed": bool(np.isclose(selected.threshold, requested)),
        }
        for column in [
                "policy_N", "alert_count", "alert_fraction", "alerts_per_1000",
                "response_count", "response_yield", "TP", "FP", "FN", "TN",
                "recall", "specificity", "PPV", "NPV", "missed_cases"]:
            if column in selected.index:
                row[column] = selected[column]
        rows.append(row)
    return FrozenThresholdDiagnosticResult(
        table=pd.DataFrame(rows),
        frozen_thresholds=frozen,
        interpretation_guard=(
            "Frozen operating evaluation only; these results cannot move, rename, or replace "
            "the supplied Module 2 thresholds."
        ),
    )


def audit_subgroups(data: pd.DataFrame, score_col: str, frozen_thresholds,
                    subgroup_col: str, response_col: Optional[str] = None,
                    outcome_col: Optional[str] = None,
                    subgroup_role: str = "primary_demographic") -> FrozenThresholdDiagnosticResult:
    if subgroup_role not in SUBGROUP_ROLES:
        raise InputValidationError("unsupported subgroup_role")
    validate_columns(data, [score_col, subgroup_col, response_col, outcome_col])
    frozen = _threshold_mapping(frozen_thresholds)
    pieces = []
    for value, group in data[data[subgroup_col].notna()].groupby(subgroup_col, sort=True):
        evaluated = evaluate_frozen_thresholds(
            group, score_col, frozen, response_col=response_col, outcome_col=outcome_col)
        part = evaluated.table.copy()
        part.insert(0, "subgroup", value)
        part.insert(1, "subgroup_N", int(len(group)))
        pieces.append(part)
    table = pd.concat(pieces, ignore_index=True, sort=False) if pieces else pd.DataFrame()
    role_guard = {
        "primary_demographic": "Primary demographic audit; differences remain descriptive.",
        "exploratory_operational_proxy": (
            "Exploratory operational or downstream proxy; do not interpret as a demographic effect."
        ),
        "custom_descriptive": "Custom descriptive grouping; no prescriptive subgroup threshold is created.",
    }[subgroup_role]
    return FrozenThresholdDiagnosticResult(
        table=table,
        frozen_thresholds=frozen,
        context={"subgroup_col": subgroup_col, "subgroup_role": subgroup_role},
        interpretation_guard=(
            role_guard + " Differences may reflect prevalence and case mix and cannot automatically "
            "create subgroup-specific treatment recommendations or mutate frozen thresholds."
        ),
    )


def normalize_era(value):
    if pd.isna(value):
        return None
    text = str(value).strip()
    text = re.sub(r"[\u2010\u2011\u2012\u2013\u2014\u2212]", "-", text)
    text = re.sub(r"\s*-\s*", "-", text)
    text = re.sub(r"\s+", " ", text)
    return text


def audit_temporal(data: pd.DataFrame, score_col: str, frozen_thresholds,
                   era_col: str, response_col: Optional[str] = None,
                   outcome_col: Optional[str] = None,
                   subject_col: Optional[str] = None,
                   local_module2: bool = False,
                   module2: Optional[Module2Config] = None) -> TemporalDiagnosticResult:
    validate_columns(data, [score_col, era_col, response_col, outcome_col, subject_col])
    frozen = _threshold_mapping(frozen_thresholds)
    use = data.copy()
    use["_normalized_era"] = use[era_col].map(normalize_era)
    use = use[use._normalized_era.notna()].copy()
    frozen_pieces, local_pieces = [], []
    for era, group in use.groupby("_normalized_era", sort=True):
        evaluated = evaluate_frozen_thresholds(
            group, score_col, frozen, response_col=response_col, outcome_col=outcome_col)
        part = evaluated.table.copy()
        part.insert(0, "era", era)
        part.insert(1, "era_N", int(len(group)))
        frozen_pieces.append(part)
        if local_module2:
            if response_col is None:
                local_pieces.append({"era": era, "status": "unavailable_missing_response"})
            else:
                try:
                    local = fit_behavior_thresholds(group, score_col, response_col, module2)
                    for row in local.anchors.itertuples(index=False):
                        local_pieces.append({
                            "era": era,
                            "level": row.level,
                            "local_diagnostic_threshold": row.selected_threshold,
                            "provenance_tier": row.provenance_tier,
                            "status": "local_diagnostic_reestimation",
                        })
                except Exception as exc:
                    local_pieces.append({
                        "era": era,
                        "status": "unavailable_local_reestimation",
                        "reason": repr(exc),
                    })
    overlap = {"subject_col": subject_col, "cross_era_subject_count": None}
    if subject_col is not None:
        memberships = use.loc[use[subject_col].notna(), [subject_col, "_normalized_era"]].drop_duplicates()
        counts = memberships.groupby(subject_col)._normalized_era.nunique()
        overlap["cross_era_subject_count"] = int((counts > 1).sum())
        overlap["subjects_evaluated"] = int(len(counts))
    mapping = (use[[era_col, "_normalized_era"]].drop_duplicates()
               .rename(columns={era_col: "original_era", "_normalized_era": "normalized_era"}))
    return TemporalDiagnosticResult(
        frozen_performance=(pd.concat(frozen_pieces, ignore_index=True, sort=False)
                            if frozen_pieces else pd.DataFrame()),
        local_diagnostic_thresholds=pd.DataFrame(local_pieces),
        era_mapping=mapping.reset_index(drop=True),
        overlap_audit=overlap,
        config={"local_module2": bool(local_module2),
                "module2": asdict(module2 or Module2Config()) if local_module2 else None},
        interpretation_guard=(
            "Point-based temporal drift diagnostic. Local re-estimation is descriptive, is not a "
            "bootstrap significance claim, and cannot mutate the frozen primary thresholds."
        ),
    )


def audit_transport(target_data: pd.DataFrame, score_col: str, frozen_thresholds,
                    target_site: str, response_col: Optional[str] = None,
                    outcome_col: Optional[str] = None, local_module2: bool = False,
                    module2: Optional[Module2Config] = None) -> TransportDiagnosticResult:
    frozen = _threshold_mapping(frozen_thresholds)
    evaluated = evaluate_frozen_thresholds(
        target_data, score_col, frozen, response_col=response_col, outcome_col=outcome_col)
    local_table = pd.DataFrame()
    local_status = "not_requested"
    if local_module2:
        if response_col is None:
            local_status = "unavailable_missing_response"
        else:
            try:
                local = fit_behavior_thresholds(target_data, score_col, response_col, module2)
                local_table = local.anchors.copy()
                local_table.insert(0, "target_site", target_site)
                local_table["transport_role"] = "local_diagnostic_reestimation"
                local_status = "completed_local_diagnostic"
            except Exception as exc:
                local_status = "unavailable_local_reestimation: {!r}".format(exc)
    frozen_table = evaluated.table.copy()
    frozen_table.insert(0, "target_site", target_site)
    frozen_table["transport_role"] = "frozen_transport_evaluation"
    return TransportDiagnosticResult(
        frozen_performance=frozen_table,
        local_diagnostic_thresholds=local_table,
        status={"frozen": "completed", "local": local_status},
        interpretation_guard=(
            "Frozen transport and local diagnostic estimates are separate. Local re-estimation "
            "cannot replace transported thresholds unless a new local implementation study is declared."
        ),
    )
