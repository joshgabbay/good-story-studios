import re


def normalize_key(raw):
    """Lowercase, strip, replace non-alphanumeric runs with single spaces."""
    if not raw:
        return ""
    s = str(raw).lower().strip()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return s.strip()
