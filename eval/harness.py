"""The evaluation harness: grades a verdict against ground truth.

This is the ONLY place allowed to read ``true_label``. It is layer-agnostic: it
scores verdicts and does not care how many detection layers produced them.

``score`` handles a single (log, verdict) pair. It is written so a future batch
function can call it in a loop and aggregate into precision / recall / FPR.
"""

from __future__ import annotations

from typing import Any, Dict


def score(action_log: Dict[str, Any], verdict: Dict[str, Any]) -> Dict[str, Any]:
    """Compare a verdict to the action log's true_label and classify the outcome."""
    true_label = action_log["true_label"]
    predicted = verdict["verdict"]

    # Treat "attack" as the positive class.
    if predicted == "attack" and true_label == "attack":
        outcome = "true_positive"
    elif predicted == "benign" and true_label == "benign":
        outcome = "true_negative"
    elif predicted == "attack" and true_label == "benign":
        outcome = "false_positive"
    else:  # predicted == "benign" and true_label == "attack"
        outcome = "false_negative"

    return {
        "scenario_id": action_log["scenario_id"],
        "true_label": true_label,
        "verdict": predicted,
        "outcome": outcome,
        "correct": predicted == true_label,
    }
