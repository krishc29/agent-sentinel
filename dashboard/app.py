"""Agent Sentinel dashboard.

Run with:  streamlit run dashboard/app.py

Two full views on the same live data - a toggle at the top switches between them:

- Confusion Matrix: the 2x2 outcome grid as hero, precision/recall/FPR/accuracy as
  metric cards, a filterable/sortable scenario table below. Light, data-dense.
- Watch Floor: dark glass-panel command center, scenarios sorted by risk_score,
  a detail panel for the selected scenario's action log, fired rules, and Layer 3
  result.

Both views are self-contained custom HTML/CSS blocks (not Streamlit's native theme
system), matching Plates 04 and 01 from the "Sentinel Plates" dashboard-concept
catalog - so each keeps its own look regardless of Streamlit's own base theme, and
the toggle can switch between them without a page reload.

Data is computed live via run_eval.run_all_scenarios() (imported directly, not by
reading a possibly-stale results/eval_report.json) and cached for the session.
"""

from __future__ import annotations

import os
import sys

import pandas as pd
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from run_eval import run_all_scenarios  # noqa: E402

st.set_page_config(page_title="Agent Sentinel", page_icon="\U0001F6E1️", layout="wide")

st.markdown(
    """
    <style>
      .block-container { padding-top: 2rem; max-width: 1180px; }
      #MainMenu, footer, header { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_results():
    return run_all_scenarios()


def confusion_counts(results):
    counts = {"true_positive": 0, "true_negative": 0, "false_positive": 0, "false_negative": 0}
    for r in results:
        counts[r["outcome"]] += 1
    return counts


# --------------------------------------------------------------------------------
# Confusion Matrix view (Plate 04)
# --------------------------------------------------------------------------------

def render_confusion_matrix(results) -> None:
    counts = confusion_counts(results)
    tp, tn, fp, fn = (
        counts["true_positive"], counts["true_negative"],
        counts["false_positive"], counts["false_negative"],
    )
    total = tp + tn + fp + fn
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    accuracy = (tp + tn) / total if total else 0.0

    st.markdown(
        f"""
        <style>
          .cm-wrap {{ background:#F5F6F2; border:1px solid #DEE1D8; border-radius:10px;
                      padding:22px 24px; font-family:-apple-system,"Segoe UI",sans-serif; }}
          .cm-grid {{ display:grid; grid-template-columns:repeat(2,1fr); gap:10px; margin-bottom:18px; }}
          .cm-cell {{ border-radius:8px; padding:18px; text-align:center; font-family:"SFMono-Regular",Consolas,monospace; }}
          .cm-cell .v {{ font-size:32px; font-weight:600; }}
          .cm-cell .l {{ font-size:11px; text-transform:uppercase; letter-spacing:.05em; opacity:.8; margin-top:4px; }}
        </style>
        <div class="cm-wrap">
          <div class="cm-grid">
            <div class="cm-cell" style="background:#DCEEDF;color:#2E6B3C"><div class="v">{tp}</div><div class="l">True positive</div></div>
            <div class="cm-cell" style="background:#F3E4DC;color:#9C4A2B"><div class="v">{fp}</div><div class="l">False positive</div></div>
            <div class="cm-cell" style="background:#F3E4DC;color:#9C4A2B"><div class="v">{fn}</div><div class="l">False negative</div></div>
            <div class="cm-cell" style="background:#DCEEDF;color:#2E6B3C"><div class="v">{tn}</div><div class="l">True negative</div></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Precision", f"{precision:.2f}")
    m2.metric("Recall", f"{recall:.2f}")
    m3.metric("False positive rate", f"{fpr:.2f}")
    m4.metric("Accuracy", f"{accuracy:.2f}")

    st.markdown("#### Scenarios")

    all_outcomes = sorted({r["outcome"] for r in results})
    all_tags = sorted({tag for r in results for tag in r["owasp_tags"]})

    fcol1, fcol2 = st.columns(2)
    outcome_filter = fcol1.multiselect("Filter by outcome", all_outcomes)
    tag_filter = fcol2.multiselect("Filter by OWASP tag", all_tags)

    rows = []
    for r in results:
        if outcome_filter and r["outcome"] not in outcome_filter:
            continue
        if tag_filter and not set(tag_filter) & set(r["owasp_tags"]):
            continue
        rows.append(
            {
                "scenario_id": r["scenario_id"],
                "true_label": r["true_label"],
                "verdict": r["verdict"],
                "outcome": r["outcome"],
                "risk_score": r["risk_score"],
                "owasp_tags": ", ".join(r["owasp_tags"]) if r["owasp_tags"] else "-",
                "task": r["task"],
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# --------------------------------------------------------------------------------
# Watch Floor view (Plate 01)
# --------------------------------------------------------------------------------

def render_watch_floor(results) -> None:
    counts = confusion_counts(results)
    tp, tn, fp, fn = (
        counts["true_positive"], counts["true_negative"],
        counts["false_positive"], counts["false_negative"],
    )
    total = tp + tn + fp + fn
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0

    ranked = sorted(results, key=lambda r: r["risk_score"], reverse=True)

    st.markdown(
        """
        <style>
          .wf-wrap { background:linear-gradient(160deg,#0E1B22,#152A31 60%,#0E1B22);
                     border-radius:10px; padding:18px 20px; color:#DCE8E8;
                     font-family:-apple-system,"Segoe UI",sans-serif; }
          .wf-kpis { display:flex; gap:10px; margin-bottom:14px; }
          .wf-card { flex:1; background:rgba(255,255,255,0.06); backdrop-filter:blur(6px);
                     border:1px solid rgba(255,255,255,0.09); border-radius:8px; padding:12px 14px; }
          .wf-card .n { font-family:"SFMono-Regular",Consolas,monospace; font-size:22px; color:#EFFAF9; }
          .wf-card .l { font-size:10px; color:#82A6A5; text-transform:uppercase; letter-spacing:.06em; margin-top:3px; }
          .wf-list { background:rgba(255,255,255,0.045); border:1px solid rgba(255,255,255,0.08);
                     border-radius:8px; padding:6px 10px; }
          .wf-item { display:flex; justify-content:space-between; align-items:center;
                     font-family:"SFMono-Regular",Consolas,monospace; font-size:12.5px;
                     padding:8px 4px; border-bottom:1px solid rgba(255,255,255,0.07); }
          .wf-item:last-child { border-bottom:none; }
          .wf-dot { width:7px; height:7px; border-radius:50%; display:inline-block; margin-right:8px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    kpi_html = f"""
    <div class="wf-wrap">
      <div class="wf-kpis">
        <div class="wf-card"><div class="n">{precision:.2f}</div><div class="l">Precision</div></div>
        <div class="wf-card"><div class="n">{recall:.2f}</div><div class="l">Recall</div></div>
        <div class="wf-card"><div class="n">{fpr:.2f}</div><div class="l">False pos. rate</div></div>
        <div class="wf-card"><div class="n">{total}</div><div class="l">Scenarios watched</div></div>
      </div>
      <div class="wf-list">
    """
    for r in ranked:
        dot_color = "#E48468" if r["true_label"] == "attack" else "#7FBE8C"
        kpi_html += (
            f'<div class="wf-item"><span><span class="wf-dot" style="background:{dot_color}"></span>'
            f'{r["scenario_id"]}</span><span>{r["risk_score"]}</span></div>'
        )
    kpi_html += "</div></div>"
    st.markdown(kpi_html, unsafe_allow_html=True)

    st.markdown("")
    scenario_ids = [r["scenario_id"] for r in ranked]
    selected_id = st.selectbox("Inspect a scenario", scenario_ids)
    selected = next(r for r in ranked if r["scenario_id"] == selected_id)

    gauge_deg = round(selected["risk_score"] / 100 * 360)
    reasons_html = "".join(
        f'<div style="padding:4px 0;color:#FF8A73;">&#9888; [{x["rule"]}] {x["detail"]}</div>'
        for x in selected["reasons"]
    ) or '<div style="color:#7FBE8C;">No Layer-1 rule fired.</div>'

    steps_html = "".join(
        f'<div style="padding:3px 0;border-bottom:1px solid rgba(255,255,255,0.06);">'
        f'[{s["i"]}] {s["tool"]} &middot; prov={s.get("data_provenance","-")} &middot; '
        f'external={s.get("destination_external", False)}</div>'
        for s in selected["action_log"]["steps"]
    )

    layer3 = selected["layer3"]
    layer3_line = (
        f'<span style="color:#E48468;">FLAGGED</span> — {layer3["detail"]}'
        if layer3["fired"]
        else f'<span style="color:#7FBE8C;">clear</span> — {layer3["detail"]}'
    )

    st.markdown(
        f"""
        <style>
          .wf-detail {{ background:#0E1B22; border:1px solid rgba(255,255,255,0.08); border-radius:8px;
                        padding:16px 18px; color:#DCE8E8; font-family:-apple-system,"Segoe UI",sans-serif;
                        display:flex; gap:22px; }}
          .wf-gauge {{ width:76px; height:76px; border-radius:50%; flex:0 0 auto;
                       background: conic-gradient(#E48468 0deg {gauge_deg}deg, rgba(255,255,255,0.1) {gauge_deg}deg 360deg);
                       display:flex; align-items:center; justify-content:center; }}
          .wf-gauge span {{ background:#0E1B22; width:58px; height:58px; border-radius:50%;
                            display:flex; align-items:center; justify-content:center;
                            font-family:"SFMono-Regular",Consolas,monospace; font-size:15px; }}
          .wf-body {{ flex:1; font-size:12.5px; font-family:"SFMono-Regular",Consolas,monospace; }}
          .wf-body h5 {{ font-family:-apple-system,"Segoe UI",sans-serif; font-size:11px;
                        text-transform:uppercase; letter-spacing:.06em; color:#82A6A5; margin:10px 0 4px; }}
          .wf-body h5:first-child {{ margin-top:0; }}
        </style>
        <div class="wf-detail">
          <div class="wf-gauge"><span>{selected['risk_score']}</span></div>
          <div class="wf-body">
            <h5>Verdict</h5>
            <div>{selected['verdict']} &middot; true_label={selected['true_label']} &middot; outcome={selected['outcome']}</div>
            <h5>Layer 1 reasons</h5>
            {reasons_html}
            <h5>Layer 3 (auxiliary)</h5>
            <div>{layer3_line}</div>
            <h5>Action log</h5>
            {steps_html}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------------

def main() -> None:
    st.title("Agent Sentinel")
    st.caption(
        "Layered detection over a simulated, gullible AI agent — every number below "
        "is computed live from the real scenario library, not a static screenshot."
    )

    view = st.segmented_control(
        "View", ["Confusion Matrix", "Watch Floor"], default="Confusion Matrix"
    )
    st.write("")

    results = load_results()

    if view == "Watch Floor":
        render_watch_floor(results)
    else:
        render_confusion_matrix(results)


if __name__ == "__main__":
    main()
