from typing import Iterable, Optional

import numpy as np
import pandas as pd

from .exceptions import InputValidationError


def numeric_series(values):
    return pd.to_numeric(values, errors="coerce")


def binary_series(values, name="value"):
    out = numeric_series(values)
    observed = set(out.dropna().unique().tolist())
    if not observed.issubset({0, 1}):
        raise InputValidationError("{} must be binary 0/1; observed {}".format(name, sorted(observed)))
    return out


def validate_columns(data: pd.DataFrame, required: Iterable[Optional[str]]):
    missing = [x for x in required if x is not None and x not in data.columns]
    if missing:
        raise InputValidationError("Missing required columns: {}".format(missing))


def validate_score(data: pd.DataFrame, score_col: str, encounter_id: Optional[str] = None):
    validate_columns(data, [score_col, encounter_id])
    score = numeric_series(data[score_col])
    valid = score.dropna()
    if valid.empty:
        raise InputValidationError("No valid numeric scores")
    if not np.isfinite(valid.to_numpy(float)).all():
        raise InputValidationError("Scores must be finite")
    if encounter_id and data[encounter_id].dropna().duplicated().any():
        raise InputValidationError("encounter_id must be unique when supplied")
    return {
        "N_input": int(len(data)),
        "N_valid_score": int(valid.size),
        "N_missing_score": int(score.isna().sum()),
        "unique_scores": int(valid.nunique()),
        "score_min": float(valid.min()),
        "score_max": float(valid.max()),
    }

