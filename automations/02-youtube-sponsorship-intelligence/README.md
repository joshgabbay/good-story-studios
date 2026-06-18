# YouTube Sponsorship Intelligence Digest

Turns Joshua Cohen's monthly sheet of sponsored YouTube videos into a ranked brand-intelligence
report: who's sponsoring the most (long-form), how that changed month-over-month, and which of
those brands Good Story already has a relationship with. Delivered by email + Slack.

**Status:** v1 engine complete and tested (44 tests). Live ingest, HubSpot, Slack, and email are
isolated stubs — wire them at deploy (see "Going live"). Design spec + plan are in
`docs/superpowers/`.

## Quick start (local)

```bash
cd automations/02-youtube-sponsorship-intelligence
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests/ -q          # run the test suite

# Run a month (baseline), then the next month (comparison):
.venv/bin/python -m pipeline.run --csv sample/2026-05_sample.csv --month 2026-05 \
  --db history.db --out may.html --month-label "May 2026" --generated-date "June 1, 2026"
.venv/bin/python -m pipeline.run --csv sample/2026-06_sample.csv --month 2026-06 \
  --db history.db --out june.html --month-label "June 2026" --generated-date "July 1, 2026"
```

The same `--db` file carries history across months (that's what powers month-over-month).
Open the `--out` HTML to see the report; the Slack text prints to stdout.

## How it works

`pipeline/`: `transform` (CSV → canonical brand-resolved rows) → `engine` (SQLite history +
ranking + month-over-month) → `relationships` (HubSpot lookup; stubbed) → `report` (HTML + Slack)
→ `delivery` (send; dry-run stub) → `run` (orchestrator). **All counting/ranking is deterministic
code — the model never tallies.** At 25k rows a two-month run takes ~0.6s.

## Configuration (`config.json`)

| Key | Meaning |
|-----|---------|
| `column_map` | Maps our fields (video/channel/sponsor/date/length/long_form_flag) to the sheet's actual header names. |
| `long_form` | `{"mode":"threshold","length_threshold_seconds":600}` or `{"mode":"flag"}` (uses `long_form_flag`). |
| `multi_sponsor.delimiter` | Splits multiple sponsors in one cell. |
| `top_n` | Brands to rank (default 25). |
| `audience` | `internal` (keeps the "review for aliasing" section) or `external` (omits it for clients). |
| `final_recipient`, `slack_channel` | Delivery targets (set at go-live). |

## Monthly operator workflow

1. Export Cohen's sheet to CSV; run the month (as above).
2. Skim the **"Top unmatched brands"** section — brand names not yet in the alias map.
3. For any that are real brands/variants, fold them in:
   ```bash
   python tools/alias_add.py "Magic Spoon" magicspoon "MagicSpoon"
   ```
   Next month they'll be counted under the canonical brand instead of fragmenting.

## Files

- `pipeline/` — the engine (see above) + `history_store` (Supabase sync seam) + `alias_admin`.
- `config.json`, `brand_aliases.seed.json`, `known_brands.json` — config + data.
- `sample/`, `tools/gen_sample.py` — demo data + a generator for scale testing.
- `sql/supabase_schema.sql` — Postgres DDL for the durable cross-month store.
- `tests/` — 44 tests; `tests/fixtures/aliases.json` is the test alias map (decoupled from the
  production seed so the seed can grow freely).
- `spec.md`, `routine.md`, `routine-prompt.txt` — as-built notes + deploy docs.

## Going live (deferred wiring — the seams are in place)

1. **Sheet** — confirm the real headers → set `column_map` and the long-form column.
2. **HubSpot** — replace `relationships.lookup_relationships` internals with a HubSpot MCP query
   (same signature).
3. **Slack** — implement `delivery._post_to_slack`.
4. **Email** — implement `delivery._send_email_via_supabase` (reuse the film-slate
   `email_queue` + edge-function pattern); set `final_recipient`; flip `deliver(dry_run=False)`.
5. **History** — apply `sql/supabase_schema.sql`; wire `history_store.pull_prior_counts` /
   `push_month_counts` to Supabase (SELECT + upsert) around the run.
6. **Deploy** — cloud routine (same `/schedule` → `RemoteTrigger` shape as the film slate);
   first run owner-only, then flip to the real recipient.
