import sys
from pathlib import Path

import numpy as np
import pandas as pd


EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
sys.path.insert(0, str(EXAMPLES))

from publication_validation import (  # noqa: E402
    deterministic_patient_split,
    fixed_threshold_patient_bootstrap,
)


def test_shared_patient_split_is_order_independent_and_disjoint():
    subjects = pd.Series([9, 2, 5, 2, 1, 8, 4, 7, 3, 6])
    first = deterministic_patient_split(subjects, learning_fraction=0.70, seed=2026)
    second = deterministic_patient_split(subjects.sample(frac=1, random_state=9),
                                         learning_fraction=0.70, seed=2026)
    assert first == second
    learning = {key for key, value in first.items() if value == "learning"}
    heldout = {key for key, value in first.items() if value == "heldout"}
    assert len(learning) == 6
    assert learning.isdisjoint(heldout)
    assert learning | heldout == set(subjects)


def test_fixed_threshold_bootstrap_is_grouped_deterministic_and_frozen():
    data = pd.DataFrame({
        "subject_id": np.repeat(np.arange(20), 2),
        "score": np.tile([0.0, 2.0], 20),
        "response": np.tile([0, 1], 20),
        "outcome": np.tile([0, 1], 20),
    })
    frozen = {"Low": 1.5, "High": 2.5}
    first = fixed_threshold_patient_bootstrap(
        data, "score", "response", "outcome", "subject_id", frozen,
        n_bootstrap=12, seed=42)
    second = fixed_threshold_patient_bootstrap(
        data, "score", "response", "outcome", "subject_id", frozen,
        n_bootstrap=12, seed=42)
    pd.testing.assert_frame_equal(first, second)
    assert set(first.groupby("level").size()) == {12}
    assert set(first.loc[first.level.eq("Low"), "frozen_threshold"]) == {1.5}
    assert set(first.loc[first.level.eq("High"), "frozen_threshold"]) == {2.5}
    assert first.loc[first.level.eq("High"), "alert_count"].eq(0).all()
