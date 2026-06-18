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


def normalize_rows(raw_rows, month, config, aliases):
    delimiter = config["multi_sponsor"]["delimiter"]
    long_form_cfg = config["long_form"]
    out = []
    seen = set()
    for r in raw_rows:
        long_form = is_long_form(r.get("length_seconds"), r.get("long_form_flag"), long_form_cfg)
        for sponsor in split_sponsors(r.get("sponsor"), delimiter):
            canonical, display = resolve_brand(sponsor, aliases)
            if not canonical:
                continue
            dedupe = (r.get("video_url"), canonical)
            if dedupe in seen:
                continue
            seen.add(dedupe)
            out.append({
                "month": month,
                "video_title": r.get("video_title"),
                "video_url": r.get("video_url"),
                "channel": r.get("channel"),
                "brand_canonical": canonical,
                "brand_display": display,
                "publish_date": r.get("publish_date"),
                "length_seconds": r.get("length_seconds"),
                "is_long_form": long_form,
                "is_aliased": normalize_key(sponsor) in aliases,
            })
    return out


def top_unmatched_brands(rows, limit=10):
    """Top long-form brands resolved by fallback (not in the alias map) — alias candidates."""
    counts, displays = {}, {}
    for r in rows:
        if r["is_long_form"] and not r.get("is_aliased", True):
            canon = r["brand_canonical"]
            counts[canon] = counts.get(canon, 0) + 1
            displays.setdefault(canon, r["brand_display"])
    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]
    return [{"brand_display": displays[c], "count": n} for c, n in ordered]
