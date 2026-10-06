"""Run the held-out/red-team scenario set through the unmodified detector.

Run with:  python run_red_team_eval.py [scenario_dir]

scenario_dir defaults to scenarios_heldout/; pass scenarios_heldout2 to run the second,
pre-fix-frozen batch (see docs/RED_TEAM_RESULTS.md).

Reads scenarios_heldout/, never scenarios/ - kept strictly separate from the curated
9-scenario library run_eval.py reports precision/recall over, so this can never quietly
dilute or improve those headline numbers (same principle eval/synth_benign.py's generated
scenarios already follow). See docs/RED_TEAM_PLAN.md for the methodology and
docs/RED_TEAM_RESULTS.md for the write-up. No rule in detector/rules.py may be changed in
response to what this script finds without an explicit, separate decision to do so - that's
the whole point of a held-out set.
"""

from __future__ import annotations

import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from agent import runner  # noqa: E402
from detector import anomaly, engine  # noqa: E402
from eval import harness, metrics  # noqa: E402

DEFAULT_SCENARIOS_DIR = os.path.join(HERE, "scenarios_heldout")
BASELINE_PATH = os.path.join(HERE, "detector", "baseline.json")


def main() -> None:
    scenarios_dir = os.path.join(HERE, sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SCENARIOS_DIR
    baseline = anomaly.load_baseline(BASELINE_PATH)
    scenario_paths = sorted(glob.glob(os.path.join(scenarios_dir, "*.json")))

    results = []
    print(f"{'scenario_id':36s} {'true_label':10s} {'verdict':10s} {'outcome':16s} correct")
    print("-" * 90)
    for path in scenario_paths:
        log = runner.run_scenario(path)
        verdict = engine.judge(log, baseline)
        result = harness.score(log, verdict)
        results.append(result)
        print(
            f"{result['scenario_id']:36s} {result['true_label']:10s} "
            f"{result['verdict']:10s} {result['outcome']:16s} {result['correct']}"
        )

    summary = metrics.aggregate(results)
    print("-" * 90)
    print(f"total: {summary['total']}   counts: {summary['counts']}")
    print(
        f"precision: {summary['precision']}   recall: {summary['recall']}   "
        f"false_positive_rate: {summary['false_positive_rate']}   accuracy: {summary['accuracy']}"
    )
    print()
    print("Compare against the curated set's numbers (python run_eval.py) to see whether")
    print("Layer 1's rules generalized or were overfit - see docs/RED_TEAM_RESULTS.md.")


if __name__ == "__main__":
    main()
