# Automation #2 — YouTube Sponsorship Intelligence Digest — Design

**Date:** 2026-06-18
**Status:** Design approved; spec under review
**Repo location (to build):** `automations/02-youtube-sponsorship-intelligence/`

## 1. Goal

Each month, turn Joshua Cohen's ~25,000-row sheet of sponsored YouTube videos into a ranked
brand-intelligence report for Good Story Studios: which brands are sponsoring the most, how that
changed versus prior months, and which of those brands Good Story already has a relationship with
(so the team can prioritize follow-up). Delivered automatically by email to the final recipient
and posted to a Slack channel.

## 2. Core principle

At 25k rows, **all counting/ranking/diffing is deterministic SQL — the LLM never tallies.** The
model only writes the narrative and assembles the HTML. This keeps the numbers exact and
reproducible.

## 3. Scope

### v1 (build now)
- Supabase data model + SQL processing engine (filter, normalize, count, rank, month-over-month).
- Brand-name normalization via an editable alias map.
- Baseline-forward history: the **first month is the baseline**, every month is stored, and all
  future reports compare against the prior month (and can compare against the baseline).
- Branded HTML report (ranked table, MoM arrows, relationship flags, short narrative).
- Delivery: email via the existing Supabase send pattern + Slack post.
- A synthetic sample CSV to build and test the whole pipeline end-to-end **without** the real sheet.
- Config-driven and broad: column mapping, long/short-form handling, multi-sponsor handling,
  thresholds, and Top-N are all parameters so we adapt to Cohen's real format without a rewrite.

### Deferred (design as pluggable now, wire in later when access exists)
These are **interfaces with stubs** in v1 so the pipeline runs end-to-end today; wiring them is a
connector/config change, not a rebuild:
- **Real data ingest** — manual CSV upload for now (Approach A). Sheets/Gmail MCP auto-ingest later.
- **HubSpot cross-reference** — discrete step behind a clean interface; stubbed (returns "no match"
  / reads an optional local brand list) until the HubSpot connector exists. Report renders with or
  without it.
- **Slack post** — step is built but no-ops/logs until the Slack connector is attached.
- **Final recipient + Slack channel** — config values, filled at go-live. Until then the report
  drafts to the owner only.

### Explicitly out of scope (v1)
- Automatic detection/parsing of Cohen's email attachment (that's the deferred Gmail/Sheets ingest).
- Any write-back to HubSpot (read-only cross-reference only).

## 4. Architecture (Approach A — Supabase/SQL engine)

```
You upload month's CSV  ──▶  Supabase staging  ──▶  sponsorship_rows (this month)
                                                       │
                          SQL: long-form filter, brand-alias normalize, dedupe
                                                       ▼
                                              brand_monthly_counts (history)
                                                       │
                          SQL: rank Top-N + month-over-month diff vs prior month
                                                       ▼
                          HubSpot (MCP, deferred/stubbed): relationship + stage flag
                                                       ▼
                          LLM: narrative + assemble branded HTML report
                                                       ▼
                          Auto-send email (Supabase edge fn)  +  Slack post (deferred/stubbed)
```

Runs as a cloud routine (CCR), **manually triggered** for now (manual ingest means there's no
point to a cron yet); becomes cron-eligible once ingest is automated. Same deployment shape as the
film-slate routine (`/schedule` → `RemoteTrigger`, prompt mirrored to `routine-prompt.txt`).

## 5. Data model (Supabase)

- **`sponsorship_rows`** — one row per ingested video record, per month.
  Columns: `id`, `month` (e.g. `2026-06`), `video_title`, `video_url`, `channel`,
  `sponsor_raw`, `publish_date`, `length_seconds` (nullable), `is_long_form` (bool),
  `ingested_at`. Source-of-truth raw layer; kept for every month (baseline forward).
- **`brand_monthly_counts`** — aggregated `(month, brand_canonical, brand_display,
  sponsorship_count)`. The history table that powers month-over-month and baseline comparison.
- **`brand_aliases`** — `(alias_normalized, brand_canonical, brand_display)`. Editable map that
  collapses name variants into one canonical brand. Seeded over time; unmatched high-volume names
  get surfaced in the report for you to add.
- HubSpot data is **not** stored — queried live via MCP (when available).

Ingest of a month is **idempotent**: re-running a month replaces that month's `sponsorship_rows`
and re-aggregates, so a re-run never double-counts.

