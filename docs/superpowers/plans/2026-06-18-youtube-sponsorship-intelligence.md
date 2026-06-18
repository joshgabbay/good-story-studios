# YouTube Sponsorship Intelligence Digest — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dependency-light Python pipeline that turns a monthly CSV of sponsored YouTube videos into a ranked brand-intelligence report (counts, month-over-month diffs vs a stored baseline, and relationship flags), runnable end-to-end today against a synthetic sample, with live ingest / HubSpot / Slack / email as pluggable stubs.

**Architecture:** Approach A from the design spec. Deterministic engine — Python (`csv`) shapes rows, `sqlite3` stores per-month history and aggregates, Python computes rankings/diffs. The LLM (production only) writes prose; it never counts. SQLite is the local stand-in for Supabase Postgres; the SQL is kept portable (CREATE/INSERT/DELETE/GROUP BY only). HubSpot, Slack, email, and live ingest are isolated behind small interfaces with v1 stubs.

**Tech Stack:** Python 3 stdlib (`csv`, `sqlite3`, `json`, `argparse`), `pytest` for tests. No third-party runtime deps (keeps it portable into the CCR routine environment).

**Spec:** `docs/superpowers/specs/2026-06-18-youtube-sponsorship-intelligence-design.md`

---

## File structure (created by this plan)

```
automations/02-youtube-sponsorship-intelligence/
  pipeline/
    __init__.py
    transform.py        # CSV → canonical brand-resolved rows (parse, split, normalize, filter); + top_unmatched_brands
    engine.py           # sqlite history store + load_month (idempotent) + rank_and_diff
    relationships.py    # relationship lookup (v1 stub over known_brands.json; HubSpot later)
    report.py           # render_html + render_slack from the structured report
    run.py              # CLI orchestrator wiring it all together
  tests/
    test_transform.py
    test_engine.py
    test_relationships.py
    test_report.py
    test_run.py
  conftest.py           # puts the package dir on sys.path for tests
  requirements-dev.txt  # pytest
  config.json           # column map, long-form rule, multi-sponsor rule, top_n, recipient, channel
  brand_aliases.seed.json
  known_brands.json     # v1 relationship stub data
  email-template.html   # branded report template
  sample/
    2026-05_sample.csv  # baseline month
    2026-06_sample.csv  # second month (exercises up/down/new/dropped)
  spec.md               # pointer to the design spec + as-built notes
  routine.md            # production deployment doc (deferred wiring documented)
  routine-prompt.txt    # production routine prompt DRAFT (deferred wiring marked)
```

### Canonical data contracts (used consistently across all tasks)

Canonical row from `transform.load_csv` (one per CSV line, sponsor still raw/combined):
`{video_title, video_url, channel, sponsor, publish_date, length_seconds (int|None), long_form_flag (str|None)}`

