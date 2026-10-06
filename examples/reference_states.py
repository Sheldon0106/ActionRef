"""Small deterministic synthetic examples of ActionRef output states."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from universal_cutoff import fit_behavior_thresholds


def run():
    rows = []
    scores = np.arange(101)
    scenarios = {
        'absolute_references': .02 + .90 * scores / 100,
        'relative_references': .02 + .38 * scores / 100,
        'partial_references': .25 + .65 * scores / 100,
        'abstention': np.full(101, .30),
    }
    for name, probabilities in scenarios.items():
        frame = pd.DataFrame({'score': np.repeat(scores, 100),
            'response': np.concatenate([np.r_[np.ones(round(p*100)), np.zeros(100-round(p*100))]
                                        for p in probabilities])})
        result = fit_behavior_thresholds(frame, 'score', 'response')
        anchors = result.anchors[['level', 'selected_threshold', 'target_probability',
                                  'anchor_family', 'provenance_tier', 'attainability_status', 'reason']].copy()
        anchors.insert(0, 'scenario', name)
        rows.append(anchors)
    return pd.concat(rows, ignore_index=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=Path('output/reference-states'))
    args = parser.parse_args()
    table = run()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.output_dir/'states.csv', index=False)
    print(table[['scenario', 'level', 'selected_threshold', 'provenance_tier', 'attainability_status']].to_string(index=False))
