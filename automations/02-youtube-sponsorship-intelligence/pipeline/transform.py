import re


def normalize_key(raw):
    """Lowercase, strip, replace non-alphanumeric runs with single spaces."""
    if not raw:
        return ""
    s = str(raw).lower().strip()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return s.strip()


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