Canonical row from `transform.normalize_rows` (one per video×resolved-brand; long- AND short-form kept, deduped):
`{month, video_title, video_url, channel, brand_canonical, brand_display, publish_date, length_seconds, is_long_form (bool), is_aliased (bool)}`
(`is_aliased` = the raw sponsor's normalized key was found in the alias map; `False` means it was resolved by fallback and is an alias candidate.)

`transform.top_unmatched_brands(rows, limit)` returns top fallback (`is_aliased=False`) long-form brands by count:
`[{"brand_display": "SomeBrand", "count": 12}, ...]`. `run.py` attaches this to the report dict as `report["unmatched"]` for rendering.

`engine.rank_and_diff(...)` returns:
```python
{
  "month": "2026-06",
  "prior_month": "2026-05",   # or None
  "is_baseline": False,        # True when prior_month is None
  "ranked": [
    {"rank": 1, "brand_canonical": "betterhelp", "brand_display": "BetterHelp",
     "count": 3, "prior_count": 2, "delta": 1, "pct_change": 50.0, "direction": "up"},
    # direction in {"up","down","same","new"}; pct_change is None when prior_count == 0
  ],
  "new_brands": [{"brand_display": "HelloFresh", "count": 2}],
  "dropped_brands": [{"brand_display": "Squarespace", "prior_count": 2}],
}
```

`relationships.lookup_relationships(...)` returns:
`{brand_canonical: {"has_relationship": bool, "stage": str|None}}`

---

## Task 1: Scaffold the package

**Files:**
- Create: `automations/02-youtube-sponsorship-intelligence/pipeline/__init__.py`
- Create: `automations/02-youtube-sponsorship-intelligence/conftest.py`
- Create: `automations/02-youtube-sponsorship-intelligence/requirements-dev.txt`
- Test: `automations/02-youtube-sponsorship-intelligence/tests/test_transform.py` (smoke import)

- [ ] **Step 1: Create the package marker**

`pipeline/__init__.py`:
```python
```
(empty file)

- [ ] **Step 2: Create conftest so tests can import the package**

`conftest.py`:
```python
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
```

- [ ] **Step 3: Create dev requirements**

`requirements-dev.txt`:
```
pytest
```

- [ ] **Step 4: Write a smoke test**

`tests/test_transform.py`:
```python
def test_package_imports():
    import pipeline  # noqa: F401
```

- [ ] **Step 5: Set up the environment and run the smoke test**

Run (from repo root):
```bash
cd automations/02-youtube-sponsorship-intelligence && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt && .venv/bin/python -m pytest tests/ -q
```
Expected: PASS (1 test). If `python3 -m venv` is unavailable, fall back to `pip install --user pytest` and `python3 -m pytest tests/ -q`.

- [ ] **Step 6: Add a venv ignore and commit**

Append to repo root `.gitignore` (create if missing) the line `automations/02-youtube-sponsorship-intelligence/.venv/`.
```bash
git add automations/02-youtube-sponsorship-intelligence/ .gitignore
git commit -m "scaffold: youtube sponsorship intelligence pipeline package"
```

---

## Task 2: Fixtures — config, seeds, sample data, template

**Files:**
- Create: `automations/02-youtube-sponsorship-intelligence/config.json`
- Create: `automations/02-youtube-sponsorship-intelligence/brand_aliases.seed.json`
- Create: `automations/02-youtube-sponsorship-intelligence/known_brands.json`
- Create: `automations/02-youtube-sponsorship-intelligence/sample/2026-05_sample.csv`
- Create: `automations/02-youtube-sponsorship-intelligence/sample/2026-06_sample.csv`
- Create: `automations/02-youtube-sponsorship-intelligence/email-template.html`

These are fixtures (no test of their own; later tasks assert against them).

- [ ] **Step 1: Create `config.json`**
```json
{
  "column_map": {
    "video_title": "Video Title",
    "video_url": "Video URL",
    "channel": "Channel",
    "sponsor": "Sponsor",
    "publish_date": "Publish Date",
    "length_seconds": "Length (s)",
    "long_form_flag": null
  },
  "long_form": { "mode": "threshold", "length_threshold_seconds": 600 },
  "multi_sponsor": { "delimiter": ";" },
  "top_n": 25,
  "final_recipient": null,
  "slack_channel": null
}
```
(Dedupe is fixed at `(video_url, brand_canonical)` in `normalize_rows` — not a tunable, so it is not in config.)

- [ ] **Step 2: Create `brand_aliases.seed.json`**
```json
{
  "better help": { "canonical": "betterhelp", "display": "BetterHelp" },
  "betterhelp com": { "canonical": "betterhelp", "display": "BetterHelp" }
}
```

- [ ] **Step 3: Create `known_brands.json`** (relationship stub, keyed by canonical)
```json
{
  "betterhelp": { "stage": "In conversation" },
  "nordvpn": { "stage": "Closed - delivered" }
}
```

- [ ] **Step 4: Create `sample/2026-05_sample.csv`** (baseline month)
```csv
Video Title,Video URL,Channel,Sponsor,Publish Date,Length (s)
Vid A,https://yt/a,ChanX,BetterHelp,2026-05-03,720
Vid B,https://yt/b,ChanY,Squarespace; NordVPN,2026-05-10,900
Vid C,https://yt/c,ChanZ,Better Help,2026-05-15,650
Vid D,https://yt/d,ChanX,ShortBrand,2026-05-20,120
Vid E,https://yt/e,ChanY,NordVPN,2026-05-22,800
Vid F,https://yt/f,ChanZ,Squarespace,2026-05-25,610
```
(May long-form brand counts: BetterHelp 2, Squarespace 2, NordVPN 2; ShortBrand filtered out.)

- [ ] **Step 5: Create `sample/2026-06_sample.csv`** (second month)
```csv
Video Title,Video URL,Channel,Sponsor,Publish Date,Length (s)
Vid G,https://yt/g,ChanX,BetterHelp,2026-06-02,700
Vid H,https://yt/h,ChanY,BetterHelp,2026-06-09,640
Vid I,https://yt/i,ChanZ,betterhelp.com,2026-06-12,700
Vid J,https://yt/j,ChanX,NordVPN,2026-06-14,900
Vid K,https://yt/k,ChanY,HelloFresh,2026-06-18,800
Vid L,https://yt/l,ChanZ,HelloFresh,2026-06-20,700
```
(June long-form counts: BetterHelp 3, HelloFresh 2, NordVPN 1; Squarespace absent → dropped.)

- [ ] **Step 6: Create `email-template.html`** (placeholders filled by `report.render_html`)
```html
<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<style>body{font-family:Arial,sans-serif;color:#2D2D2D;background:#F7F8FC;margin:0;padding:24px;}
.card{max-width:760px;margin:0 auto;background:#fff;border-radius:16px;padding:32px;}
h1{color:#6B90D9;margin:0 0 4px;} .sub{color:#9AA7C2;font-weight:700;margin:0 0 20px;}
table{width:100%;border-collapse:collapse;font-size:14px;} th,td{text-align:left;padding:8px 10px;border-bottom:1px solid #EDF2FB;}
th{color:#6B90D9;text-transform:uppercase;font-size:12px;letter-spacing:.5px;}
.rel{background:#EAF7EE;color:#2E7D43;border-radius:10px;padding:2px 8px;font-size:12px;font-weight:700;}
.section{margin-top:24px;} .narr{color:#5A78BB;line-height:1.6;}</style></head>
<body><div class="card">
<h1>Sponsorship Intelligence</h1>
<p class="sub">{{MONTH_LABEL}}</p>
<p class="narr">{{NARRATIVE}}</p>
<div class="section"><table>
<tr><th>#</th><th>Brand</th><th>Sponsorships</th><th>MoM</th><th>Relationship</th></tr>
{{ROWS}}
</table></div>
<div class="section"><strong>New this month:</strong> {{NEW_BRANDS}}</div>
<div class="section"><strong>Dropped off:</strong> {{DROPPED_BRANDS}}</div>
<div class="section"><strong>Top unmatched brands (review for aliasing):</strong> {{UNMATCHED}}</div>
<p class="sub" style="margin-top:28px;">Generated {{GENERATED_DATE}} · Good Story Studios</p>
</div></body></html>
```

- [ ] **Step 7: Commit**
```bash
git add automations/02-youtube-sponsorship-intelligence/
git commit -m "fixtures: config, aliases, known brands, sample CSVs, email template"
```

---

## Task 3: `transform.normalize_key`

**Files:**
- Create: `automations/02-youtube-sponsorship-intelligence/pipeline/transform.py`
- Test: `automations/02-youtube-sponsorship-intelligence/tests/test_transform.py`

- [ ] **Step 1: Write failing tests** (append to `tests/test_transform.py`)
```python
from pipeline import transform


def test_normalize_key_lowercases_and_trims():
    assert transform.normalize_key("  BetterHelp ") == "betterhelp"


def test_normalize_key_collapses_punctuation_and_spaces():
    assert transform.normalize_key("Better  Help!!") == "better help"


def test_normalize_key_strips_domain_punctuation():
    assert transform.normalize_key("betterhelp.com") == "betterhelp com"


def test_normalize_key_empty():
    assert transform.normalize_key("") == ""
    assert transform.normalize_key(None) == ""
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `.venv/bin/python -m pytest tests/test_transform.py -q`
Expected: FAIL (`AttributeError: module 'pipeline.transform' has no attribute 'normalize_key'`).

- [ ] **Step 3: Implement** (`pipeline/transform.py`)
```python
import re


def normalize_key(raw):
    """Lowercase, strip, replace non-alphanumeric runs with single spaces."""
    if not raw:
        return ""
    s = str(raw).lower().strip()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return s.strip()
```

- [ ] **Step 4: Run tests, verify pass**

Run: `.venv/bin/python -m pytest tests/test_transform.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add automations/02-youtube-sponsorship-intelligence/pipeline/transform.py automations/02-youtube-sponsorship-intelligence/tests/test_transform.py
git commit -m "feat: transform.normalize_key"
```

---

## Task 4: `transform.split_sponsors` and `transform.is_long_form`

**Files:**
- Modify: `pipeline/transform.py`
- Test: `tests/test_transform.py`

- [ ] **Step 1: Write failing tests** (append)
```python
def test_split_sponsors_single():
    assert transform.split_sponsors("BetterHelp", ";") == ["BetterHelp"]


def test_split_sponsors_multi_and_trims():
    assert transform.split_sponsors("Squarespace; NordVPN ", ";") == ["Squarespace", "NordVPN"]


def test_split_sponsors_drops_empties():
    assert transform.split_sponsors("A;; ;B", ";") == ["A", "B"]


def test_is_long_form_threshold():
    cfg = {"mode": "threshold", "length_threshold_seconds": 600}
    assert transform.is_long_form(720, None, cfg) is True
    assert transform.is_long_form(120, None, cfg) is False


def test_is_long_form_flag_mode():
    cfg = {"mode": "flag"}
    assert transform.is_long_form(None, "long", cfg) is True
    assert transform.is_long_form(None, "short", cfg) is False


def test_is_long_form_unknown_defaults_true():
    cfg = {"mode": "threshold", "length_threshold_seconds": 600}
    assert transform.is_long_form(None, None, cfg) is True
```

- [ ] **Step 2: Run, verify fail**

Run: `.venv/bin/python -m pytest tests/test_transform.py -q`
Expected: FAIL (missing `split_sponsors` / `is_long_form`).

- [ ] **Step 3: Implement** (append to `pipeline/transform.py`)
```python
def split_sponsors(raw, delimiter):
    if not raw:
        return []
    parts = str(raw).split(delimiter)
    return [p.strip() for p in parts if p and p.strip()]


_TRUE_FLAGS = {"long", "longform", "long form", "true", "yes", "1"}


def is_long_form(length_seconds, flag_value, long_form_cfg):
    mode = long_form_cfg.get("mode", "threshold")
    if mode == "flag":
        if flag_value is None:
            return True
        return normalize_key(flag_value) in _TRUE_FLAGS
    if length_seconds is None:
        return True
    threshold = long_form_cfg.get("length_threshold_seconds", 600)
    return int(length_seconds) >= int(threshold)
```

- [ ] **Step 4: Run, verify pass**

Run: `.venv/bin/python -m pytest tests/test_transform.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add automations/02-youtube-sponsorship-intelligence/pipeline/transform.py automations/02-youtube-sponsorship-intelligence/tests/test_transform.py
git commit -m "feat: transform.split_sponsors and is_long_form"
```

---

## Task 5: `transform.load_csv` and `transform.resolve_brand`

**Files:**
- Modify: `pipeline/transform.py`
- Test: `tests/test_transform.py`

- [ ] **Step 1: Write failing tests** (append)
```python
import os

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample")

COLUMN_MAP = {
    "video_title": "Video Title",
    "video_url": "Video URL",
    "channel": "Channel",
    "sponsor": "Sponsor",
    "publish_date": "Publish Date",
    "length_seconds": "Length (s)",
    "long_form_flag": None,
}


def test_load_csv_maps_columns_and_parses_length():
    rows = transform.load_csv(os.path.join(SAMPLE_DIR, "2026-05_sample.csv"), COLUMN_MAP)
    assert len(rows) == 6
    assert rows[0]["video_title"] == "Vid A"
    assert rows[0]["channel"] == "ChanX"
    assert rows[0]["sponsor"] == "BetterHelp"
    assert rows[0]["length_seconds"] == 720
    assert rows[0]["long_form_flag"] is None


def test_resolve_brand_uses_alias():
    aliases = {"better help": {"canonical": "betterhelp", "display": "BetterHelp"}}
    assert transform.resolve_brand("Better Help", aliases) == ("betterhelp", "BetterHelp")


def test_resolve_brand_without_alias_uses_normalized_key_and_raw_display():
    assert transform.resolve_brand("HelloFresh", {}) == ("hellofresh", "HelloFresh")
```

- [ ] **Step 2: Run, verify fail**

Run: `.venv/bin/python -m pytest tests/test_transform.py -q`
Expected: FAIL (missing `load_csv` / `resolve_brand`).

- [ ] **Step 3: Implement** (append to `pipeline/transform.py`; add `import csv` at top of file)
```python
import csv  # add near the top with the other imports


def _to_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def load_csv(path, column_map):
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for raw in reader:
            row = {}
            for field, source_col in column_map.items():
                if source_col is None or source_col not in raw:
                    row[field] = None
                else:
                    row[field] = raw[source_col]
            row["length_seconds"] = _to_int(row.get("length_seconds"))
            rows.append(row)
    return rows


def resolve_brand(raw_sponsor, aliases):
    key = normalize_key(raw_sponsor)
    if key in aliases:
        a = aliases[key]
        return a["canonical"], a["display"]
    return key, str(raw_sponsor).strip()
```

- [ ] **Step 4: Run, verify pass**

Run: `.venv/bin/python -m pytest tests/test_transform.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add automations/02-youtube-sponsorship-intelligence/pipeline/transform.py automations/02-youtube-sponsorship-intelligence/tests/test_transform.py
git commit -m "feat: transform.load_csv and resolve_brand"
```

---

## Task 6: `transform.normalize_rows` (full row shaping)

**Files:**
- Modify: `pipeline/transform.py`
- Test: `tests/test_transform.py`

- [ ] **Step 1: Write failing test** (append)
```python
import json

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")
ALIASES_PATH = os.path.join(os.path.dirname(__file__), "..", "brand_aliases.seed.json")


def _load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def test_normalize_rows_splits_filters_and_resolves():
    config = _load_json(CONFIG_PATH)
    aliases = _load_json(ALIASES_PATH)
    raw = transform.load_csv(os.path.join(SAMPLE_DIR, "2026-05_sample.csv"), config["column_map"])
    out = transform.normalize_rows(raw, "2026-05", config, aliases)

    # Multi-sponsor Vid B becomes two rows; short-form Vid D (120s) is kept but flagged short.
    canon_counts = {}
    for r in out:
        if r["is_long_form"]:
            canon_counts[r["brand_canonical"]] = canon_counts.get(r["brand_canonical"], 0) + 1
    assert canon_counts.get("betterhelp") == 2   # Vid A + Vid C (alias)
    assert canon_counts.get("squarespace") == 2  # Vid B + Vid F
    assert canon_counts.get("nordvpn") == 2      # Vid B + Vid E
    assert "shortbrand" not in canon_counts      # Vid D is short-form

    # Every output row carries the month and a display name.
    assert all(r["month"] == "2026-05" for r in out)
    assert all(r["brand_display"] for r in out)


def test_normalize_rows_dedupes_same_video_same_brand():
    config = _load_json(CONFIG_PATH)
    rows = [
        {"video_title": "X", "video_url": "https://yt/x", "channel": "C",
         "sponsor": "BetterHelp; BetterHelp", "publish_date": "2026-05-01",
         "length_seconds": 700, "long_form_flag": None},
    ]
    out = transform.normalize_rows(rows, "2026-05", config, {})
    assert len(out) == 1


def test_normalize_rows_marks_alias_vs_fallback():
    config = _load_json(CONFIG_PATH)
    aliases = _load_json(ALIASES_PATH)
    rows = [
        {"video_title": "A", "video_url": "https://yt/a", "channel": "C", "sponsor": "Better Help",
         "publish_date": "2026-05-01", "length_seconds": 700, "long_form_flag": None},
        {"video_title": "B", "video_url": "https://yt/b", "channel": "C", "sponsor": "HelloFresh",
         "publish_date": "2026-05-02", "length_seconds": 700, "long_form_flag": None},
    ]
    out = transform.normalize_rows(rows, "2026-05", config, aliases)
    by_canon = {r["brand_canonical"]: r for r in out}
    assert by_canon["betterhelp"]["is_aliased"] is True       # matched alias
    assert by_canon["hellofresh"]["is_aliased"] is False      # fallback → alias candidate


def test_top_unmatched_brands_ranks_fallback_only():
    rows = [
        {"brand_canonical": "hellofresh", "brand_display": "HelloFresh", "is_long_form": True, "is_aliased": False},
        {"brand_canonical": "hellofresh", "brand_display": "HelloFresh", "is_long_form": True, "is_aliased": False},
        {"brand_canonical": "betterhelp", "brand_display": "BetterHelp", "is_long_form": True, "is_aliased": True},
        {"brand_canonical": "shorty", "brand_display": "Shorty", "is_long_form": False, "is_aliased": False},
    ]
    out = transform.top_unmatched_brands(rows, limit=10)
    assert out == [{"brand_display": "HelloFresh", "count": 2}]  # aliased + short-form excluded
```

- [ ] **Step 2: Run, verify fail**

Run: `.venv/bin/python -m pytest tests/test_transform.py -q`
Expected: FAIL (missing `normalize_rows`).

- [ ] **Step 3: Implement** (append to `pipeline/transform.py`)
```python
def normalize_rows(raw_rows, month, config, aliases):
    delimiter = config["multi_sponsor"]["delimiter"]
    long_form_cfg = config["long_form"]
    out = []
    seen = set()
    for r in raw_rows:
        long_form = is_long_form(r.get("length_seconds"), r.get("long_form_flag"), long_form_cfg)
        for sponsor in split_sponsors(r.get("sponsor"), delimiter):
            canonical, display = resolve_brand(sponsor, aliases)
            if not canonical:
                continue
            dedupe = (r.get("video_url"), canonical)
            if dedupe in seen:
                continue
            seen.add(dedupe)
            out.append({
                "month": month,
                "video_title": r.get("video_title"),
                "video_url": r.get("video_url"),
                "channel": r.get("channel"),
                "brand_canonical": canonical,
                "brand_display": display,
                "publish_date": r.get("publish_date"),
                "length_seconds": r.get("length_seconds"),
                "is_long_form": long_form,
                "is_aliased": normalize_key(sponsor) in aliases,
            })
    return out


def top_unmatched_brands(rows, limit=10):
    """Top long-form brands resolved by fallback (not in the alias map) — alias candidates."""
    counts, displays = {}, {}
    for r in rows:
        if r["is_long_form"] and not r.get("is_aliased", True):
            canon = r["brand_canonical"]
            counts[canon] = counts.get(canon, 0) + 1
            displays.setdefault(canon, r["brand_display"])
    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]
    return [{"brand_display": displays[c], "count": n} for c, n in ordered]
