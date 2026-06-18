def test_package_imports():
    import pipeline  # noqa: F401


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


# ---------------------------------------------------------------------------
# Fix 1: UTF-8 BOM test
# ---------------------------------------------------------------------------

def test_load_csv_with_bom_parses_first_column(tmp_path):
    """CSV written with a UTF-8 BOM must not corrupt the first header."""
    csv_path = tmp_path / "bom.csv"
    # Write with utf-8-sig so the file starts with the BOM byte sequence.
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as fh:
        fh.write("Video Title,Video URL,Channel,Sponsor,Publish Date,Length (s)\n")
        fh.write("My Title,https://yt/z,ChanZ,Acme,2026-06-01,700\n")
    rows = transform.load_csv(str(csv_path), COLUMN_MAP)
    assert len(rows) == 1
    assert rows[0]["video_title"] == "My Title", (
        "video_title was None — BOM corrupted the first header column"
    )


# ---------------------------------------------------------------------------
# Fix 2a: is_aliased for canonical-spelled sponsors
# ---------------------------------------------------------------------------

def test_normalize_rows_canonical_sponsor_is_aliased_true():
    """Raw 'BetterHelp' resolves to canonical 'betterhelp', which is an alias
    *target* — it should be marked is_aliased=True so it won't surface as a
    review candidate.  'HelloFresh' has no alias entry at all → is_aliased=False."""
    config = _load_json(CONFIG_PATH)
    aliases = _load_json(ALIASES_PATH)
    rows = [
        {"video_title": "G", "video_url": "https://yt/g", "channel": "C",
         "sponsor": "BetterHelp",   # canonical spelling — not an alias *key*
         "publish_date": "2026-06-02", "length_seconds": 700, "long_form_flag": None},
        {"video_title": "K", "video_url": "https://yt/k", "channel": "C",
         "sponsor": "HelloFresh",   # genuinely unknown brand
         "publish_date": "2026-06-18", "length_seconds": 800, "long_form_flag": None},
    ]
    out = transform.normalize_rows(rows, "2026-06", config, aliases)
    by_canon = {r["brand_canonical"]: r for r in out}
    assert by_canon["betterhelp"]["is_aliased"] is True, (
        "BetterHelp (canonical spelling) should be is_aliased=True"
    )
    assert by_canon["hellofresh"]["is_aliased"] is False, (
        "HelloFresh (unknown brand) should be is_aliased=False"
    )


# ---------------------------------------------------------------------------
# Fix 2b: top_unmatched_brands exclude parameter
# ---------------------------------------------------------------------------

def test_top_unmatched_brands_exclude_removes_known():
    """Brands in the exclude set should never appear in the unmatched list."""
    rows = [
        {"brand_canonical": "hellofresh", "brand_display": "HelloFresh",
         "is_long_form": True, "is_aliased": False},
        {"brand_canonical": "nordvpn", "brand_display": "NordVPN",
         "is_long_form": True, "is_aliased": False},
    ]
    out = transform.top_unmatched_brands(rows, limit=10, exclude={"nordvpn"})
    canonicals = [item["brand_display"] for item in out]
    assert "HelloFresh" in canonicals, "HelloFresh should still appear"
    assert "NordVPN" not in canonicals, "NordVPN should be excluded"
