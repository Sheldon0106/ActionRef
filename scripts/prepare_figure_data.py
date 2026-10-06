"""Export aggregate synthetic figure inputs; drawing is implemented entirely in R.

Reuses the existing seeded demonstration and learning split. No clinical data,
analysis changes, or Python plotting dependencies are involved.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

from universal_cutoff import build_threshold_table

ROOT = Path(__file__).resolve().parents[1]


def main():
    spec = importlib.util.spec_from_file_location(
        "actionref_demo", ROOT / "examples/synthetic_walkthrough.py")
    demo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(demo)
    behavior, capacity, heldout, summary = demo.run_demo(ROOT / "output/synthetic")
    learning = demo.make_synthetic_data().sample(frac=0.7, random_state=2026)
    candidates = build_threshold_table(learning, "score", "response", "outcome")
    out = ROOT / "docs/assets/data"
    tables = {
        "synthetic_learning_curve.csv": behavior.response_curve,
        "synthetic_alert_curve.csv": candidates.table[["threshold", "alert_count"]],
        "synthetic_references.csv": behavior.anchors,
        "synthetic_capacity.csv": capacity.table,
        "synthetic_heldout.csv": heldout.table,
    }
    for name, table in tables.items():
        table.to_csv(out / name, index=False, lineterminator="\n")
    (out / "synthetic_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    names = list(tables) + ["synthetic_summary.json"]
    manifest = {
        "source": "examples/synthetic_walkthrough.py",
        "kind": "synthetic aggregate data",
        "seed": 719, "split_seed": 2026,
        "sha256": {name: hashlib.sha256((out / name).read_bytes()).hexdigest()
                   for name in names},
    }
    (out / "synthetic_provenance.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
