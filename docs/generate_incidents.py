"""Generate docs/incidents/<scenario_id>.md, one per scenario, from the live pipeline.

Run with:  python docs/generate_incidents.py

Same "always live, never a stale copy" approach as generate_owasp_mapping.py - this
is Plate 03's "Case File" concept (see the Sentinel Plates artifact) rendered as
committed docs instead of a live UI panel.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from run_eval import run_all_scenarios  # noqa: E402

OUTPUT_DIR = os.path.join(HERE, "incidents")


def build_markdown(result) -> str:
    lines = [
        f"# {result['scenario_id']}",
        "",
        f"**Verdict:** `{result['verdict']}` &nbsp;·&nbsp; "
        f"**True label:** `{result['true_label']}` &nbsp;·&nbsp; "
        f"**Outcome:** `{result['outcome']}` &nbsp;·&nbsp; "
        f"**Risk score:** {result['risk_score']}/100",
        "",
        "## Task",
        "",
        result["task"],
        "",
    ]

    if result["owasp_tags"]:
        lines.append("## OWASP tags")
        lines.append("")
        lines.append(", ".join(f"`{tag}`" for tag in result["owasp_tags"]))
        lines.append("")

    lines.append("## Layer 1 (rules)")
    lines.append("")
    if result["reasons"]:
        for reason in result["reasons"]:
            lines.append(f"- **{reason['rule']}** fired: {reason['detail']}")
    else:
        lines.append("No rule fired.")
    lines.append("")

    lines.append("## Layer 3 (anomaly, auxiliary)")
    lines.append("")
    layer3 = result["layer3"]
    status = "flagged" if layer3["fired"] else "not flagged"
    lines.append(f"{status} — {layer3['detail']}")
    lines.append("")

    lines.append("## Action log")
    lines.append("")
    lines.append("| step | tool | data_provenance | destination_external |")
    lines.append("|---|---|---|---|")
    for step in result["action_log"]["steps"]:
        lines.append(
            f"| {step['i']} | `{step['tool']}` | {step.get('data_provenance', '')} | "
            f"{step.get('destination_external', '')} |"
        )
    lines.append("")

    return "\n".join(lines) + "\n"


def main() -> None:
    results = run_all_scenarios()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for result in results:
        path = os.path.join(OUTPUT_DIR, f"{result['scenario_id']}.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(build_markdown(result))
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
