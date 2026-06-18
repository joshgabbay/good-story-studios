# YouTube Sponsorship Intelligence — Production Routine (planned)

NOT YET DEPLOYED as a cloud routine — v1 is the local `pipeline/` validated against `sample/`.
Deploy once the data source + HubSpot + Slack connectors exist.

## Planned shape
- Cloud routine (CCR), repo cloned, MCP connectors: Supabase, HubSpot, Slack, (Gmail optional).
- Trigger: manual for now (manual CSV ingest); cron once ingest is automated.
- Steps: ingest month CSV → `pipeline` processing → relationships via HubSpot → render → email + Slack.
- First production run: deliver to owner only, then flip `final_recipient` / `slack_channel`.

## To finalize at deploy
- routine-prompt.txt (draft alongside) → fill recipient/channel, confirm sheet column_map.
- Supabase project + tables (DDL in plan Task 7).
