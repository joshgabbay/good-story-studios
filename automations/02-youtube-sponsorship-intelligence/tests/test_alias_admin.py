import pytest

from pipeline import alias_admin


def test_add_alias_normalizes_key_and_sets_fields():
    out = alias_admin.add_alias({}, "Better Help", "betterhelp")
    assert out == {"better help": {"canonical": "betterhelp", "display": "Better Help"}}


def test_add_alias_custom_display_and_domain_variant():
    out = alias_admin.add_alias({}, "betterhelp.com", "betterhelp", display="BetterHelp")
    assert out == {"betterhelp com": {"canonical": "betterhelp", "display": "BetterHelp"}}


def test_add_alias_does_not_mutate_input():
    original = {"x": {"canonical": "x", "display": "X"}}
    out = alias_admin.add_alias(original, "Nord VPN", "nordvpn")
    assert "nord vpn" in out and "nord vpn" not in original


def test_add_alias_rejects_empty():
    with pytest.raises(ValueError):
        alias_admin.add_alias({}, "!!!", "x")  # normalizes to empty key
    with pytest.raises(ValueError):
        alias_admin.add_alias({}, "Brand", "")  # no canonical
