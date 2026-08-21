"""Batch evaluation: run every scenario -> verdict -> score, then aggregate.

Run with:  python run_eval.py

This complements run.py (which walks through a single scenario in detail). Here we
run the whole scenarios/ directory and report precision / recall / false-positive
rate / accuracy across the set. A copy of the report is written to
results/eval_report.json (results/ is gitignored except for a .gitkeep placeholder,
so this is generated output, not something we commit).
"""

from __future__ import annotations

import glob
import json
import os

from agent import runner
from detector import engine
from eval import harness, metrics

HERE = os.path.dirname(os.path.abspath(__file__))
SCENARIOS_DIR = os.path.join(HERE, "scenarios")
REPORT_PATH = os.path.join(HERE, "results", "eval_report.json")


def main() -> None:
    scenario_paths = sorted(glob.glob(os.path.join(SCENARIOS_DIR, "*.json")))

    results = []
    print(f"{'scenario_id':32s} {'true_label':10s} {'verdict':10s} {'outcome':16s} correct")
    print("-" * 82)
    for path in scenario_paths:
        log = runner.run_scenario(path)
        verdict = engine.judge(log)
        result = harness.score(log, verdict)
        results.append(result)
        print(
            f"{result['scenario_id']:32s} {result['true_label']:10s} "
            f"{result['verdict']:10s} {result['outcome']:16s} {result['correct']}"
        )

    summary = metrics.aggregate(results)

    print("-" * 82)
    print(f"total: {summary['total']}   counts: {summary['counts']}")
    print(
        f"precision: {summary['precision']}   recall: {summary['recall']}   "
        f"false_positive_rate: {summary['false_positive_rate']}   accuracy: {summary['accuracy']}"
    )

    report = {"results": results, "summary": summary}
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(f"\nWrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