```

- [ ] **Step 4: Run, verify pass**

Run: `.venv/bin/python -m pytest tests/test_transform.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add automations/02-youtube-sponsorship-intelligence/pipeline/transform.py automations/02-youtube-sponsorship-intelligence/tests/test_transform.py
git commit -m "feat: transform.normalize_rows"
```

---

## Task 7: `engine` — schema + idempotent `load_month`

**Files:**
- Create: `pipeline/engine.py`
- Test: `tests/test_engine.py`

- [ ] **Step 1: Write failing tests** (`tests/test_engine.py`)
```python
from pipeline import engine


def _row(month, url, canon, display, long_form=True):
    return {
        "month": month, "video_title": "t", "video_url": url, "channel": "c",
        "brand_canonical": canon, "brand_display": display, "publish_date": "2026-05-01",
        "length_seconds": 700, "is_long_form": long_form,
    }


def test_load_month_aggregates_long_form_only():
    conn = engine.connect(":memory:")
    engine.init_schema(conn)
    rows = [
        _row("2026-05", "https://yt/a", "betterhelp", "BetterHelp"),
        _row("2026-05", "https://yt/c", "betterhelp", "BetterHelp"),
        _row("2026-05", "https://yt/d", "shortbrand", "ShortBrand", long_form=False),
    ]
    engine.load_month(conn, "2026-05", rows)
    counts = dict(conn.execute(
        "SELECT brand_canonical, sponsorship_count FROM brand_monthly_counts WHERE month='2026-05'"
    ).fetchall())
    assert counts == {"betterhelp": 2}  # short-form excluded from counts


