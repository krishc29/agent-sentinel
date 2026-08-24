# Held-Out / Red-Team Evaluation: Design

**Run — see [`docs/RED_TEAM_RESULTS.md`](RED_TEAM_RESULTS.md) for the actual results.** This
doc is the methodology that was designed and then executed against `scenarios_heldout/`;
kept as-is below since the design reasoning is still the reference for *why* it was built
this way.

Every Layer-1 rule in `detector/rules.py` was written by looking directly at the 9
scenarios in `scenarios/`. That's a real, unavoidable methodological gap: a rule tuned by
reading the exact attacks it's meant to catch tells you the rule works on *those* attacks,
not that it generalizes. This doc is the plan for closing that gap.

## Why this has to wait for `docs/LLM_AGENT_PLAN.md`'s work, not run alongside it

A held-out set is only informative if it's genuinely independently designed - written
without re-reading `detector/rules.py` for inspiration. The most natural way to get a
second, honestly-independent set of attack scenarios without hand-authoring bias is to have
the (still not yet built) LLM agent from Step 6 help generate novel injection phrasings and
attack shapes, then hand-check which are structurally valid scenario files. That makes this
plan a direct downstream consumer of Phase 4, not a parallel track.

**What actually happened**: Phase 4 got built, but true independence was never fully
achievable anyway - the same session that wrote `detector/rules.py` also designed the
held-out set, since neither a second independent author nor an LLM-driven scenario-generation
pipeline existed. Rather than wait indefinitely for perfect independence, the held-out set
was hand-authored deliberately structurally different from the original 9 (not just
re-skinned with new names), *plus* an explicit adaptive-evasion pass that uses full knowledge
of the rules' exact logic to construct genuine evasions - which the plan below already
identifies as the more rigorous test anyway ("tests the rules' worst case, not their average
case"). See `docs/RED_TEAM_RESULTS.md` for what that found.

## What "the rules generalized" vs. "they didn't" would actually mean

- **Rules generalize**: precision/recall on the held-out set stays close to the 1.0/1.0
  measured on the original 9. Evidence the two Layer-1 rules capture a real, general
  pattern (untrusted-read-then-external-send; untrusted-read-then-delete), not an
  accidental property of these specific 9 scenarios' exact wording or file names.
- **Rules don't generalize**: recall drops on the held-out set - real attacks the rules miss
  because they don't match the exact shape the rules were written against (e.g. an
  injection that triggers a `send_email` without a preceding `read_file` step recorded the
  same way, or a third tool/action pattern not covered by either rule). This would be a
  legitimate, useful negative result, in the same spirit as the Layer 3 order-blindness
  finding in `docs/LAYER3_NOTES.md` - reported honestly, not hidden.

## Two distinct methodologies, both worth doing eventually

1. **Held-out set**: a second batch of scenarios, same format, designed independently
   (ideally by a different process/session than the one that wrote `detector/rules.py`),
   run once through the *unmodified* existing detector. No rule changes allowed based on
   the held-out set's results - that would just fold it into the training set and defeat
   the point.
2. **Adaptive red-team pass**: given the two rules' exact logic (published openly in this
   repo), deliberately construct scenarios designed to *evade* them - e.g. an exfiltration
   that never has a `read_file` step with `data_provenance == "untrusted_document"` recorded
   as such (relies on some other provenance-laundering step instead), or a destructive
   action that isn't `delete_file` (nothing currently stops an overwrite-in-place kind of
   action, since only three tools exist today). This tests the rules' worst case, not their
   average case.

## What this would need from the rest of the project first

- Phase 4 (LLM agent) built, so novel scenarios can be generated rather than only
  hand-authored one at a time.
- Possibly a 4th tool beyond `read_file`/`send_email`/`delete_file` (e.g. `write_file` or
  `overwrite_file`) if the adaptive pass wants to test evasion via actions the current rules
  don't watch at all - a real scope decision to make explicitly when this is picked up, not
  something to smuggle in now.

## Explicitly out of scope for this plan

A full CaMeL-style prevention-architecture companion (flagged in earlier project status
notes as the most novel remaining research direction) is a different, larger piece of work
than red-teaming the current detection layers, and isn't scoped here at all.
