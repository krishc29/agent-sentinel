"""Generate the static Agent Sentinel dashboard: site/index.html.

Run with:  python site/generate.py

Pure stdlib - imports agent/detector/eval the same way run_eval.py does, no
streamlit/pandas dependency here at all. Bakes the live pipeline's output directly
into the generated HTML as an inline JSON blob (no fetch, no server needed - the
page works standalone opened straight from disk). Committed like the project's other
regenerable artifacts (schema/action_log.example.json, detector/baseline.json,
docs/owasp_mapping.md); regenerate after any change to scenarios/ or detector/.

.github/workflows/deploy-pages.yml re-runs this on every push to master and publishes
site/ to GitHub Pages, so the live site stays in sync even if someone forgets to
regenerate locally before pushing.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from detector import anomaly  # noqa: E402
from eval import metrics  # noqa: E402
from run_eval import run_all_scenarios  # noqa: E402

OUTPUT_PATH = os.path.join(HERE, "index.html")
BASELINE_PATH = os.path.join(ROOT, "detector", "baseline.json")


def build_data() -> dict:
    results = run_all_scenarios()
    summary = metrics.aggregate(results)
    baseline = anomaly.load_baseline(BASELINE_PATH)
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "summary": summary,
        "results": results,
        "baseline": baseline,
    }


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agent Sentinel</title>
<meta name="description" content="Layered detection over a simulated, gullible AI agent - live results from the Agent Sentinel scenario library.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,500;0,6..72,600;1,6..72,500&family=Work+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --ground: #12141A;
    --panel: #1B1E27;
    --panel-2: #21242F;
    --ink: #ECEEF3;
    --muted: #9CA2B2;
    --line: #2A2E3A;
    --accent: #E8A33D;
    --accent-ink: #241804;
    --sem-attack: #E2664C;
    --sem-attack-soft: #33221D;
    --sem-benign: #6FBF8B;
    --sem-benign-soft: #1D2B22;
    --font-display: "Newsreader", Georgia, serif;
    --font-body: "Work Sans", -apple-system, "Segoe UI", sans-serif;
    --font-mono: "JetBrains Mono", "SFMono-Regular", Consolas, monospace;
  }
  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body {
    margin: 0; background: var(--ground); color: var(--ink);
    font-family: var(--font-body); line-height: 1.6; font-size: 16px;
  }
  ::selection { background: var(--accent); color: var(--accent-ink); }
  a { color: var(--accent); }
  code { font-family: var(--font-mono); background: var(--panel-2); padding: 1px 6px; border-radius: 3px; font-size: 0.88em; }
  .wrap { max-width: 1100px; margin: 0 auto; padding: 0 28px; }
  .mono { font-family: var(--font-mono); font-variant-numeric: tabular-nums; }

  /* ---------- hero ---------- */
  .hero { padding: 88px 0 56px; border-bottom: 1px solid var(--line); }
  .kicker { font-family: var(--font-mono); font-size: 12.5px; letter-spacing: .12em; text-transform: uppercase; color: var(--accent); margin: 0 0 20px; }
  h1.title { font-family: var(--font-display); font-weight: 600; font-size: clamp(2.4rem, 5vw, 3.6rem); line-height: 1.08; margin: 0 0 22px; max-width: 18ch; text-wrap: balance; }
  .lede { font-size: 1.15rem; color: var(--muted); max-width: 62ch; margin: 0 0 44px; }
  .stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px; background: var(--line); border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
  .stat { background: var(--panel); padding: 20px 22px; }
  .stat .v { font-family: var(--font-mono); font-size: 2.1rem; color: var(--accent); }
  .stat .l { font-size: 12px; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); margin-top: 4px; }
  @media (max-width: 720px) { .stat-row { grid-template-columns: repeat(2, 1fr); } }

  /* ---------- layers ---------- */
  .layers { padding: 64px 0; border-bottom: 1px solid var(--line); }
  .section-kicker { font-family: var(--font-mono); font-size: 12px; text-transform: uppercase; letter-spacing: .1em; color: var(--muted); margin: 0 0 10px; }
  h2 { font-family: var(--font-display); font-weight: 600; font-size: 1.85rem; margin: 0 0 14px; text-wrap: balance; }
  .section-intro { color: var(--muted); max-width: 66ch; margin: 0 0 32px; }
  .lane { display: grid; grid-template-columns: 220px 1fr; gap: 24px; padding: 22px 0; border-top: 1px solid var(--line); transition: opacity .2s; }
  .lane:first-of-type { border-top: none; }
  .lane.dim { opacity: .35; }
  .lane-head .n { font-family: var(--font-mono); font-size: 11px; color: var(--accent); }
  .lane-head h3 { font-family: var(--font-display); font-weight: 600; font-size: 1.15rem; margin: 4px 0 6px; }
  .lane-head p { color: var(--muted); font-size: 13.5px; margin: 0; }
  .lane-status { display: flex; align-items: center; gap: 14px; font-family: var(--font-mono); font-size: 13px; }
  .lane-badge { padding: 5px 12px; border-radius: 20px; font-size: 12px; white-space: nowrap; }
  .lane-badge.idle { background: var(--panel-2); color: var(--muted); }
  .lane-badge.fired { background: var(--sem-attack-soft); color: var(--sem-attack); }
  .lane-badge.clear { background: var(--sem-benign-soft); color: var(--sem-benign); }
  .lane-detail { color: var(--muted); flex: 1; }
  .layers-hint { font-size: 12.5px; color: var(--muted); margin-top: 18px; }

  /* ---------- explorer ---------- */
  .explorer { padding: 64px 0; border-bottom: 1px solid var(--line); }
  .filters { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 22px; }
  .chip { font-family: var(--font-mono); font-size: 12px; padding: 6px 13px; border-radius: 20px; border: 1px solid var(--line); background: var(--panel); color: var(--muted); cursor: pointer; user-select: none; }
  .chip.active { background: var(--accent); color: var(--accent-ink); border-color: var(--accent); }
  table.scenarios { width: 100%; border-collapse: collapse; }
  table.scenarios th { text-align: left; font-family: var(--font-mono); font-size: 11px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); padding: 10px 12px; border-bottom: 1px solid var(--line); cursor: pointer; white-space: nowrap; }
  table.scenarios th:hover { color: var(--ink); }
  table.scenarios th.sorted::after { content: " \2193"; color: var(--accent); }
  table.scenarios th.sorted.asc::after { content: " \2191"; }
  tr.srow { cursor: pointer; }
  tr.srow td { padding: 12px; border-bottom: 1px solid var(--line); font-size: 13.5px; vertical-align: middle; }
  tr.srow:hover td { background: var(--panel); }
  tr.srow.selected td { background: var(--panel-2); }
  .pill { font-family: var(--font-mono); font-size: 11px; padding: 3px 10px; border-radius: 20px; white-space: nowrap; }
  .pill.attack { background: var(--sem-attack-soft); color: var(--sem-attack); }
  .pill.benign { background: var(--sem-benign-soft); color: var(--sem-benign); }
  .risk-bar-wrap { display: flex; align-items: center; gap: 8px; }
  .risk-bar { width: 64px; height: 5px; background: var(--panel-2); border-radius: 3px; overflow: hidden; }
  .risk-bar > span { display: block; height: 100%; background: var(--accent); }
  .tag-list { color: var(--muted); font-size: 12px; }
  tr.detail-row td { padding: 0; border-bottom: 1px solid var(--line); }
  .detail-body { display: none; padding: 20px 16px 26px; background: var(--panel); font-family: var(--font-mono); font-size: 12.5px; }
  .detail-body.open { display: block; }
  .detail-body h4 { font-family: var(--font-body); font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); margin: 14px 0 6px; }
  .detail-body h4:first-child { margin-top: 0; }
  .detail-body .reason { color: var(--sem-attack); padding: 3px 0; }
  .detail-body .clear-line { color: var(--sem-benign); }
  .step-line { padding: 3px 0; border-bottom: 1px dashed var(--line); color: var(--muted); }
  .step-line:last-child { border-bottom: none; }
  .step-line .tool { color: var(--ink); }

  /* ---------- owasp ---------- */
  .owasp { padding: 64px 0; border-bottom: 1px solid var(--line); }
  .owasp-row { display: flex; align-items: center; gap: 14px; padding: 10px 0; }
  .owasp-tag { font-family: var(--font-mono); font-size: 12.5px; width: 320px; flex: 0 0 auto; color: var(--muted); }
  .owasp-track { flex: 1; height: 8px; background: var(--panel-2); border-radius: 4px; overflow: hidden; }
  .owasp-track > span { display: block; height: 100%; background: var(--accent); }
  .owasp-count { font-family: var(--font-mono); font-size: 12.5px; width: 24px; text-align: right; }

  footer { padding: 40px 0 60px; color: var(--muted); font-size: 13px; }
  footer a { color: var(--muted); text-decoration: underline; }
</style>
</head>
<body>

<div class="wrap">
  <div class="hero">
    <p class="kicker">Agent Sentinel &middot; live results</p>
    <h1 class="title">Layered detection over a simulated, gullible AI agent</h1>
    <p class="lede">A sandboxed AI agent is run through pre-labelled scenarios - some ordinary, some carrying a hidden prompt injection. A three-layer detector reads only the agent's action log, decides attack or benign, and an evaluator grades that verdict against the known truth. Nothing here touches a real network, inbox, or file.</p>
    <div class="stat-row" id="stat-row"></div>
  </div>

  <div class="layers">
    <p class="section-kicker">Architecture</p>
    <h2>Three layers, one verdict</h2>
    <p class="section-intro">Layer 1's rules alone decide attack or benign. Layers 2 and 3 are auxiliary signal a reviewer can see, never a vote - select any scenario below to see exactly which layers fired for it.</p>
    <div id="lanes"></div>
    <p class="layers-hint">Showing aggregate behaviour across all scenarios. Click a row in the table below to inspect one.</p>
  </div>

  <div class="explorer">
    <p class="section-kicker">Scenario library</p>
    <h2>Every scenario, every verdict</h2>
    <div class="filters" id="filters"></div>
    <table class="scenarios">
      <thead>
        <tr>
          <th data-key="scenario_id">Scenario</th>
          <th data-key="true_label">Label</th>
          <th data-key="verdict">Verdict</th>
          <th data-key="outcome">Outcome</th>
          <th data-key="risk_score" class="sorted">Risk</th>
          <th data-key="owasp_tags">OWASP</th>
        </tr>
      </thead>
      <tbody id="scenario-body"></tbody>
    </table>
  </div>

  <div class="owasp">
    <p class="section-kicker">Coverage</p>
    <h2>OWASP LLM Top 10 (2025) mapping</h2>
    <div id="owasp-rows"></div>
  </div>

  <footer>
    Generated __GENERATED_AT__ by <code>site/generate.py</code> from the live scenario library and detector output - not a static screenshot. Regenerate after any change to <code>scenarios/</code> or <code>detector/</code>. Source: <a href="https://github.com/krishc29/agent-sentinel">github.com/krishc29/agent-sentinel</a>.
  </footer>
</div>

<script>
const DATA = __DATA_JSON__;

function fmtPct(x) { return x === null || x === undefined ? "-" : x.toFixed(2); }

function renderStats() {
  const s = DATA.summary;
  const stats = [
    ["Precision", fmtPct(s.precision)],
    ["Recall", fmtPct(s.recall)],
    ["False positive rate", fmtPct(s.false_positive_rate)],
    ["Accuracy", fmtPct(s.accuracy)],
  ];
  document.getElementById("stat-row").innerHTML = stats.map(([l, v]) =>
    `<div class="stat"><div class="v mono">${v}</div><div class="l">${l}</div></div>`
  ).join("");
}

function laneStatsAggregate() {
  const results = DATA.results;
  const l1Attacks = results.filter(r => r.true_label === "attack");
  const l1Caught = l1Attacks.filter(r => r.reasons.length > 0).length;
  const l1FPs = results.filter(r => r.true_label === "benign" && r.reasons.length > 0).length;
  const scores = results.map(r => r.risk_score);
  const l3Attacks = l1Attacks.filter(r => r.layer3 && r.layer3.fired).length;
  return {
    l1: `${l1Caught}/${l1Attacks.length} attacks caught, ${l1FPs} false positive(s)`,
    l2: `Risk scores range ${Math.min(...scores)}-${Math.max(...scores)} across ${scores.length} scenarios`,
    l3: `${l3Attacks}/${l1Attacks.length} attacks caught alone - misses order-dependent attacks by design`,
  };
}

function renderLanes(selected) {
  const agg = laneStatsAggregate();
  let lanes;
  if (selected) {
    const r = selected;
    const l1fired = r.reasons.length > 0;
    const l3fired = r.layer3 && r.layer3.fired;
    lanes = [
      { n: "01", name: "Rules", desc: "Deterministic checks over the action log's provenance/destination fields.",
        status: l1fired ? "fired" : "clear", detail: l1fired ? r.reasons.map(x => x.detail).join(" ") : "No rule fired for this scenario." },
      { n: "02", name: "Risk score", desc: "Weighted count-based score, 0-100. Auxiliary - never decides the verdict.",
        status: "idle", detail: `risk_score = ${r.risk_score}/100 for ${r.scenario_id}` },
      { n: "03", name: "Anomaly", desc: "Flags deviation from a statistical baseline of 80 synthetic benign runs.",
        status: l3fired ? "fired" : "clear", detail: r.layer3 ? r.layer3.detail : "n/a" },
    ];
  } else {
    lanes = [
      { n: "01", name: "Rules", desc: "Deterministic checks over the action log's provenance/destination fields.", status: "idle", detail: agg.l1 },
      { n: "02", name: "Risk score", desc: "Weighted count-based score, 0-100. Auxiliary - never decides the verdict.", status: "idle", detail: agg.l2 },
      { n: "03", name: "Anomaly", desc: "Flags deviation from a statistical baseline of 80 synthetic benign runs.", status: "idle", detail: agg.l3 },
    ];
  }
  document.getElementById("lanes").innerHTML = lanes.map(l => `
    <div class="lane">
      <div class="lane-head"><div class="n mono">Layer ${l.n}</div><h3>${l.name}</h3><p>${l.desc}</p></div>
      <div class="lane-status">
        <span class="lane-badge ${l.status}">${l.status === "fired" ? "FIRED" : l.status === "clear" ? "clear" : "-"}</span>
        <span class="lane-detail">${l.detail}</span>
      </div>
    </div>
  `).join("");
}

let sortKey = "risk_score", sortAsc = false;
let activeOutcomeFilter = null, activeTagFilter = null;
let selectedId = null;

function allTags() {
  const s = new Set();
  DATA.results.forEach(r => r.owasp_tags.forEach(t => s.add(t)));
  return [...s].sort();
}
function allOutcomes() {
  return [...new Set(DATA.results.map(r => r.outcome))].sort();
}

function renderFilters() {
  const chips = [];
  allOutcomes().forEach(o => chips.push(["outcome", o]));
  allTags().forEach(t => chips.push(["tag", t]));
  document.getElementById("filters").innerHTML = chips.map(([kind, val]) => {
    const active = (kind === "outcome" && activeOutcomeFilter === val) || (kind === "tag" && activeTagFilter === val);
    return `<span class="chip ${active ? "active" : ""}" data-kind="${kind}" data-val="${val}">${val}</span>`;
  }).join("");
  document.querySelectorAll(".chip").forEach(el => {
    el.addEventListener("click", () => {
      const kind = el.dataset.kind, val = el.dataset.val;
      if (kind === "outcome") activeOutcomeFilter = (activeOutcomeFilter === val) ? null : val;
      else activeTagFilter = (activeTagFilter === val) ? null : val;
      renderFilters();
      renderTable();
    });
  });
}

function filteredSorted() {
  let rows = DATA.results.filter(r =>
    (!activeOutcomeFilter || r.outcome === activeOutcomeFilter) &&
    (!activeTagFilter || r.owasp_tags.includes(activeTagFilter))
  );
  rows = rows.slice().sort((a, b) => {
    let av = a[sortKey], bv = b[sortKey];
    if (sortKey === "owasp_tags") { av = av.join(","); bv = bv.join(","); }
    if (av < bv) return sortAsc ? -1 : 1;
    if (av > bv) return sortAsc ? 1 : -1;
    return 0;
  });
  return rows;
}

function renderTable() {
  const rows = filteredSorted();
  const maxRisk = Math.max(...DATA.results.map(r => r.risk_score));
  document.getElementById("scenario-body").innerHTML = rows.map(r => `
    <tr class="srow ${r.scenario_id === selectedId ? "selected" : ""}" data-id="${r.scenario_id}">
      <td class="mono">${r.scenario_id}</td>
      <td><span class="pill ${r.true_label}">${r.true_label}</span></td>
      <td><span class="pill ${r.verdict}">${r.verdict}</span></td>
      <td class="mono">${r.outcome}</td>
      <td><div class="risk-bar-wrap"><span class="mono">${r.risk_score}</span><span class="risk-bar"><span style="width:${(r.risk_score / maxRisk * 100).toFixed(0)}%"></span></span></div></td>
      <td class="tag-list">${r.owasp_tags.join(", ") || "-"}</td>
    </tr>
    <tr class="detail-row"><td colspan="6"><div class="detail-body" id="detail-${r.scenario_id}">${renderDetail(r)}</div></td></tr>
  `).join("");

  document.querySelectorAll(".srow").forEach(el => {
    el.addEventListener("click", () => {
      const id = el.dataset.id;
      const wasOpen = selectedId === id;
      document.querySelectorAll(".detail-body.open").forEach(d => d.classList.remove("open"));
      document.querySelectorAll(".srow.selected").forEach(d => d.classList.remove("selected"));
      if (wasOpen) {
        selectedId = null;
        renderLanes(null);
      } else {
        selectedId = id;
        el.classList.add("selected");
        document.getElementById(`detail-${id}`).classList.add("open");
        renderLanes(DATA.results.find(r => r.scenario_id === id));
      }
    });
  });

  document.querySelectorAll("table.scenarios th[data-key]").forEach(th => {
    th.classList.toggle("sorted", th.dataset.key === sortKey);
    th.classList.toggle("asc", th.dataset.key === sortKey && sortAsc);
    th.onclick = () => {
      if (sortKey === th.dataset.key) sortAsc = !sortAsc;
      else { sortKey = th.dataset.key; sortAsc = false; }
      renderTable();
    };
  });
}

function renderDetail(r) {
  const reasons = r.reasons.length
    ? r.reasons.map(x => `<div class="reason">[${x.rule}] ${x.detail}</div>`).join("")
    : `<div class="clear-line">No Layer-1 rule fired.</div>`;
  const layer3 = r.layer3
    ? (r.layer3.fired ? `<div class="reason">${r.layer3.detail}</div>` : `<div class="clear-line">${r.layer3.detail}</div>`)
    : "n/a";
  const steps = r.action_log.steps.map(s =>
    `<div class="step-line">[${s.i}] <span class="tool">${s.tool}</span> &middot; prov=${s.data_provenance || "-"} &middot; external=${s.destination_external ?? false}</div>`
  ).join("");
  return `
    <h4>Task</h4><div>${r.task}</div>
    <h4>Layer 1 reasons</h4>${reasons}
    <h4>Layer 3 (auxiliary)</h4>${layer3}
    <h4>Action log</h4>${steps}
  `;
}

function renderOwasp() {
  const counts = {};
  DATA.results.forEach(r => r.owasp_tags.forEach(t => counts[t] = (counts[t] || 0) + 1));
  const max = Math.max(1, ...Object.values(counts));
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  document.getElementById("owasp-rows").innerHTML = entries.map(([tag, n]) => `
    <div class="owasp-row">
      <div class="owasp-tag mono">${tag}</div>
      <div class="owasp-track"><span style="width:${(n / max * 100).toFixed(0)}%"></span></div>
      <div class="owasp-count mono">${n}</div>
    </div>
  `).join("");
}

renderStats();
renderLanes(null);
renderFilters();
renderTable();
renderOwasp();
</script>
</body>
</html>
"""


def main() -> None:
    data = build_data()
    html = TEMPLATE.replace("__DATA_JSON__", json.dumps(data)).replace(
        "__GENERATED_AT__", data["generated_at"]
    )
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"Wrote {OUTPUT_PATH} ({len(html)} bytes)")


if __name__ == "__main__":
    main()
