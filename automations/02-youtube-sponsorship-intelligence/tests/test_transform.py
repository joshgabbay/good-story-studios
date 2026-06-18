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
