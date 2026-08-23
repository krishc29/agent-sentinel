"""Run every scenario through the real LLM agent instead of the deterministic policy.

Run with:  python run_llm_eval.py [model]

Non-deterministic - the whole point of this script. Kept entirely separate from
run_eval.py/results/eval_report.json, which report the deterministic, regenerable,
locked-reference numbers. This is a live experiment: it goes through the *same*
unmodified detector (detector/engine.py, detector/anomaly.py) as everything else, so the
detector's behaviour is being tested against a genuinely unpredictable agent, not just
reported on. Each run's raw Ollama transcripts (including the model's `thinking` field) are
saved to llm_runs/ (gitignored) so *why* the model did or didn't take the bait can actually
be inspected, not just the final tool calls.
"""

from __future__ import annotations

import glob
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from agent.tools import ToolLog  # noqa: E402
from detector import anomaly, engine  # noqa: E402
from eval import harness, metrics  # noqa: E402
from llm.ollama_agent import DEFAULT_MODEL, run_llm_policy  # noqa: E402

SCENARIOS_DIR = os.path.join(HERE, "scenarios")
BASELINE_PATH = os.path.join(HERE, "detector", "baseline.json")
RUNS_DIR = os.path.join(HERE, "llm_runs")


def run_scenario_with_llm(scenario: dict, model: str) -> tuple[dict, list]:
    """Same assembly agent/runner.py:run_scenario_dict does, but via the LLM policy -
    kept here rather than added to agent/runner.py, which must stay deterministic-only."""
    log = ToolLog()
    transcript: list = []
    run_llm_policy(
        task=scenario["task"],
        files=scenario["files"],
        primary_file=scenario["primary_file"],
        log=log,
        model=model,
        transcript=transcript,
    )
    action_log = {
        "scenario_id": scenario["scenario_id"],
        "true_label": scenario["true_label"],
        "owasp_tags": scenario["owasp_tags"],
        "task": scenario["task"],
        "steps": log.steps,
    }
    return action_log, transcript


def main() -> None:
    model = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL
    baseline = anomaly.load_baseline(BASELINE_PATH)
    scenario_paths = sorted(glob.glob(os.path.join(SCENARIOS_DIR, "*.json")))

    os.makedirs(RUNS_DIR, exist_ok=True)
    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    print(f"Model: {model}")
    print("(first call loads the model into memory and can take a while)")
    print()
    print(f"{'scenario_id':32s} {'true_label':10s} {'verdict':10s} {'outcome':16s} steps")
    print("-" * 86)

    results = []
    for path in scenario_paths:
        with open(path, "r", encoding="utf-8") as fh:
            scenario = json.load(fh)

        action_log, transcript = run_scenario_with_llm(scenario, model)
        verdict = engine.judge(action_log, baseline)
        result = harness.score(action_log, verdict)
        results.append(result)

        print(
            f"{result['scenario_id']:32s} {result['true_label']:10s} "
            f"{result['verdict']:10s} {result['outcome']:16s} {len(action_log['steps'])}"
        )

        transcript_path = os.path.join(RUNS_DIR, f"{run_stamp}_{scenario['scenario_id']}.json")
        with open(transcript_path, "w", encoding="utf-8") as fh:
            json.dump(
                {"model": model, "action_log": action_log, "verdict": verdict, "raw_transcript": transcript},
                fh,
                indent=2,
            )

    summary = metrics.aggregate(results)
    print("-" * 86)
    print(f"total: {summary['total']}   counts: {summary['counts']}")
    print(
        f"precision: {summary['precision']}   recall: {summary['recall']}   "
        f"false_positive_rate: {summary['false_positive_rate']}   accuracy: {summary['accuracy']}"
    )
    print(f"\nTranscripts saved under {RUNS_DIR}/{run_stamp}_*.json")


if __name__ == "__main__":
    main()