def test_load_month_is_idempotent():
    conn = engine.connect(":memory:")
    engine.init_schema(conn)
    rows = [_row("2026-05", "https://yt/a", "betterhelp", "BetterHelp")]
    engine.load_month(conn, "2026-05", rows)
    engine.load_month(conn, "2026-05", rows)  # re-run same month
    total = conn.execute(
        "SELECT sponsorship_count FROM brand_monthly_counts WHERE month='2026-05' AND brand_canonical='betterhelp'"
    ).fetchone()[0]
    assert total == 1  # not doubled
```

- [ ] **Step 2: Run, verify fail**

Run: `.venv/bin/python -m pytest tests/test_engine.py -q`
Expected: FAIL (no module `pipeline.engine`).

- [ ] **Step 3: Implement** (`pipeline/engine.py`)
```python
import sqlite3


def connect(db_path=":memory:"):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS sponsorship_rows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT NOT NULL,
            video_title TEXT, video_url TEXT, channel TEXT,
            brand_canonical TEXT NOT NULL, brand_display TEXT,
            publish_date TEXT, length_seconds INTEGER, is_long_form INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS brand_monthly_counts (
            month TEXT NOT NULL,
            brand_canonical TEXT NOT NULL,
            brand_display TEXT,
            sponsorship_count INTEGER NOT NULL,
            PRIMARY KEY (month, brand_canonical)
        );
        """
    )
    conn.commit()


def load_month(conn, month, rows):
    """Idempotent: replace this month's raw rows and re-aggregate long-form counts."""
    conn.execute("DELETE FROM sponsorship_rows WHERE month = ?", (month,))
    conn.execute("DELETE FROM brand_monthly_counts WHERE month = ?", (month,))
    conn.executemany(
        """INSERT INTO sponsorship_rows
           (month, video_title, video_url, channel, brand_canonical, brand_display,
            publish_date, length_seconds, is_long_form)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        [(r["month"], r["video_title"], r["video_url"], r["channel"], r["brand_canonical"],
          r["brand_display"], r["publish_date"], r["length_seconds"], 1 if r["is_long_form"] else 0)
         for r in rows],
    )
    conn.execute(
        """INSERT INTO brand_monthly_counts (month, brand_canonical, brand_display, sponsorship_count)
           SELECT month, brand_canonical, MIN(brand_display), COUNT(*)
           FROM sponsorship_rows
           WHERE month = ? AND is_long_form = 1
           GROUP BY month, brand_canonical""",
        (month,),
    )
    conn.commit()
```

- [ ] **Step 4: Run, verify pass**

Run: `.venv/bin/python -m pytest tests/test_engine.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add automations/02-youtube-sponsorship-intelligence/pipeline/engine.py automations/02-youtube-sponsorship-intelligence/tests/test_engine.py
git commit -m "feat: engine schema and idempotent load_month"
```

---

## Task 8: `engine.rank_and_diff` (baseline + MoM + new/dropped)

**Files:**
- Modify: `pipeline/engine.py`
- Test: `tests/test_engine.py`

- [ ] **Step 1: Write failing tests** (append to `tests/test_engine.py`)
```python
def _seed_two_months(conn):
    engine.init_schema(conn)
    may = [
        _row("2026-05", "https://yt/a", "betterhelp", "BetterHelp"),
        _row("2026-05", "https://yt/c", "betterhelp", "BetterHelp"),
        _row("2026-05", "https://yt/e", "nordvpn", "NordVPN"),
        _row("2026-05", "https://yt/b", "nordvpn", "NordVPN"),
        _row("2026-05", "https://yt/f", "squarespace", "Squarespace"),
        _row("2026-05", "https://yt/b2", "squarespace", "Squarespace"),
    ]
    june = [
        _row("2026-06", "https://yt/g", "betterhelp", "BetterHelp"),
        _row("2026-06", "https://yt/h", "betterhelp", "BetterHelp"),
        _row("2026-06", "https://yt/i", "betterhelp", "BetterHelp"),
        _row("2026-06", "https://yt/j", "nordvpn", "NordVPN"),
        _row("2026-06", "https://yt/k", "hellofresh", "HelloFresh"),
        _row("2026-06", "https://yt/l", "hellofresh", "HelloFresh"),
    ]
    engine.load_month(conn, "2026-05", may)
    engine.load_month(conn, "2026-06", june)


def test_rank_and_diff_baseline_first_month():
    conn = engine.connect(":memory:")
    engine.init_schema(conn)
    engine.load_month(conn, "2026-05", [_row("2026-05", "https://yt/a", "betterhelp", "BetterHelp")])
    out = engine.rank_and_diff(conn, "2026-05", top_n=25)
    assert out["is_baseline"] is True
    assert out["prior_month"] is None
    assert out["ranked"][0]["direction"] == "new"
    assert out["dropped_brands"] == []


def test_rank_and_diff_month_over_month():
    conn = engine.connect(":memory:")
    _seed_two_months(conn)
    out = engine.rank_and_diff(conn, "2026-06", top_n=25)
    assert out["is_baseline"] is False
    assert out["prior_month"] == "2026-05"

    by_canon = {r["brand_canonical"]: r for r in out["ranked"]}
    assert by_canon["betterhelp"]["count"] == 3
    assert by_canon["betterhelp"]["prior_count"] == 2
    assert by_canon["betterhelp"]["direction"] == "up"
    assert by_canon["betterhelp"]["pct_change"] == 50.0
    assert by_canon["nordvpn"]["direction"] == "down"
    assert by_canon["hellofresh"]["direction"] == "new"
    assert by_canon["hellofresh"]["pct_change"] is None

    new_displays = [b["brand_display"] for b in out["new_brands"]]
    dropped_displays = [b["brand_display"] for b in out["dropped_brands"]]
    assert "HelloFresh" in new_displays
    assert "Squarespace" in dropped_displays


def test_rank_and_diff_respects_top_n():
    conn = engine.connect(":memory:")
    _seed_two_months(conn)
    out = engine.rank_and_diff(conn, "2026-06", top_n=1)
    assert len(out["ranked"]) == 1
    assert out["ranked"][0]["brand_canonical"] == "betterhelp"
```

- [ ] **Step 2: Run, verify fail**

Run: `.venv/bin/python -m pytest tests/test_engine.py -q`
Expected: FAIL (missing `rank_and_diff`).

- [ ] **Step 3: Implement** (append to `pipeline/engine.py`)
```python
def _counts_for_month(conn, month):
    rows = conn.execute(
        "SELECT brand_canonical, brand_display, sponsorship_count FROM brand_monthly_counts WHERE month = ?",
        (month,),
    ).fetchall()
    return {canon: {"display": display, "count": count} for canon, display, count in rows}


def _prior_month(conn, month):
    row = conn.execute(
        "SELECT MAX(month) FROM brand_monthly_counts WHERE month < ?", (month,)
    ).fetchone()
    return row[0] if row and row[0] else None


def rank_and_diff(conn, month, top_n):
    current = _counts_for_month(conn, month)
    prior_month = _prior_month(conn, month)
    prior = _counts_for_month(conn, prior_month) if prior_month else {}
    is_baseline = prior_month is None

    ordered = sorted(current.items(), key=lambda kv: (-kv[1]["count"], kv[0]))
    ranked = []
    for i, (canon, cur) in enumerate(ordered[:top_n], start=1):
        prior_count = prior.get(canon, {}).get("count", 0)
        delta = cur["count"] - prior_count
        if prior_count == 0:
            direction, pct = "new", None
        elif delta > 0:
            direction, pct = "up", round(delta / prior_count * 100, 1)
        elif delta < 0:
            direction, pct = "down", round(delta / prior_count * 100, 1)
        else:
            direction, pct = "same", 0.0
        ranked.append({
            "rank": i, "brand_canonical": canon, "brand_display": cur["display"],
            "count": cur["count"], "prior_count": prior_count, "delta": delta,
            "pct_change": pct, "direction": direction,
        })

    # `ordered` is sorted by count desc; cap to top_n so a 25k-row month doesn't emit
    # hundreds of tiny new brands. Baseline has nothing to compare against.
    new_brands = (
        [{"brand_display": cur["display"], "count": cur["count"]}
         for canon, cur in ordered if canon not in prior][:top_n]
        if not is_baseline else []
    )

    dropped = [
        {"brand_display": p["display"], "prior_count": p["count"]}
        for canon, p in sorted(prior.items(), key=lambda kv: -kv[1]["count"])
        if canon not in current
    ][:top_n]

    return {
        "month": month, "prior_month": prior_month, "is_baseline": is_baseline,
        "ranked": ranked, "new_brands": new_brands, "dropped_brands": dropped,
    }
```

- [ ] **Step 4: Run, verify pass**

Run: `.venv/bin/python -m pytest tests/test_engine.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add automations/02-youtube-sponsorship-intelligence/pipeline/engine.py automations/02-youtube-sponsorship-intelligence/tests/test_engine.py
git commit -m "feat: engine.rank_and_diff with baseline, MoM, new/dropped"
```

---

## Task 9: `relationships` — v1 stub over `known_brands.json`

**Files:**
- Create: `pipeline/relationships.py`
- Test: `tests/test_relationships.py`

- [ ] **Step 1: Write failing tests** (`tests/test_relationships.py`)
```python
from pipeline import relationships


def test_lookup_flags_known_brands():
    known = {"betterhelp": {"stage": "In conversation"}}
    out = relationships.lookup_relationships(["betterhelp", "hellofresh"], known)
    assert out["betterhelp"] == {"has_relationship": True, "stage": "In conversation"}
    assert out["hellofresh"] == {"has_relationship": False, "stage": None}


def test_load_known_brands_reads_file():
    import os
    path = os.path.join(os.path.dirname(__file__), "..", "known_brands.json")
    known = relationships.load_known_brands(path)
    assert "betterhelp" in known
```

- [ ] **Step 2: Run, verify fail**

Run: `.venv/bin/python -m pytest tests/test_relationships.py -q`
Expected: FAIL (no module).

- [ ] **Step 3: Implement** (`pipeline/relationships.py`)
```python
import json


def load_known_brands(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def lookup_relationships(brand_canonicals, known):
    """v1 stub. Replace internals with a HubSpot MCP query later; signature stays the same."""
    out = {}
    for canon in brand_canonicals:
        entry = known.get(canon)
        if entry:
            out[canon] = {"has_relationship": True, "stage": entry.get("stage")}
        else:
            out[canon] = {"has_relationship": False, "stage": None}
    return out
```

- [ ] **Step 4: Run, verify pass**

Run: `.venv/bin/python -m pytest tests/test_relationships.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add automations/02-youtube-sponsorship-intelligence/pipeline/relationships.py automations/02-youtube-sponsorship-intelligence/tests/test_relationships.py
git commit -m "feat: relationships stub over known_brands.json"
```

---

## Task 10: `report` — `render_slack` and `render_html`

**Files:**
- Create: `pipeline/report.py`
- Test: `tests/test_report.py`

- [ ] **Step 1: Write failing tests** (`tests/test_report.py`)
```python
import os
from pipeline import report

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "..", "email-template.html")

REPORT = {
    "month": "2026-06", "prior_month": "2026-05", "is_baseline": False,
    "ranked": [
        {"rank": 1, "brand_canonical": "betterhelp", "brand_display": "BetterHelp",
         "count": 3, "prior_count": 2, "delta": 1, "pct_change": 50.0, "direction": "up"},
        {"rank": 2, "brand_canonical": "hellofresh", "brand_display": "HelloFresh",
         "count": 2, "prior_count": 0, "delta": 2, "pct_change": None, "direction": "new"},
    ],
    "new_brands": [{"brand_display": "HelloFresh", "count": 2}],
    "dropped_brands": [{"brand_display": "Squarespace", "prior_count": 2}],
    "unmatched": [{"brand_display": "MysteryCo", "count": 5}],
}
RELATIONSHIPS = {
    "betterhelp": {"has_relationship": True, "stage": "In conversation"},
    "hellofresh": {"has_relationship": False, "stage": None},
}


def test_render_slack_contains_movers_and_flags():
    text = report.render_slack(REPORT, RELATIONSHIPS, "June 2026")
    assert "June 2026" in text
    assert "BetterHelp" in text
    assert "HelloFresh" in text
    assert "Squarespace" in text  # dropped
    assert "MysteryCo" in text  # unmatched alias candidate
    assert "In conversation" in text  # relationship stage surfaced


def test_render_html_fills_template():
    with open(TEMPLATE_PATH, encoding="utf-8") as fh:
        template = fh.read()
    html = report.render_html(REPORT, RELATIONSHIPS, template, "June 2026", "June 18, 2026",
                              narrative="BetterHelp leads with 3.")
    assert "{{ROWS}}" not in html and "{{MONTH_LABEL}}" not in html and "{{UNMATCHED}}" not in html
    assert "June 2026" in html
    assert "BetterHelp" in html
    assert "HelloFresh" in html
    assert "Squarespace" in html
    assert "MysteryCo" in html  # unmatched section rendered
    assert "BetterHelp leads with 3." in html
```

- [ ] **Step 2: Run, verify fail**

Run: `.venv/bin/python -m pytest tests/test_report.py -q`
Expected: FAIL (no module).

- [ ] **Step 3: Implement** (`pipeline/report.py`)
```python
import html as _html

_ARROW = {"up": "▲", "down": "▼", "same": "▬", "new": "✦"}


def _mom_label(r):
    if r["direction"] == "new":
        return "NEW"
    if r["direction"] == "same":
        return "▬ 0%"
    return "%s %s%%" % (_ARROW[r["direction"]], r["pct_change"])


def render_slack(report_data, relationships, month_label):
    lines = ["*Sponsorship Intelligence — %s*" % month_label]
    if report_data["is_baseline"]:
        lines.append("_(baseline month — no prior comparison)_")
    for r in report_data["ranked"]:
        rel = relationships.get(r["brand_canonical"], {})
        flag = (" · 🤝 %s" % rel.get("stage")) if rel.get("has_relationship") else ""
        lines.append("%d. %s — %d (%s)%s" % (r["rank"], r["brand_display"], r["count"], _mom_label(r), flag))
    if report_data["new_brands"]:
        lines.append("New: " + ", ".join(b["brand_display"] for b in report_data["new_brands"]))
    if report_data["dropped_brands"]:
        lines.append("Dropped: " + ", ".join(b["brand_display"] for b in report_data["dropped_brands"]))
    if report_data.get("unmatched"):
        lines.append("Unmatched (alias?): " + ", ".join(b["brand_display"] for b in report_data["unmatched"]))
    return "\n".join(lines)


def _esc(value):
    return _html.escape("" if value is None else str(value))


def render_html(report_data, relationships, template, month_label, generated_date, narrative=""):
    rows_html = []
    for r in report_data["ranked"]:
        rel = relationships.get(r["brand_canonical"], {})
        badge = ('<span class="rel">%s</span>' % _esc(rel.get("stage"))) if rel.get("has_relationship") else ""
        rows_html.append(
            "<tr><td>%d</td><td>%s</td><td>%d</td><td>%s</td><td>%s</td></tr>"
            % (r["rank"], _esc(r["brand_display"]), r["count"], _mom_label(r), badge)
        )
    new_html = ", ".join(_esc(b["brand_display"]) for b in report_data["new_brands"]) or "—"
    dropped_html = ", ".join(_esc(b["brand_display"]) for b in report_data["dropped_brands"]) or "—"
    unmatched_html = ", ".join(_esc(b["brand_display"]) for b in report_data.get("unmatched", [])) or "—"
    return (
        template
        .replace("{{MONTH_LABEL}}", _esc(month_label))
        .replace("{{GENERATED_DATE}}", _esc(generated_date))
        .replace("{{NARRATIVE}}", _esc(narrative or ""))
        .replace("{{ROWS}}", "\n".join(rows_html))
        .replace("{{NEW_BRANDS}}", new_html)
        .replace("{{DROPPED_BRANDS}}", dropped_html)
        .replace("{{UNMATCHED}}", unmatched_html)
    )
```

> Note: `_mom_label` output (`▲ 50.0%`, `NEW`) is generated from controlled strings/numbers, so it is safe to inject without escaping.

- [ ] **Step 4: Run, verify pass**

Run: `.venv/bin/python -m pytest tests/test_report.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add automations/02-youtube-sponsorship-intelligence/pipeline/report.py automations/02-youtube-sponsorship-intelligence/tests/test_report.py
git commit -m "feat: report render_slack and render_html"
```

---

## Task 11: `run` — CLI orchestrator + end-to-end integration test

**Files:**
- Create: `pipeline/run.py`
- Test: `tests/test_run.py`

- [ ] **Step 1: Write failing test** (`tests/test_run.py`)
```python
import json
import os
from pipeline import run

BASE = os.path.join(os.path.dirname(__file__), "..")


def test_end_to_end_two_months(tmp_path):
    db = str(tmp_path / "history.db")
    out_may = str(tmp_path / "may.html")
    out_jun = str(tmp_path / "jun.html")

    # Month 1 = baseline
    res_may = run.run_month(
        csv_path=os.path.join(BASE, "sample", "2026-05_sample.csv"),
        month="2026-05", config_path=os.path.join(BASE, "config.json"),
        aliases_path=os.path.join(BASE, "brand_aliases.seed.json"),
        known_brands_path=os.path.join(BASE, "known_brands.json"),
        template_path=os.path.join(BASE, "email-template.html"),
        db_path=db, out_html_path=out_may, month_label="May 2026", generated_date="June 1, 2026",
    )
    assert res_may["report"]["is_baseline"] is True
    assert os.path.exists(out_may)

    # Month 2 = comparison
    res_jun = run.run_month(
        csv_path=os.path.join(BASE, "sample", "2026-06_sample.csv"),
        month="2026-06", config_path=os.path.join(BASE, "config.json"),
        aliases_path=os.path.join(BASE, "brand_aliases.seed.json"),
        known_brands_path=os.path.join(BASE, "known_brands.json"),
        template_path=os.path.join(BASE, "email-template.html"),
        db_path=db, out_html_path=out_jun, month_label="June 2026", generated_date="July 1, 2026",
    )
    report = res_jun["report"]
    assert report["is_baseline"] is False
    by_canon = {r["brand_canonical"]: r for r in report["ranked"]}
    assert by_canon["betterhelp"]["count"] == 3
    assert by_canon["betterhelp"]["direction"] == "up"
    assert by_canon["nordvpn"]["direction"] == "down"
    assert any(b["brand_display"] == "HelloFresh" for b in report["new_brands"])
    assert any(b["brand_display"] == "Squarespace" for b in report["dropped_brands"])
    # HelloFresh has no alias entry → resolved by fallback → surfaced as an alias candidate.
    assert any(b["brand_display"] == "HelloFresh" for b in report["unmatched"])

    html = open(out_jun, encoding="utf-8").read()
    assert "BetterHelp" in html and "{{ROWS}}" not in html


def test_run_month_is_rerunnable(tmp_path):
    db = str(tmp_path / "history.db")
    args = dict(
        csv_path=os.path.join(BASE, "sample", "2026-05_sample.csv"), month="2026-05",
        config_path=os.path.join(BASE, "config.json"),
        aliases_path=os.path.join(BASE, "brand_aliases.seed.json"),
        known_brands_path=os.path.join(BASE, "known_brands.json"),
        template_path=os.path.join(BASE, "email-template.html"),
        db_path=db, out_html_path=str(tmp_path / "o.html"),
        month_label="May 2026", generated_date="June 1, 2026",
    )
    run.run_month(**args)
    res = run.run_month(**args)  # second identical run
    by_canon = {r["brand_canonical"]: r for r in res["report"]["ranked"]}
    assert by_canon["betterhelp"]["count"] == 2  # not doubled
```

- [ ] **Step 2: Run, verify fail**

Run: `.venv/bin/python -m pytest tests/test_run.py -q`
Expected: FAIL (no module).

- [ ] **Step 3: Implement** (`pipeline/run.py`)
```python
import argparse
import json

from pipeline import transform, engine, relationships, report


def _load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _build_narrative(report_data):
    if report_data["is_baseline"]:
        return "Baseline month — establishing the comparison point for future reports."
    if not report_data["ranked"]:
        return "No long-form sponsorships found this month."
    top = report_data["ranked"][0]
    bits = ["%s leads with %d sponsorships (%s vs prior month)." %
            (top["brand_display"], top["count"], top["direction"])]
    if report_data["new_brands"]:
        bits.append("New entrants: " + ", ".join(b["brand_display"] for b in report_data["new_brands"]) + ".")
    if report_data["dropped_brands"]:
        bits.append("Dropped off: " + ", ".join(b["brand_display"] for b in report_data["dropped_brands"]) + ".")
    return " ".join(bits)


def run_month(csv_path, month, config_path, aliases_path, known_brands_path,
              template_path, db_path, out_html_path, month_label, generated_date):
    config = _load_json(config_path)
    aliases = _load_json(aliases_path)
    known = relationships.load_known_brands(known_brands_path)

    raw = transform.load_csv(csv_path, config["column_map"])
    rows = transform.normalize_rows(raw, month, config, aliases)

    conn = engine.connect(db_path)
    engine.init_schema(conn)
    engine.load_month(conn, month, rows)
    report_data = engine.rank_and_diff(conn, month, config["top_n"])
    report_data["unmatched"] = transform.top_unmatched_brands(rows)

    rels = relationships.lookup_relationships(
        [r["brand_canonical"] for r in report_data["ranked"]], known)
    narrative = _build_narrative(report_data)

    with open(template_path, encoding="utf-8") as fh:
        template = fh.read()
    html = report.render_html(report_data, rels, template, month_label, generated_date, narrative)
    slack_text = report.render_slack(report_data, rels, month_label)

    with open(out_html_path, "w", encoding="utf-8") as fh:
        fh.write(html)

    # Delivery is a STUB in v1: write artifacts + print. Email (Supabase) and Slack are wired later.
    print(slack_text)
    return {"report": report_data, "relationships": rels, "html_path": out_html_path,
            "slack_text": slack_text}


def main(argv=None):
    p = argparse.ArgumentParser(description="YouTube Sponsorship Intelligence monthly run")
    p.add_argument("--csv", required=True)
    p.add_argument("--month", required=True, help="YYYY-MM")
    p.add_argument("--config", default="config.json")
    p.add_argument("--aliases", default="brand_aliases.seed.json")
    p.add_argument("--known-brands", default="known_brands.json")
    p.add_argument("--template", default="email-template.html")
    p.add_argument("--db", default="history.db")
    p.add_argument("--out", default="report.html")
    p.add_argument("--month-label", required=True)
    p.add_argument("--generated-date", required=True)
    a = p.parse_args(argv)
    run_month(a.csv, a.month, a.config, a.aliases, a.known_brands, a.template,
              a.db, a.out, a.month_label, a.generated_date)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run, verify pass + run full suite**

Run: `.venv/bin/python -m pytest tests/ -q`
Expected: PASS (all tests).

- [ ] **Step 5: Manual end-to-end smoke (optional but recommended)**

Run:
```bash
.venv/bin/python -m pipeline.run --csv sample/2026-05_sample.csv --month 2026-05 --db history.db --out may.html --month-label "May 2026" --generated-date "June 1, 2026"
.venv/bin/python -m pipeline.run --csv sample/2026-06_sample.csv --month 2026-06 --db history.db --out june.html --month-label "June 2026" --generated-date "July 1, 2026"
```
Expected: Slack-style text prints for each; `may.html` and `june.html` written; June shows BetterHelp ▲, NordVPN ▼, HelloFresh NEW, Squarespace dropped.

- [ ] **Step 6: Commit** (ignore generated artifacts)

Append to root `.gitignore`: `automations/02-youtube-sponsorship-intelligence/*.db` and `automations/02-youtube-sponsorship-intelligence/*.html` EXCEPT the template — instead add specific ignores:
```
automations/02-youtube-sponsorship-intelligence/history.db
automations/02-youtube-sponsorship-intelligence/may.html
automations/02-youtube-sponsorship-intelligence/june.html
automations/02-youtube-sponsorship-intelligence/report.html
```
```bash
git add automations/02-youtube-sponsorship-intelligence/pipeline/run.py automations/02-youtube-sponsorship-intelligence/tests/test_run.py .gitignore
git commit -m "feat: run.py CLI orchestrator with end-to-end test"
```

---

## Task 12: Production docs (deferred wiring) + spec pointer

**Files:**
- Create: `automations/02-youtube-sponsorship-intelligence/spec.md`
- Create: `automations/02-youtube-sponsorship-intelligence/routine.md`
- Create: `automations/02-youtube-sponsorship-intelligence/routine-prompt.txt`

Documentation task (no tests). Marks exactly what must be wired when connectors arrive.

- [ ] **Step 1: Create `spec.md`**
```markdown
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
```

- [ ] **Step 2: Create `routine.md`** (production deployment doc, mirrors the film-slate one)
```markdown
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
```

- [ ] **Step 3: Create `routine-prompt.txt`** (DRAFT — clearly marked)
```text
[DRAFT — finalize when Supabase/HubSpot/Slack connectors and the real recipient/channel exist.]

You are running the monthly YouTube Sponsorship Intelligence digest for Good Story Studios.

1. Inputs: the month (YYYY-MM), the path/link to this month's sponsored-video CSV, and config.json.
2. Pull prior months' brand_monthly_counts from Supabase into a local SQLite DB, then run the
   tested pipeline/ over this month's CSV (SQLite is the compute; Supabase is just durable storage).
   At the end, upsert this month's brand_monthly_counts back to Supabase.
3. The pipeline aggregates long-form rows, ranks Top-N, computes month-over-month vs the prior
   stored month (up/down/same/new, plus new and dropped brands), and surfaces top unmatched brands
   for alias review. First month = baseline.
4. For the Top-N brands, query HubSpot (MCP) for an existing relationship + deal stage.
5. Write a 2-3 sentence narrative of what moved; assemble the HTML report from email-template.html.
6. Email the report to config.final_recipient (Supabase send pattern) AND post a Slack summary to
   config.slack_channel. FIRST RUN: owner-only until validated.

Deterministic counting/ranking is done in code (see pipeline/), NOT by you. You write the narrative.
```

- [ ] **Step 4: Commit**
```bash
git add automations/02-youtube-sponsorship-intelligence/spec.md automations/02-youtube-sponsorship-intelligence/routine.md automations/02-youtube-sponsorship-intelligence/routine-prompt.txt
git commit -m "docs: spec pointer + production routine docs (deferred wiring)"
```

---

## Final verification

- [ ] **Run the full suite**

Run (from the automation dir): `.venv/bin/python -m pytest tests/ -q`
Expected: all tests PASS.

- [ ] **Confirm clean tree**

Run: `git status -s`
Expected: empty (all committed; `.venv/`, `*.db`, generated `*.html` ignored).
