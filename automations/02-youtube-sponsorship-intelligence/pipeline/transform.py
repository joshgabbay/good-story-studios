import csv
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


def _to_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def load_csv(path, column_map):
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for raw in reader:
            row = {}
            for field, source_col in column_map.items():
                if source_col is None or source_col not in raw:
                    row[field] = None
                else:
                    row[field] = raw[source_col]
            row["length_seconds"] = _to_int(row.get("length_seconds"))
            rows.append(row)
    return rows


def resolve_brand(raw_sponsor, aliases):
    key = normalize_key(raw_sponsor)
    if key in aliases:
        a = aliases[key]
        return a["canonical"], a["display"]
    return key, str(raw_sponsor).strip()
