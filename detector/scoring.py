"""Layer 2: weighted risk scoring over features.

Auxiliary signal only — the "verdict" field is decided entirely by Layer 1's rules
(see engine.py); risk_score is additional context for a human reviewer and does not
change what counts as attack/benign. Weights are hand-picked, not learned: an
external send after an untrusted read is the single strongest signal (matches the
Layer-1 rule's own logic), a triggered delete is next, and raw step count is a
weak, capped tiebreaker.
"""

from __future__ import annotations

from typing import Dict

WEIGHTS = {
    "untrusted_read_count": 15,
    "external_send_count": 35,
    "delete_count": 30,
    "step_count": 2,
}
MAX_SCORE = 100


def score(features: Dict[str, int]) -> int:
    """Combine a feature dict into a single 0-100 risk score."""
    raw = sum(WEIGHTS[name] * count for name, count in features.items() if name in WEIGHTS)
    return min(raw, MAX_SCORE)
