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

**9 scenarios (5 attack, 4 benign), 2 Layer-1 rules, aggregate eval — end-to-end.** The agent
executes scenarios generically (see `docs/SCHEMA.md` section 2), not just the one it was
originally written for. Current batch result: precision 1.0, recall 1.0, false-positive rate 0.0
across the set (`python run_eval.py`). Still ahead: Layer 2 risk scoring, Layer 3 anomaly
detection, a Streamlit dashboard, and a real-LLM (Ollama) agent.

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

## Key concept

- **Scenarios are inputs** (`scenarios/`): the world the agent wakes up in.
- **Action logs are outputs**: what the agent actually did, recorded in the trace schema.
- **`true_label`** (the ground truth) is used **only by the eval harness**. The detector never
  reads it — it must catch the attack from behaviour alone.

See [`docs/SCHEMA.md`](docs/SCHEMA.md) for the trace schema and scenario format (the contract).
