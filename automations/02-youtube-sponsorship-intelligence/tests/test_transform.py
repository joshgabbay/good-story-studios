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
