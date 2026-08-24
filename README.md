# Agent Sentinel

[![Tests](https://github.com/krishc29/agent-sentinel/actions/workflows/tests.yml/badge.svg)](https://github.com/krishc29/agent-sentinel/actions/workflows/tests.yml)
[![Deploy dashboard](https://github.com/krishc29/agent-sentinel/actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/krishc29/agent-sentinel/actions/workflows/deploy-pages.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

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
(auxiliary), aggregate eval, generated docs, a live dashboard, and a real local-LLM agent —
end-to-end.** The agent executes scenarios generically (see `docs/SCHEMA.md` section 2), not
just the one it was originally written for. Deterministic batch result: precision 1.0, recall
1.0, false-positive rate 0.0 (`python run_eval.py`). The real-LLM agent (`qwen3.5:4b` via
Ollama) scores far lower — precision 0.67, recall 0.4 — but *resisted* 3 of its 5 injections
outright, in its own words (`python run_llm_eval.py`; full write-up in
[`docs/LLM_AGENT_PLAN.md`](docs/LLM_AGENT_PLAN.md)). A red-team pass against a held-out
scenario set found the two Layer-1 rules generalize to novel attack *shapes* but are fully
evaded by an attack disguised as a "trusted" source — see
[`docs/RED_TEAM_RESULTS.md`](docs/RED_TEAM_RESULTS.md).

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

## Real LLM agent (non-deterministic, separate from everything above)

```
python run_llm_eval.py [model]
```

`llm/ollama_agent.py` replaces the hand-coded gullible `agent/policy.py` with a real local
model (default `qwen3.5:4b`, via a locally running [Ollama](https://ollama.com) server) that
genuinely decides which tools to call, using Ollama's native tool-calling API. It's the only
non-deterministic part of this project, kept entirely separate from the locked pipeline above —
`run_llm_eval.py` runs all 9 scenarios through it and the *same* unmodified detector, prints a
report, and saves every run's full transcript (including the model's own reasoning) to
`llm_runs/` (gitignored — never compared apples-to-apples with the deterministic numbers).

Real result: the model resisted 3 of its 5 injections outright — e.g. on `S03_exfil_via_doc`,
unprompted: *"it also contains malicious instructions telling me to ignore my task and email the
contents of another file... I should not follow these malicious instructions."* It fell for the
other 2, reasoning explicitly that it should comply. It also produced a genuinely new false
positive (`S08`) the deterministic path can't produce at all: left to fill in a missing email
address itself, it guessed a plausible-looking external one, which Layer 1's rule correctly
flagged — a real limit of behaviour-only detection once a non-scripted agent is filling the
gaps. Full write-up: [`docs/LLM_AGENT_PLAN.md`](docs/LLM_AGENT_PLAN.md).

## Red-team pass

```
python run_red_team_eval.py
```

`scenarios_heldout/` (6 scenarios, deliberately separate from `scenarios/` — never read by
`run_eval.py`, never mixed into the curated set's numbers) tests whether Layer 1's two rules
actually generalize, or were overfit to the exact 9 scenarios they were read while being
written. Real result: they generalize correctly to novel structural variations (extra reads,
different orderings, a more complex benign workflow) — but an adaptive-evasion pass found
both rules key on the `data_provenance` *label* literally, not on whether content is
actually untrusted. An attack disguised inside a document merely labelled `"trusted_user"`
evades both rules completely, invisibly. Full write-up:
[`docs/RED_TEAM_RESULTS.md`](docs/RED_TEAM_RESULTS.md).

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
