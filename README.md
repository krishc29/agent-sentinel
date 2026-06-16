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

**Vertical slice — one scenario, one rule, end-to-end.** The full pipeline runs for a single
attack scenario (`S03_exfil_via_doc`) through a single Layer-1 detection rule. Later phases add
more rules, scoring/anomaly layers, aggregate metrics, a Streamlit dashboard, and a real-LLM agent.

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

## Key concept

- **Scenarios are inputs** (`scenarios/`): the world the agent wakes up in.
- **Action logs are outputs**: what the agent actually did, recorded in the trace schema.
- **`true_label`** (the ground truth) is used **only by the eval harness**. The detector never
  reads it — it must catch the attack from behaviour alone.

See [`docs/SCHEMA.md`](docs/SCHEMA.md) for the trace schema and scenario format (the contract).
