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
