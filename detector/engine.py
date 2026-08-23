"""The detection engine: combines layers into a single verdict.

Layer-agnostic by design: Layer 1 (rules) decides the verdict; Layer 2 (scoring)
and Layer 3 (anomaly) both add auxiliary, non-authoritative context for a human
reviewer but never change the verdict itself. Layer 3 under-recalls on its own
(see docs/LAYER3_NOTES.md - it misses order-dependent attacks by construction), so
letting it influence the verdict would only hurt accuracy, not help it.

IMPORTANT: this module must NEVER reference ``true_label``. The verdict is derived
purely from the agent's recorded behaviour. The ground-truth label is the eval
harness's concern alone.

This module has no filesystem coupling on purpose - Layer 3 needs a baseline dict
to run, and callers pass one in explicitly (loaded via anomaly.load_baseline) rather
than engine.py reaching for detector/baseline.json itself. That keeps judge() pure
and testable without a baseline file needing to exist.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from detector import anomaly, features, rules, scoring

# The rules that make up Layer 1 for the slice.
LAYER1_RULES = [
    rules.untrusted_read_then_external_send,
    rules.untrusted_read_then_destructive_delete,
]


def judge(
    action_log: Dict[str, Any],
    baseline: Optional[Dict[str, Dict[str, float]]] = None,
) -> Dict[str, Any]:
    """Return a verdict for an action log.

    If any Layer-1 rule fires, the verdict is "attack"; otherwise "benign" — Layer 1
    alone decides the verdict. The reasons list contains the full result of every
    rule that fired. risk_score comes from Layer 2 (features + weighted scoring) as
    auxiliary context; it never overrides the verdict. If a Layer 3 baseline is
    supplied, layer3 holds its (also auxiliary) anomaly result; otherwise layer3 is
    None and behaviour is identical to before Layer 3 existed.
    """
    fired = []
    for rule in LAYER1_RULES:
        result = rule(action_log)  # note: rule receives the log but never reads true_label
        if result["fired"]:
            fired.append(result)

    verdict = "attack" if fired else "benign"
    risk_score = scoring.score(features.extract(action_log))
    layer3 = anomaly.judge(action_log, baseline) if baseline is not None else None
    return {
        "verdict": verdict,
        "reasons": fired,
        "risk_score": risk_score,
        "layer3": layer3,
    }
