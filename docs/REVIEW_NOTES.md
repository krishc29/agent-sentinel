# Tier 1 + Full-Codebase Review — 2026-08-23

A critical re-review of everything built this session, done at your request rather than
trusting the original build-session writeup. Every file below was re-read fresh, not
recalled from memory. Full detail is in the git history (`git log`); this is the summary.

## What was rechecked

- All 5 Tier 1 deliverables: `detector/engine.py`'s Layer 3 wiring, `run.py`, the extended
  `run_eval.py`, both doc generators (`docs/generate_owasp_mapping.py`,
  `docs/generate_incidents.py`), and `dashboard/app.py`.
- The rest of the codebase not touched this session but not re-verified either:
  `agent/policy.py`, `agent/runner.py`, `agent/tools.py`, `detector/rules.py`,
  `detector/scoring.py`, `detector/features.py`, `eval/harness.py`, `eval/metrics.py`,
  `eval/synth_benign.py`, `build_baseline.py`, all 9 scenario files, `llm/ollama_agent.py`,
  `README.md`, `requirements.txt`, `.gitignore`.

## Real issues found and fixed (commits `e17bf6a`, `a5cc945`, `e6602fd`)

1. **`detector/anomaly.py`'s module docstring was stale** — still said "Not yet wired into
   detector/engine.py," left over from before that wiring actually happened earlier in the
   session. Corrected.
2. **`build_baseline.py`'s module docstring had the same staleness** — same "not wired in"
   claim, same fix. Found on the second, broader pass — the first Tier-1-only recheck
   missed it because `build_baseline.py` wasn't part of Tier 1's five deliverables.
3. **`run_eval.py`'s `run_all_scenarios()` was redundantly re-parsing scenario JSON files**
   it had already loaded — opening each file a second time just to read `owasp_tags`/`task`
   back out, when `agent/runner.py` already copies both onto the action log. Not a
   correctness bug (same data, same source), but real duplicate logic. Simplified to read
   both off the log instead.
4. **`docs/generate_owasp_mapping.py` inserted free-text task strings directly into markdown
   table cells with no escaping.** Harmless today (no current task contains a `|`
   character) but a latent bug: a future scenario whose task text contained a pipe would
   silently corrupt the generated table. Added an escape helper.

## A significant finding from actual research, not code inspection

5. **All 5 attack scenarios' `owasp_tags` used the old (2023) OWASP Top 10 for LLM
   Applications numbering.** Researched the real, current standard rather than trusting
   what was already in the repo: the 2025 v2.0 revision (published 2024-11-18)
   substantially renumbered categories. `LLM06_sensitive_disclosure` is now `LLM02`;
   `LLM08_excessive_agency` is now `LLM06`. Fixed across all 5 scenarios, the locked schema
   example (regenerated from a live run, same pattern as the earlier schema fix),
   `docs/SCHEMA.md`'s embedded copy, and both regenerated docs. Commit `a5cc945`.

## What was checked and found correct (no changes)

- `agent/policy.py`, `agent/runner.py`, `agent/tools.py` — the generic-execution refactor
  from earlier in the session holds up; no bugs found.
- `detector/rules.py`, `detector/scoring.py`, `detector/features.py` — rule logic, weights,
  and feature extraction all check out against a fresh read.
- `eval/harness.py`, `eval/metrics.py` — both still exactly as scoped, no drift.
- `eval/synth_benign.py` — determinism and the zero-variance `delete_count` property both
  hold as documented.
- `llm/ollama_agent.py`, `README.md`, `requirements.txt`, `.gitignore` — accurate as of this
  recheck.

## Verification after every fix

- `python -m unittest discover tests` — 17/17 passing throughout.
- `docs/owasp_mapping.md` confirmed to regenerate byte-identical after the pipe-escaping fix
  (proves it was a safe no-op on current data, not a behavior change).
- `detector/baseline.json` re-verified exactly reproducible on a fresh `build_baseline.py`
  run (byte-for-byte diff against the committed file).
- `python run.py` / `python run_eval.py` both still run clean after every change.
- Repo-wide grep for the old OWASP tag strings and any remaining "not wired in" language
  came back empty after all fixes landed.
