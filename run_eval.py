"""Batch evaluation: run every scenario -> verdict -> score, then aggregate.

Run with:  python run_eval.py

This complements run.py (which walks through a single scenario in detail). Here we
run the whole scenarios/ directory and report precision / recall / false-positive
rate / accuracy across the set. A copy of the report is written to
results/eval_report.json (results/ is gitignored except for a .gitkeep placeholder,
so this is generated output, not something we commit).

Each report entry carries more than harness.score() alone returns - reasons,
risk_score, layer3, owasp_tags, task, and the full action_log - so downstream
consumers (the dashboard, docs/generate_owasp_mapping.py, docs/generate_incidents.py)
don't each need to re-run the pipeline themselves. harness.py itself stays untouched;
this assembly happens here, not there.
"""

from __future__ import annotations

import glob
import json
import os

from agent import runner
from detector import anomaly, engine
from eval import harness, metrics

HERE = os.path.dirname(os.path.abspath(__file__))
SCENARIOS_DIR = os.path.join(HERE, "scenarios")
REPORT_PATH = os.path.join(HERE, "results", "eval_report.json")
BASELINE_PATH = os.path.join(HERE, "detector", "baseline.json")


def run_all_scenarios(scenarios_dir: str = SCENARIOS_DIR, baseline_path: str = BASELINE_PATH):
    """Run every scenario through the full pipeline; return the enriched result list.

    Pulled out as its own function (not just inline in main()) so other scripts -
    the dashboard, the doc generators - can get the same enriched results without
    shelling out to this script or re-parsing eval_report.json.
    """
    baseline = anomaly.load_baseline(baseline_path)
    scenario_paths = sorted(glob.glob(os.path.join(scenarios_dir, "*.json")))

    results = []
    for path in scenario_paths:
        with open(path, "r", encoding="utf-8") as fh:
            scenario = json.load(fh)
        log = runner.run_scenario_dict(scenario)
        verdict = engine.judge(log, baseline)
        result = harness.score(log, verdict)
        result.update(
            {
                "reasons": verdict["reasons"],
                "risk_score": verdict["risk_score"],
                "layer3": verdict["layer3"],
                "owasp_tags": scenario["owasp_tags"],
                "task": scenario["task"],
                "action_log": log,
            }
        )
        results.append(result)
    return results


def main() -> None:
    results = run_all_scenarios()

    print(f"{'scenario_id':32s} {'true_label':10s} {'verdict':10s} {'outcome':16s} correct")
    print("-" * 82)
    for result in results:
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
