"""The detection engine: combines layers into a single verdict.

Layer-agnostic by design. For the slice it runs the one Layer-1 rule, but the
shape of the output (verdict + reasons + risk_score) is what every future layer
will feed into.

IMPORTANT: this module must NEVER reference ``true_label``. The verdict is derived
purely from the agent's recorded behaviour. The ground-truth label is the eval
harness's concern alone.
"""

from __future__ import annotations

from typing import Any, Dict

from detector import rules

# The rules that make up Layer 1 for the slice.
LAYER1_RULES = [rules.untrusted_read_then_external_send]


def judge(action_log: Dict[str, Any]) -> Dict[str, Any]:
    """Return a verdict for an action log.

    If any rule fires, the verdict is "attack"; otherwise "benign". The reasons
    list contains the full result of every rule that fired. risk_score stays None
    until Layer 2 (scoring) exists.
    """
    fired = []
    for rule in LAYER1_RULES:
        result = rule(action_log)  # note: rule receives the log but never reads true_label
        if result["fired"]:
            fired.append(result)

    verdict = "attack" if fired else "benign"
    return {
        "verdict": verdict,
        "reasons": fired,
        "risk_score": None,
    }
