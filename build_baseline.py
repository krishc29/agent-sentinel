"""Build the Layer 3 statistical baseline from synthetic benign scenarios.

Run with:  python build_baseline.py

Generates 80 deterministic synthetic benign scenarios (eval/synth_benign.py), runs
each through the agent, extracts features, builds a per-feature mean/stdev baseline
(detector/anomaly.py), and writes it to detector/baseline.json. Also prints three
sanity checks: self-consistency against the same synthetic set, a held-out check
against the real S06-S09 benign scenarios, and an exploratory check against the real
attack scenarios (Layer 3 is not wired into the main verdict - see
docs/LAYER3_NOTES.md - so this is informational, not a pass/fail gate).
"""

from __future__ import annotations

import glob
import json
import os

from agent import runner
from detector import anomaly, features

HERE = os.path.dirname(os.path.abspath(__file__))
SCENARIOS_DIR = os.path.join(HERE, "scenarios")
BASELINE_PATH = os.path.join(HERE, "detector", "baseline.json")
N_SYNTHETIC = 80
SEED = 0


def _flag_rate(scenario_paths, baseline) -> None:
    fired = 0
    for path in scenario_paths:
        log = runner.run_scenario(path)
        verdict = anomaly.judge(log, baseline)
        marker = "FLAGGED" if verdict["fired"] else "ok"
        if verdict["fired"]:
            fired += 1
        print(f"  {log['scenario_id']:32s} true_label={log['true_label']:7s} {marker}")
    print(f"  -> {fired}/{len(scenario_paths)} flagged")


def main() -> None:
    from eval import synth_benign

    print(f"Generating {N_SYNTHETIC} synthetic benign scenarios (seed={SEED})...")
    synthetic = synth_benign.generate(N_SYNTHETIC, seed=SEED)

    feature_vectors = []
    for scenario in synthetic:
        log = runner.run_scenario_dict(scenario)
        feature_vectors.append(features.extract(log))

    baseline = anomaly.build_baseline(feature_vectors)
    anomaly.save_baseline(baseline, BASELINE_PATH)
    print(f"Wrote baseline to {BASELINE_PATH}:")
    print(json.dumps(baseline, indent=2, sort_keys=True))

    print("\n--- Self-consistency: judge() over the same synthetic set it was built from ---")
    fired = 0
    for scenario in synthetic:
        log = runner.run_scenario_dict(scenario)
        verdict = anomaly.judge(log, baseline)
        if verdict["fired"]:
            fired += 1
    print(f"  {fired}/{len(synthetic)} flagged")

    print("\n--- Held-out: real benign scenarios (S06-S09) ---")
    benign_paths = sorted(
        p for p in glob.glob(os.path.join(SCENARIOS_DIR, "*.json"))
        if os.path.basename(p).startswith(("S06", "S07", "S08", "S09"))
    )
    _flag_rate(benign_paths, baseline)

    print("\n--- Exploratory: real attack scenarios (S01-S05) ---")
    attack_paths = sorted(
        p for p in glob.glob(os.path.join(SCENARIOS_DIR, "*.json"))
        if os.path.basename(p).startswith(("S01", "S02", "S03", "S04", "S05"))
    )
    _flag_rate(attack_paths, baseline)


if __name__ == "__main__":
    main()
