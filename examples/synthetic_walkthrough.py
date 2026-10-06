"""Learn references, map capacity, and evaluate fixed thresholds on synthetic data.

Run from the repository root after installation:
    python examples/synthetic_walkthrough.py --output-dir output/synthetic

No clinical data or downloads are required. Each synthetic row represents a
different person, so a row split also separates people in this demonstration.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from universal_cutoff import (
    CapacityConfig, Module2Config, apply_capacity, build_threshold_table,
    evaluate_frozen_thresholds, fit_behavior_thresholds,
)


def make_synthetic_data(n=12000, seed=719):
    rng = np.random.RandomState(seed)
    score = rng.randint(0, 101, n)
    action_probability = 0.05 + 0.92 / (1 + np.exp(-(score - 45) / 8))
    outcome_probability = 0.01 + 0.35 / (1 + np.exp(-(score - 60) / 12))
    return pd.DataFrame({
        'score': score,
        'response': rng.binomial(1, action_probability),
        'outcome': rng.binomial(1, outcome_probability),
    })


def run_demo(output_dir):
    data = make_synthetic_data()
    learning = data.sample(frac=0.7, random_state=2026)
    evaluation = data.drop(learning.index)
    behavior = fit_behavior_thresholds(learning, 'score', 'response', Module2Config())
    learning_table = build_threshold_table(learning, 'score', 'response', 'outcome')
    capacity = apply_capacity(
        learning_table, behavior.anchors,
        CapacityConfig(K=1680, period='8,400 synthetic learning encounters'),
    )
    fixed = dict(zip(behavior.anchors.level, behavior.anchors.selected_threshold))
    fixed.update({
        row.level + ' capacity': float(row.operational_threshold)
        for row in capacity.table.itertuples()
        if np.isfinite(row.operational_threshold)
    })
    heldout = evaluate_frozen_thresholds(
        evaluation, 'score', fixed, response_col='response', outcome_col='outcome',
    )
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    behavior.anchors.to_csv(output / 'references.csv', index=False)
    behavior.response_curve.to_csv(output / 'learning_curve.csv', index=False)
    capacity.table.to_csv(output / 'capacity.csv', index=False)
    heldout.table.to_csv(output / 'heldout.csv', index=False)
    summary = {
        'data_kind': 'synthetic', 'seed': 719, 'split_seed': 2026,
        'learning_N': len(learning), 'evaluation_N': len(evaluation),
        'learning_action_rate': behavior.input_summary['response_prevalence'],
        'evidence_gate': behavior.evidence_gate, 'module2_config': behavior.config,
        'capacity_K': 1680, 'capacity_fraction_learning': 0.20,
        'evaluation_role': 'fixed thresholds; no refitting on evaluation data',
    }
    (output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print('Synthetic example | learning: {} | evaluation: {}'.format(len(learning), len(evaluation)))
    print('\nLearned references:')
    print(behavior.anchors[['level', 'selected_threshold', 'anchor_family', 'provenance_tier']].to_string(index=False))
    print('\nHeld-out evaluation (synthetic data):')
    print(heldout.table[['level', 'frozen_threshold', 'alert_fraction', 'response_yield', 'recall']].to_string(index=False))
    print('\nSaved aggregate outputs to {}'.format(output))
    return behavior, capacity, heldout, summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=Path('output/synthetic'))
    run_demo(parser.parse_args().output_dir)
