from typing import Optional

import numpy as np
import pandas as pd

from .results import ThresholdTableResult
from .validation import binary_series, numeric_series, validate_columns


def build_threshold_table(data: pd.DataFrame, score_col: str,
                          response_col: Optional[str] = None,
                          outcome_col: Optional[str] = None) -> ThresholdTableResult:
    validate_columns(data, [score_col, response_col, outcome_col])
    columns = [x for x in [score_col, response_col, outcome_col] if x]
    d = data[columns].copy()
    d[score_col] = numeric_series(d[score_col])
    if response_col:
        d[response_col] = binary_series(d[response_col], response_col)
    if outcome_col:
        d[outcome_col] = binary_series(d[outcome_col], outcome_col)
    d = d[d[score_col].notna()].copy()
    if d.empty:
        raise ValueError("No valid scores")
    policy_n = int(len(d))
    aggregate = {"N_at_score": (score_col, "size")}
    if response_col:
        aggregate.update(response_at_score=(response_col, "sum"), response_observed=(response_col, "count"))
    if outcome_col:
        aggregate.update(outcome_at_score=(outcome_col, "sum"), outcome_observed=(outcome_col, "count"))
    table = d.groupby(score_col, as_index=False).agg(**aggregate).sort_values(score_col, ascending=False)
    table["alert_count"] = table.N_at_score.cumsum().astype(int)
    table["alert_fraction"] = table.alert_count / float(policy_n)
    table["alerts_per_1000"] = table.alert_fraction * 1000
    table["policy_N"] = policy_n
    if response_col:
        table["response_count"] = table.response_at_score.fillna(0).cumsum()
        table["response_nonmissing_alerts"] = table.response_observed.cumsum()
        table["response_yield"] = table.response_count / table.response_nonmissing_alerts.replace(0, np.nan)
    if outcome_col:
        outcome_n = int(d[outcome_col].notna().sum())
        positive_n = int(d[outcome_col].eq(1).sum())
        negative_n = outcome_n - positive_n
        table["TP"] = table.outcome_at_score.fillna(0).cumsum().astype(int)
        table["outcome_nonmissing_alerts"] = table.outcome_observed.cumsum().astype(int)
        table["FP"] = table.outcome_nonmissing_alerts - table.TP
        table["FN"] = positive_n - table.TP
        table["TN"] = negative_n - table.FP
        table["recall"] = table.TP / positive_n if positive_n else np.nan
        table["FNR"] = 1 - table.recall
        table["specificity"] = table.TN / negative_n if negative_n else np.nan
        table["PPV"] = table.TP / (table.TP + table.FP).replace(0, np.nan)
        table["NPV"] = table.TN / (table.TN + table.FN).replace(0, np.nan)
        table["missed_cases"] = table.FN
        table["outcome_N"] = outcome_n
        table["outcome_positive_N"] = positive_n
    table = table.rename(columns={score_col: "threshold"})
    observed = np.sort(d[score_col].unique().astype(float))
    step = float(np.min(np.diff(observed))) if len(observed) > 1 else 1.0
    zero = {column: np.nan for column in table.columns}
    zero.update(threshold=float(observed.max() + step), N_at_score=0, alert_count=0,
                alert_fraction=0.0, alerts_per_1000=0.0, policy_N=policy_n)
    if response_col:
        zero.update(response_count=0, response_nonmissing_alerts=0, response_yield=np.nan)
    if outcome_col:
        zero.update(TP=0, FP=0, FN=positive_n, TN=negative_n, recall=0.0, FNR=1.0,
                    specificity=1.0 if negative_n else np.nan, PPV=np.nan,
                    NPV=negative_n / outcome_n if outcome_n else np.nan,
                    missed_cases=positive_n, outcome_N=outcome_n, outcome_positive_N=positive_n)
    intermediates = ["response_at_score", "response_observed", "outcome_at_score", "outcome_observed"]
    table = table.drop(columns=[x for x in intermediates if x in table])
    table = pd.concat([table, pd.DataFrame([zero])], ignore_index=True)
    table = table.sort_values("threshold").reset_index(drop=True)
    return ThresholdTableResult(table=table, policy_N=policy_n)


def threshold_row(table: pd.DataFrame, threshold: float):
    exact = table[np.isclose(table.threshold.astype(float), float(threshold), atol=1e-10, rtol=0)]
    if len(exact):
        return exact.iloc[0]
    higher = table[table.threshold >= float(threshold) - 1e-10].sort_values("threshold")
    return higher.iloc[0] if len(higher) else table.sort_values("threshold").iloc[-1]

