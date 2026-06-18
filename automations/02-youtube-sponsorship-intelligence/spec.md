# Automation #2 — YouTube Sponsorship Intelligence

Design spec: `docs/superpowers/specs/2026-06-18-youtube-sponsorship-intelligence-design.md`
Plan: `docs/superpowers/plans/2026-06-18-youtube-sponsorship-intelligence.md`

## As-built (v1, local pipeline)
- Dependency-light Python (`pipeline/`): `transform` → `engine` (sqlite history) → `relationships`
  (stub) → `report` → `delivery` (dry-run stub) → `run`.
- Deterministic counting/ranking/MoM in code; LLM never tallies.
- Surfaces top unmatched (fallback) brands each month as alias candidates so the alias map
  improves over time and counts stop fragmenting (excludes already-established/known brands).
- `config.audience` (`internal`/`external`): the external report omits the internal
  "review for aliasing" section.
- Warning banner when the sheet has no length/long-form column (numbers not silently trusted).
- `brand_aliases.seed.json` pre-seeded with common YouTube sponsors; tests use
  `tests/fixtures/aliases.json` (decoupled from the production seed).
- Runs end-to-end against `sample/` with `python -m pipeline.run`. 41 tests.

## Deferred wiring (when access exists) — the seams are already in place
- Ingest: replace manual CSV with Sheets/Gmail MCP (rows still land in the same local SQLite compute).
- History store: **SQLite stays the compute engine.** Supabase is only the durable cross-month
  store (DDL in `sql/supabase_schema.sql`): at the start of a run, pull prior months'
  `brand_monthly_counts` from Supabase into the local SQLite DB; at the end, upsert the new month's
  counts back. The tested `pipeline/` code is unchanged — only a Supabase pull-in/push-out wraps it.
- `relationships.lookup_relationships`: swap stub internals for a HubSpot MCP query (same signature).
- Delivery: implement `delivery._send_email_via_supabase` (Supabase send pattern) and
  `delivery._post_to_slack` (Slack connector); flip `deliver(..., dry_run=False)`. `run.py` does
  not change.
- Config: set `final_recipient`, `slack_channel`, `audience`; confirm `column_map` + long-form
  column from the real sheet.