## 6. Config (`config.json` — broad and tunable)

- `column_map` — maps our canonical fields (video, channel, sponsor, date, length/longform) to
  Cohen's actual header names. Lets us adapt to the real sheet without code changes.
- `long_form`: either a direct column (`is_long_form` flag — likely, per owner) **or** a
  `length_threshold_seconds` fallback (default 600s) if only a length column exists.
- `multi_sponsor`: handling for multiple sponsors in one cell — `delimiter` (e.g. `;` or `,`) or
  `none` if rows are already one sponsor each.
- `top_n` — brands to surface (default 25).
- `final_recipient` — email (deferred; owner-only until set).
- `slack_channel` — channel id/name (deferred; no-op until set).
- `dedupe_key` — default `(video_url, brand_canonical)`.

## 7. Monthly run sequence

1. **Ingest** — load the uploaded CSV into `sponsorship_rows` for `month`, applying `column_map`.
   Idempotent: clear any existing rows for that month first.
2. **Normalize + filter** — keep long-form only; split multi-sponsor cells per config; map each
   `sponsor_raw` → `brand_canonical` via `brand_aliases`; dedupe by `dedupe_key`.
3. **Aggregate** — write `(month, brand_canonical, count)` into `brand_monthly_counts`.
4. **Rank + diff** — Top-N by count this month; for each, compute delta vs **prior month**
   (▲ more / ▬ same / ▼ less, with % change); list **new** brands (absent last month) and
   **dropped** brands (present last month, gone this month). First month = baseline (no diffs;
   labeled as such).
5. **Relationship cross-ref** — for the Top-N (and notable new brands), call the HubSpot step:
   match on normalized brand name/domain → `has_relationship`, `stage`, `owner`. Stubbed until the
   connector exists (returns no-match, or matches an optional local `known_brands.json`).
6. **Render** — LLM writes a short narrative (what moved, notable new spenders, priority
   relationships) and assembles the branded HTML: ranked table with count, MoM arrow/%, and a
   relationship badge; sections for "new this month," "dropped off," and "priority follow-ups."
7. **Deliver** — auto-send the HTML email to `final_recipient` via the Supabase send pattern, and
   post a Slack summary (top movers + a link/snippet) to `slack_channel`. **First run is
   owner-only** (email to you, Slack no-op) until you validate, then flip the config.

## 8. Brand normalization (the #1 accuracy lever)

Counts fragment if "BetterHelp," "Better Help," and "betterhelp.com" are treated as three brands.
Strategy: normalize aggressively for matching (lowercase, strip punctuation/spacing/domain
suffixes), resolve via `brand_aliases`, and **surface the top unmatched/unnormalized names in the
report** so the alias map improves every month. Canonical display name is kept separate from the
match key.

## 9. Edge cases handled

- **First month:** baseline — store everything, render without diffs, label clearly.
- **Re-running a month:** idempotent replace (no double counting).
- **Multi-sponsor cells / duplicate rows:** split + dedupe per config.
- **Missing length / long-form column:** fall back to the configured threshold; if neither exists,
  flag and process all rows with a warning in the report.
- **HubSpot/Slack not connected:** steps stub cleanly; report still ships by email.
- **Brand-name drift:** unmatched high-volume names flagged for alias curation.

## 10. Repo layout (to build)

```
automations/02-youtube-sponsorship-intelligence/
  spec.md                  # pointer to this design + as-built notes
  routine.md               # deployment + behavior (canonical, like the film-slate one)
  routine-prompt.txt       # verbatim production prompt
  config.json              # section 6
  brand_aliases.seed.json  # initial alias seeds
  known_brands.json        # optional local relationship list (HubSpot stub fallback)
  sample/                  # synthetic sample CSV(s) to build + test without the real sheet
  sql/                     # table DDL + the processing queries
  email-template.html      # branded report template (adapted from film-slate)
```

## 11. Deferred inputs to collect at go-live

- The real sheet (exact headers → finalize `column_map`; confirm the long/short-form column).
- HubSpot connector + the matching fields available (name? domain? company object?).
- Slack connector + target channel.
- Final recipient email.

Until these arrive, v1 is built and validated against the synthetic sample, delivering owner-only.

## 12. Testing

Build and validate the full pipeline against a **synthetic sample CSV** (a few hundred rows across
two simulated months) so counting, MoM diffs, baseline behavior, normalization, and the rendered
report are all verified before the real data or connectors exist.
