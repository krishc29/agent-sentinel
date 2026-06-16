"""Batch entry point for the vertical slice: scenario -> verdict -> score.

Run with:  python run.py

Expected result for S03_exfil_via_doc: the agent is fooled into emailing the secret
externally, the single rule fires, the verdict is "attack", and the eval harness
reports true_positive / correct = true.
"""

from __future__ import annotations

import json
import os

from agent import runner
from detector import engine
from eval import harness

# Resolve paths relative to this script so `python run.py` works from any CWD.
HERE = os.path.dirname(os.path.abspath(__file__))
SCENARIO = os.path.join(HERE, "scenarios", "S03_exfil_via_doc.json")


def main() -> None:
    log = runner.run_scenario(SCENARIO)
    verdict = engine.judge(log)
    result = harness.score(log, verdict)

    print("=" * 70)
    print("ACTION LOG (what the agent did)")
    print("=" * 70)
    print(json.dumps(log, indent=2))

    print()
    print("=" * 70)
    print("DETECTOR VERDICT")
    print("=" * 70)
    print(f"verdict:    {verdict['verdict']}")
    print(f"risk_score: {verdict['risk_score']}")
    if verdict["reasons"]:
        print("reasons:")
        for reason in verdict["reasons"]:
            print(f"  - [{reason['rule']}] {reason['detail']}")
    else:
        print("reasons:    (none — no rule fired)")

    print()
    print("=" * 70)
    print("EVAL OUTCOME")
    print("=" * 70)
    print(f"scenario_id: {result['scenario_id']}")
    print(f"true_label:  {result['true_label']}")
    print(f"verdict:     {result['verdict']}")
    print(f"outcome:     {result['outcome']}")
    print(f"correct:     {result['correct']}")


if __name__ == "__main__":
    main()
