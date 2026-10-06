from typing import Optional

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from .validation import binary_series, numeric_series, validate_columns


def evaluate_score(data: pd.DataFrame, score_col: str, outcome_col: Optional[str] = None):
    validate_columns(data, [score_col, outcome_col])
    score = numeric_series(data[score_col])
    result = {"N_input": int(len(data)), "N_valid_score": int(score.notna().sum()),
              "N_missing_score": int(score.isna().sum())}
    if outcome_col is None:
        return result, None
    outcome = binary_series(data[outcome_col], outcome_col)
    complete = score.notna() & outcome.notna()
    x, y = score[complete].to_numpy(float), outcome[complete].to_numpy(int)
    result.update(N_outcome_complete=int(len(y)), prevalence=float(y.mean()) if len(y) else np.nan)
    if len(np.unique(y)) == 2:
        result.update(AUROC=float(roc_auc_score(y, x)), AUPRC=float(average_precision_score(y, x)))
        calibrator = IsotonicRegression(y_min=0, y_max=1, out_of_bounds="clip").fit(x, y)
        probability = calibrator.predict(x)
        result["Brier"] = float(brier_score_loss(y, probability))
        logit_probability = np.log(np.clip(probability, 1e-6, 1 - 1e-6) /
                                   (1 - np.clip(probability, 1e-6, 1 - 1e-6)))
        calibration = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000)
        calibration.fit(logit_probability.reshape(-1, 1), y)
        result["calibration_intercept"] = float(calibration.intercept_[0])
        result["calibration_slope"] = float(calibration.coef_[0, 0])
        result["calibration_role"] = "apparent_in_sample"
    else:
        result.update(AUROC=np.nan, AUPRC=np.nan, Brier=np.nan,
                      calibration_intercept=np.nan, calibration_slope=np.nan,
                      calibration_role="unavailable_single_outcome_class")
        calibrator = None
    return result, calibrator
