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
