# Automation #2 — YouTube Sponsorship Intelligence

Design spec: `docs/superpowers/specs/2026-06-18-youtube-sponsorship-intelligence-design.md`
Plan: `docs/superpowers/plans/2026-06-18-youtube-sponsorship-intelligence.md`

## As-built (v1, local pipeline)
- Dependency-light Python (`pipeline/`): `transform` → `engine` (sqlite history) → `relationships`
  (stub) → `report` → `run`.
- Deterministic counting/ranking/MoM in code; LLM never tallies.
- Surfaces top unmatched (fallback) brands each month as alias candidates so the alias map
  improves over time and counts stop fragmenting.
- Runs end-to-end against `sample/` with `python -m pipeline.run`.

## Deferred wiring (when access exists)
- Ingest: replace manual CSV with Sheets/Gmail MCP (rows still land in the same local SQLite compute).
- History store: **SQLite stays the compute engine.** Supabase is only the durable cross-month
  store: at the start of a run, pull prior months' `brand_monthly_counts` from Supabase into the
  local SQLite DB; at the end, upsert the new month's `brand_monthly_counts` back to Supabase. The
  tested `pipeline/` code is unchanged — we only add a Supabase pull-in/push-out around it.
- `relationships.lookup_relationships`: swap stub internals for a HubSpot MCP query (same signature).
- Delivery: email via Supabase send pattern; Slack post via Slack connector.
- Config: set `final_recipient`, `slack_channel`; confirm `column_map` + long-form column from the real sheet.
