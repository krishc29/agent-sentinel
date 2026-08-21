"""The detection engine: combines layers into a single verdict.

Layer-agnostic by design: Layer 1 (rules) decides the verdict; Layer 2 (scoring)
adds an auxiliary risk_score for a human reviewer but never changes the verdict
itself. Layer 3 (anomaly) is not wired in yet.

IMPORTANT: this module must NEVER reference ``true_label``. The verdict is derived
purely from the agent's recorded behaviour. The ground-truth label is the eval
harness's concern alone.
"""

from __future__ import annotations

from typing import Any, Dict

from detector import features, rules, scoring

# The rules that make up Layer 1 for the slice.
LAYER1_RULES = [
    rules.untrusted_read_then_external_send,
    rules.untrusted_read_then_destructive_delete,
]


def judge(action_log: Dict[str, Any]) -> Dict[str, Any]:
    """Return a verdict for an action log.

    If any Layer-1 rule fires, the verdict is "attack"; otherwise "benign" — Layer 1
    alone decides the verdict. The reasons list contains the full result of every
    rule that fired. risk_score comes from Layer 2 (features + weighted scoring) as
    auxiliary context; it never overrides the verdict.
    """
    fired = []
    for rule in LAYER1_RULES:
        result = rule(action_log)  # note: rule receives the log but never reads true_label
        if result["fired"]:
            fired.append(result)

    verdict = "attack" if fired else "benign"
    risk_score = scoring.score(features.extract(action_log))
    return {
        "verdict": verdict,
        "reasons": fired,
        "risk_score": risk_score,
    }
