"""Layer 3: anomaly detection over feature vectors.

Flags an action log as anomalous by comparing its feature vector (detector/features.py)
against a statistical baseline built from many benign examples, instead of a hand-written
rule (Layer 1) or a hand-weighted score (Layer 2). build_baseline()/judge() are pure
functions with no filesystem coupling, to stay unit-testable and consistent with the
rest of detector/; save_baseline()/load_baseline() do the JSON I/O separately.

Wired into detector/engine.judge() as an optional, auxiliary field (verdict["layer3"]) -
callers pass a baseline loaded via load_baseline(), engine.py itself stays free of
filesystem coupling. See docs/LAYER3_NOTES.md for why it's auxiliary, not a vote: it
under-recalls by construction (blind to step order), so it must never flip the verdict.
"""

from __future__ import annotations

import json
import statistics
from typing import Any, Dict, List

from detector import features as features_module

Z_SCORE_THRESHOLD = 3.0


def build_baseline(feature_vectors: List[Dict[str, int]]) -> Dict[str, Dict[str, float]]:
    """Compute per-feature {mean, stdev} over a list of feature dicts.

    All feature dicts are expected to share the same keys (they all come from
    detector.features.extract). A feature that never varies across the baseline
    (e.g. delete_count, since legitimate tasks never delete files in this project's
    model) ends up with stdev == 0.0 - judge() has an explicit branch for that.
    """
    if not feature_vectors:
        raise ValueError("build_baseline requires at least one feature vector")

    keys = feature_vectors[0].keys()
    baseline: Dict[str, Dict[str, float]] = {}
    for key in keys:
        values = [fv[key] for fv in feature_vectors]
        baseline[key] = {
            "mean": statistics.mean(values),
            "stdev": statistics.pstdev(values),
        }
    return baseline


def judge(action_log: Dict[str, Any], baseline: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """Compare an action log's features against the baseline; flag outliers.

    For each feature: if the baseline has nonzero spread, flag when the observed
    value is more than Z_SCORE_THRESHOLD standard deviations from the mean. If the
    baseline is constant for that feature (stdev == 0 - e.g. delete_count, which is
    always 0 across every benign example), a z-score is undefined, so instead flag
    any deviation at all from that constant: any delete_file call when the baseline
    NEVER shows one is exactly the kind of thing Layer 3 should catch.
    """
    feats = features_module.extract(action_log)
    flagged = []

    for key, observed in feats.items():
        if key not in baseline:
            continue
        mean = baseline[key]["mean"]
        stdev = baseline[key]["stdev"]

        if stdev > 0:
            z = (observed - mean) / stdev
            if abs(z) > Z_SCORE_THRESHOLD:
                flagged.append(
                    f"{key}={observed} is {abs(z):.1f} standard deviations from the "
                    f"baseline mean ({mean:.2f})"
                )
        else:
            if observed != mean:
                flagged.append(
                    f"{key}={observed} but the baseline never shows anything other "
                    f"than {mean:.0f}"
                )

    fired = bool(flagged)
    detail = "; ".join(flagged) if flagged else "No feature deviated from the baseline."
    return {
        "rule": "layer3_anomaly",
        "fired": fired,
        "detail": detail,
        "flagged_features": flagged,
    }


def save_baseline(baseline: Dict[str, Dict[str, float]], path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(baseline, fh, indent=2, sort_keys=True)


def load_baseline(path: str) -> Dict[str, Dict[str, float]]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)
