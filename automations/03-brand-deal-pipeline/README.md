# Brand Deal Pipeline (Priority 1)

> **Status: PLANNING — not started.** Decomposed and scoped; paused mid-brainstorm 2026-06-18,
> resuming next week. No code or spec yet. This folder is the placeholder for the sub-project.

The top-priority automation from `good_story_context.md` §9 (see also `AUTOMATIONS.md` →
"Automation 1"). Inbound brand emails become tracked HubSpot deals, mirrored to Sheets and
announced in Slack, with stale-deal follow-ups auto-drafted.

```
Inbound brand email
   │
   ▼
[1] Parse brand + deal info            ← the core engine (LLM extraction)  ◀ BUILD FIRST
   │
   ▼
[2] Create/update HubSpot deal/contact ← source of truth
   │            │               │
   ▼            ▼               ▼
[3] Slack     [4] Google      [5] Stage tracking + stale-deal
   alerts        Sheets mirror     follow-up draft generation
```

## Decomposition (each is its own spec → plan → build)
1. **Inbound email → structured deal extraction (the parser)** — chosen as the first build;
   everything downstream feeds off it. Fully buildable + testable on sample emails now.
2. HubSpot sync (deal/contact upsert) — source of truth.
3. Slack alerts on major events (deal closed, new deal, stage change).
4. Google Sheets mirror.
5. Stale-deal detection + follow-up draft generation.

## Approach (same proven pattern as Automation #2)
Build the buildable cores now; **stub the connectors** (HubSpot / Slack / Sheets / Gmail) behind
clean interfaces and wire them at deploy. Likely a dependency-light Python `pipeline/` with
LLM-based extraction (latest Claude model), validated against sample emails.

## Key rules
- Tag the brand from the email **content, not the sender** (an agency emailing *about* OpenAI →
  tagged OpenAI); keep the original sender for reference.
- **HubSpot is the source of truth** — Slack and Sheets are downstream mirrors/notifications.

## Open questions to resume with
1. Email input source for the build-now phase (paste raw text / drop `.eml`/JSON files / Gmail MCP).
2. Extraction field schema (brand, contact/agency, creator(s) requested, deal type, budget/rate,
   deliverables, timeline, summary, confidence signal).
3. Brand resolution — match against a maintained known-brand list (reuse the alias-map idea from
   Automation #2) and the creator roster.
4. Scope vs Inbound Email Triage (Priority 3): extraction-only (assume brand-relevant) vs also
   classify legit-deal/junk. Lean: extraction-only with a confidence signal.

When resuming: brainstorm → spec (`docs/superpowers/specs/`) → plan → subagent-driven build,
exactly like `../02-youtube-sponsorship-intelligence/`.
