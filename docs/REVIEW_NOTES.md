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

---

# Second Pass — After the Dashboard Rebuild and LLM Agent — 2026-08-23

A further non-skimming pass over the whole repo (57 tracked files) after the static
dashboard, its GitHub Pages deploy, and the real LLM agent all landed. Same standard as the
first pass: re-read fresh, verify by running, not by recalling.

## What was checked this time

- Repo-wide grep for `TODO`/`FIXME`/`XXX`/`HACK` across every `.py`/`.md`/`.yml` file —
  **zero hits**.
- Regenerated `docs/owasp_mapping.md`, `docs/incidents/`, and `site/index.html` fresh and
  diffed against the committed versions — all three matched exactly (site's only diff was
  its own generation timestamp, discarded). Nothing has silently drifted out of sync with
  its source data.
- Fresh reads of `site/generate.py`, `.github/workflows/deploy-pages.yml`,
  `docs/LLM_AGENT_PLAN.md`, `docs/RED_TEAM_PLAN.md` end to end — no issues found.
- Found and removed a harmless but pointless leftover: an empty `dashboard/` directory
  (just a stray `__pycache__`) left behind after `dashboard/app.py` was deleted - never
  tracked by git, but confusing to find on disk.

**No new bugs found this pass** - a genuinely clean result, not a shortened review.

## What else can be added, what isn't necessary, what makes this stand out

Asked to assess honestly, not just list ideas.

### Already the standout material - don't undersell these

- **The Layer 3 negative result** (`docs/LAYER3_NOTES.md`): most portfolio projects hide
  where a component falls short. This one built Layer 3, found it structurally can't catch
  order-dependent attacks, and documented the exact z-scores proving it - then kept it
  anyway as auxiliary signal rather than deleting the evidence. That intellectual honesty
  *is* the differentiator, more than any single feature.
- **The real LLM agent's actual behavior** (`docs/LLM_AGENT_PLAN.md`, just written up): a
  model quoted refusing an injection in its own words, and a genuinely novel false-positive
  class (guessed email domain) that the deterministic path could never produce. This is a
  real, small research finding, not a demo — worth leading with if this project is ever
  shown to anyone.
- **Reproducibility discipline**: every generated artifact regenerates byte-identical from
  source (verified again this pass), the one non-deterministic path is clearly walled off
  and never silently mixed with the locked numbers. This is rarer than it should be even in
  professional codebases.

### Worth adding - concrete, cheap, real value

1. **A LICENSE file.** The repo is now public and has none. Costs one file, removes real
   ambiguity about reuse terms.
2. **A test-on-PR CI workflow.** The only GitHub Actions workflow that exists deploys the
   dashboard; nothing runs `python -m unittest discover tests` automatically. Trivial to
   add (pure stdlib, no install step, same shape as the existing deploy workflow) and closes
   an obvious gap for a project that otherwise takes testing seriously.
3. **Turn 2-3 of the LLM agent's actual observed behaviors into new deterministic
   scenarios.** `S05`'s partial engagement (read the secondary file, stopped short of
   sending) and `S08`'s ambiguous-recipient false positive are genuinely novel attack/edge
   shapes that weren't in the original 9 - and they're evidence-based rather than
   hand-invented, which is a more compelling way to grow the scenario library than writing
   more variations of the same exfiltration pattern.
4. **The held-out/red-team pass** (`docs/RED_TEAM_PLAN.md`) is still the single highest-value
   remaining piece: it's the only thing that would test whether Layer 1's rules actually
   generalize, versus just fit the 9 scenarios they were read while being written. Everything
   else on this list is polish; this one tests the project's actual scientific claim.
5. **Consider also mapping to OWASP's Agentic AI Top 10 (2026)** alongside the general LLM
   Top 10 already used - it's newer and purpose-built for autonomous, tool-using agents
   specifically (this project's exact subject), not general single-prompt LLM apps. A
   sharper, more current standard to sit alongside the existing one, not a replacement for it.

### Not necessary - real redundancy, not a defect

- **`docs/incidents/*.md` and the dashboard's per-scenario detail panel now show almost the
  same information twice**, in two different formats. Not wrong - the markdown files serve
  someone browsing the repo without running anything, the dashboard serves someone who wants
  to explore interactively - but it's worth being honest that this is two presentations of
  one dataset, not two independent features. If the project needs trimming later, this is
  the first place to look, not something to keep expanding.
- **Five separate engineering-log docs** (`LAYER3_NOTES.md`, `REVIEW_NOTES.md` (this one),
  `LLM_AGENT_PLAN.md`, `RED_TEAM_PLAN.md`) is still fine at the current size and each has a
  distinct, real purpose, but is worth watching - past a certain point this becomes a
  project that's more documentation than code. Not a problem today; a thing to notice if a
  sixth and seventh get added for smaller and smaller reasons.
