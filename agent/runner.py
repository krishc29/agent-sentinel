"""Walks a scenario and emits the action log.

Pure and deterministic: the same scenario file in produces an identical action log
out, every run. No randomness anywhere.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from agent import policy
from agent.tools import ToolLog


def run_scenario_dict(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Run the gullible policy against an in-memory scenario dict, and assemble the action log.

    Pulled out of run_scenario() so callers that build scenarios in memory (e.g. the
    synthetic benign generator) don't need to round-trip through a JSON file on disk.
    """
    log = ToolLog()
    policy.run_policy(
        task=scenario["task"],
        files=scenario["files"],
        primary_file=scenario["primary_file"],
        log=log,
    )

    # Assemble the final action-log object. scenario_id / true_label / owasp_tags /
    # task are copied straight from the scenario; steps come from what the agent did.
    return {
        "scenario_id": scenario["scenario_id"],
        "true_label": scenario["true_label"],
        "owasp_tags": scenario["owasp_tags"],
        "task": scenario["task"],
        "steps": log.steps,
    }


def run_scenario(scenario_path: str) -> Dict[str, Any]:
    """Load a scenario from a JSON file and run it."""
    with open(scenario_path, "r", encoding="utf-8") as fh:
        scenario = json.load(fh)
    return run_scenario_dict(scenario)
