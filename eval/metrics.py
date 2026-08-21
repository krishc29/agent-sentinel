"""Aggregate metrics: precision / recall / FPR over a batch of eval results.

Pure function over the ``outcome``/``correct`` fields eval/harness.py already produces
for each (log, verdict) pair — nothing here re-derives a verdict or touches true_label
beyond what harness.score already exposed.
"""

from __future__ import annotations

from typing import Any, Dict, List


def aggregate(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Roll up a list of harness.score(...) outputs into summary metrics.

    Treats "attack" as the positive class, matching eval/harness.py.
    """
    counts = {"true_positive": 0, "true_negative": 0, "false_positive": 0, "false_negative": 0}
    for result in results:
        counts[result["outcome"]] += 1

    tp, tn, fp, fn = (
        counts["true_positive"],
        counts["true_negative"],
        counts["false_positive"],
        counts["false_negative"],
    )
    total = tp + tn + fp + fn

    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    false_positive_rate = fp / (fp + tn) if (fp + tn) else None
    accuracy = (tp + tn) / total if total else None

    return {
        "total": total,
        "counts": counts,
        "precision": precision,
        "recall": recall,
        "false_positive_rate": false_positive_rate,
        "accuracy": accuracy,
    }
