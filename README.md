# Agent Sentinel

Agent Sentinel is a **defensive AI-agent security lab**. A simulated AI agent with fake tools is
run through pre-labelled scenarios. Some scenarios are ordinary jobs; some contain a hidden
**prompt injection** (a secret instruction buried inside a document the agent reads) that tricks
the agent into misusing its tools. A layered **detection engine** reads the agent's action log,
decides **safe** or **attack**, explains which signals fired, and an **evaluation harness** grades
that verdict against the known-true label. Everything is sandboxed and fictional — the fake tools
never do anything real; they only log that they were called. No network calls, no live targets,
no offensive tooling.

**The one question the project answers:** *When an AI agent is manipulated, can a layered detection
system catch it — and how well?*

## Current status

**9 scenarios (5 attack, 4 benign), 2 Layer-1 rules, Layer 2 scoring, Layer 3 anomaly detection
(auxiliary), aggregate eval, generated docs, and a live dashboard — end-to-end.** The agent
executes scenarios generically (see `docs/SCHEMA.md` section 2), not just the one it was
originally written for. Current batch result: precision 1.0, recall 1.0, false-positive rate 0.0
across the set (`python run_eval.py`). Still ahead: a real-LLM (Ollama) agent and a held-out/
red-team pass — see `docs/LLM_AGENT_PLAN.md` and `docs/RED_TEAM_PLAN.md` for the design work
already done toward both.

## How to run

```
python run.py
```

This runs the agent on `scenarios/S03_exfil_via_doc.json` and prints three things:

1. **The action log** the agent produced — it should contain a `send_email` step with
   `destination_external: true`, i.e. the agent was genuinely fooled into exfiltrating a secret.
2. **The detector verdict** — `attack`, with the `untrusted_read_then_external_send` rule fired.
3. **The eval outcome** — `true_positive`, `correct = true`.

Uses only the Python standard library (3.11+). The run is fully deterministic: the same scenario
in always produces an identical action log out.

## Batch evaluation

```
python run_eval.py
```

Runs every scenario in `scenarios/` through the same agent -> detector -> eval pipeline and
prints a per-scenario table plus aggregate precision / recall / false-positive rate / accuracy
across the set. A copy of the report is written to `results/eval_report.json` (generated output,
not committed — see `.gitignore`).

## Layer 3 (auxiliary — wired in, does not drive the verdict)

```
python build_baseline.py
```

`detector/anomaly.py` flags an action log as anomalous by comparing its feature vector
(`detector/features.py`) against a statistical baseline built from 80 deterministic synthetic
benign scenarios (`eval/synth_benign.py`) — per-feature mean/stdev, z-score flagging. The baseline
is committed at `detector/baseline.json` (regenerate it with the command above; same seed always
reproduces it exactly).

`detector/engine.judge(log, baseline)` includes its result as `verdict["layer3"]`, but Layer 1's
rules alone still decide `verdict["verdict"]` — Layer 3 under-recalls on its own by design. Real
finding from validating it against the hand-labelled scenarios: it catches the malicious delete
scenario, but misses the 4 exfiltration scenarios, because its feature vector is pure counts with
no notion of step order — see [`docs/LAYER3_NOTES.md`](docs/LAYER3_NOTES.md) for the full
write-up (including the exact z-scores) and the rest of this build's engineering log.

## Generated documentation

```
python docs/generate_owasp_mapping.py
python docs/generate_incidents.py
```

Both read the live pipeline (not a stale file) and write committed, regenerable docs:
[`docs/owasp_mapping.md`](docs/owasp_mapping.md) (scenarios grouped by OWASP LLM Top 10 tag) and
`docs/incidents/<scenario_id>.md` (one write-up per scenario — task, fired rules, Layer 3 result,
full action log).

## Dashboard

**Live:** https://krishc29.github.io/agent-sentinel/

```
python site/generate.py
```

`site/generate.py` bakes the live pipeline's output (same as `run_eval.py`) directly into a
single, self-contained `site/index.html` — no server, no fetch, works standalone opened straight
from disk. One cohesive page: headline aggregate stats, a "Three layers, one verdict" section
that live-links to whichever scenario is selected, and a sortable/filterable scenario table that
expands inline into the full action log, fired rules, and Layer 3 result. Pure standard library,
like everything else in this project. `.github/workflows/deploy-pages.yml` regenerates and
redeploys it automatically on every push to `master`.

## Key concept

- **Scenarios are inputs** (`scenarios/`): the world the agent wakes up in.
- **Action logs are outputs**: what the agent actually did, recorded in the trace schema.
- **`true_label`** (the ground truth) is used **only by the eval harness**. The detector never
  reads it — it must catch the attack from behaviour alone.

See [`docs/SCHEMA.md`](docs/SCHEMA.md) for the trace schema and scenario format (the contract).
