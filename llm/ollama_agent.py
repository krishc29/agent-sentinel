"""Phase 4: a real-LLM agent driven via Ollama (local, offline).

NOT IMPLEMENTED YET - this is the interface this module will expose once it is,
kept here (rather than a "LATER" one-liner) so the shape is locked in advance. Full
design, including why this can't just replace agent/policy.py, is in
docs/LLM_AGENT_PLAN.md.

This will be the only non-deterministic component in the whole project. It must
never be called from anywhere in the deterministic pipeline (agent/runner.py,
run.py, run_eval.py, tests/) - it gets its own, clearly-labeled entry point once
implemented.
"""

from __future__ import annotations

from typing import Any, Dict

from agent.tools import ToolLog

DEFAULT_MODEL = "qwen3.5:4b"


def run_llm_policy(
    task: str,
    files: Dict[str, Any],
    primary_file: str,
    log: ToolLog,
    model: str = DEFAULT_MODEL,
) -> None:
    """Drive the same ToolLog/tools.py interface as agent.policy.run_policy, but with
    a real local LLM (via Ollama) deciding which tool calls to make, instead of the
    hand-coded gullible policy.

    See docs/LLM_AGENT_PLAN.md for the full design: prompt structure, how the
    model's output gets parsed into structured calls (never executed directly -
    always routed through agent/tools.py's safe stubs), and what a run through this
    is actually meant to measure.
    """
    raise NotImplementedError(
        "Phase 4 is designed (see docs/LLM_AGENT_PLAN.md) but not yet built. "
        "Ollama is installed locally with models pulled (qwen3.5:4b, qwen3-coder:30b) "
        "and ready when this is picked up."
    )
