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
