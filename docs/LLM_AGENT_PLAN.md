# Phase 4 — A Real LLM Agent: Design

`agent/policy.py` is a small, deterministic, hand-coded stand-in for an AI agent: it's
gullible *by construction* — it always obeys a scenario's `injected_action` if
`hidden_instruction` is set, because that's literally what the Python code does. It has
never had to actually be fooled, because it can't help but be fooled. A real LLM
(qwen3.5:4b, installed locally via Ollama) genuinely deciding what to do, and genuinely
being manipulated or not, is a different and more interesting experiment. This doc is the
design for that — not the implementation. Foundation, not a finished feature.

## Why this can't just replace `agent/policy.py`

Two hard constraints this project has kept since the very first commit break the moment a
real model is in the loop:

1. **Determinism.** "Same scenario in -> identical action log out" is asserted by
   `tests/test_regression.py` and is how every regression in this project gets caught. An
   LLM's output is not guaranteed identical run to run, even at temperature 0 (batching,
   backend nondeterminism, model updates). An LLM-driven run needs its own clearly
   separate, clearly labeled non-deterministic code path — never a silent swap-in for
   `agent/policy.py`.
2. **The detector must never read `true_label`, and the agent must never know it's being
   tested.** This still holds with a real LLM; nothing here changes it. What's new is that
   the LLM *might resist the injection on its own* (general safety training), which the
   current hand-coded gullible policy structurally cannot do. That's a real, useful
   difference to be able to observe and report - not something to route around.

## The interface it must satisfy

Same shape as `agent.policy.run_policy` (`agent/policy.py`), so it's a drop-in *alternative*
policy, not a rewrite of anything else in `agent/`:

```python
def run_llm_policy(
    task: str,
    files: Dict[str, Any],
    primary_file: str,
    log: ToolLog,
    model: str = "qwen3.5:4b",
) -> None:
    ...
```

Crucially: **the model's output text is never executed.** It gets parsed into a small,
constrained set of structured tool calls, and those calls are dispatched through the exact
same `agent/tools.py` stubs every other policy uses (`tools.read_file`, `tools.send_email`,
`tools.delete_file`, all still CRITICAL-SAFETY-PROPERTY no-ops - see `agent/tools.py`'s own
docstring). A model that hallucinates a tool that doesn't exist, or malformed JSON, is a
parse failure to handle gracefully (log nothing, or log a `permission: "blocked"` step -
schema already supports that value even though nothing uses it yet), never a crash and
never a bypass of the stub layer.

## Prompt design

- **System prompt**: describes the three available tools and their exact argument shapes
  (reusing section 1.3 of `docs/SCHEMA.md` almost verbatim - the trace schema's per-tool
  `args` shapes already are the tool contract), and instructs the model to respond with a
  structured call (JSON) rather than prose.
- **User content**: the scenario's `task`, followed by the `primary_file`'s content. Nothing
  about `hidden_instruction`, `true_label`, or `injected_action` is ever included - those
  are scenario-authoring/grading concepts, invisible to the agent, same as today.
- **Loop**: read -> (tool result becomes new context) -> decide next call, or stop, capped
  at a fixed max-steps (e.g. 6) so a confused model can't loop forever. Every call in the
  loop, successful or not, is one record in `log`.

## Which model, and why

`qwen3.5:4b` — already pulled locally, small enough to iterate on quickly. `qwen3-coder:30b`
is also available locally for a slower, more capable comparison run once the pipeline
itself is proven out. Both run fully offline via the local Ollama server - no external API
calls, consistent with the project's "sandboxed, no live targets" property elsewhere.

## What running this would actually measure

Re-run the same 9 scenarios (or a subset) through `run_llm_policy` instead of `run_policy`,
through the *same* unmodified detector. Two genuinely open questions, not assumed answers:

- Does the LLM fall for the same injections the hand-coded policy is designed to fall for,
  less often, more often, or on different scenarios than expected?
- Does the *detector* still work correctly when the log it's reading was produced by a real
  (imperfectly predictable) agent instead of a scripted one?

Both are real findings either way, in the same spirit as `docs/LAYER3_NOTES.md`: report what
actually happens, not what makes the numbers look best.

## Explicitly deferred to actual implementation time

- The exact JSON call-format and its parser/validator
- Retry/repair behavior on malformed model output
- Where LLM-driven runs get stored (separate from `scenarios/`+`results/`, since they're not
  deterministic and shouldn't be compared apples-to-apples with the batch eval numbers)
- Whether `eval/harness.py` needs any change at all (current expectation: no - it only reads
  `action_log["true_label"]` and a verdict, neither of which cares how the log was produced)
