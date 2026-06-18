"""Helpers for growing the brand-alias map from the monthly 'unmatched brands' list.

The report surfaces fallback brand names that aren't in the alias map. Use ``add_alias`` to fold
a name (or a misspelled variant) into a canonical brand so future months stop fragmenting it.
"""

from pipeline.transform import normalize_key


def add_alias(aliases, raw_name, canonical, display=None):
    """Return a new alias map with ``raw_name`` mapped to ``canonical``.

    The key is the normalized form of ``raw_name`` (so 'Better Help' and 'betterhelp.com' are
    stored consistently). ``display`` defaults to ``raw_name`` trimmed. Pure — does not mutate
    the input.
    """
    key = normalize_key(raw_name)
    if not key:
        raise ValueError("raw_name normalizes to an empty key")
    if not canonical:
        raise ValueError("canonical is required")
    updated = dict(aliases)
    updated[key] = {"canonical": canonical, "display": display or str(raw_name).strip()}
    return updated
