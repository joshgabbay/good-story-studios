import html as _html

_ARROW = {"up": "▲", "down": "▼", "same": "▬", "new": "✦"}


def _mom_label(r):
    if r["direction"] == "new":
        return "NEW"
    if r["direction"] == "same":
        return "▬ 0%"
    return "%s %s%%" % (_ARROW[r["direction"]], r["pct_change"])


def render_slack(report_data, relationships, month_label):
    lines = ["*Sponsorship Intelligence — %s*" % month_label]
    if report_data["is_baseline"]:
        lines.append("_(baseline month — no prior comparison)_")
    for r in report_data["ranked"]:
        rel = relationships.get(r["brand_canonical"], {})
        flag = (" · 🤝 %s" % rel.get("stage")) if rel.get("has_relationship") else ""
        lines.append("%d. %s — %d (%s)%s" % (r["rank"], r["brand_display"], r["count"], _mom_label(r), flag))
    if report_data["new_brands"]:
        lines.append("New: " + ", ".join(b["brand_display"] for b in report_data["new_brands"]))
    if report_data["dropped_brands"]:
        lines.append("Dropped: " + ", ".join(b["brand_display"] for b in report_data["dropped_brands"]))
    if report_data.get("unmatched"):
        lines.append("Unmatched (alias?): " + ", ".join(b["brand_display"] for b in report_data["unmatched"]))
    return "\n".join(lines)


def _esc(value):
    return _html.escape("" if value is None else str(value))


def render_html(report_data, relationships, template, month_label, generated_date, narrative=""):
    rows_html = []
    for r in report_data["ranked"]:
        rel = relationships.get(r["brand_canonical"], {})
        badge = ('<span class="rel">%s</span>' % _esc(rel.get("stage"))) if rel.get("has_relationship") else ""
        rows_html.append(
            "<tr><td>%d</td><td>%s</td><td>%d</td><td>%s</td><td>%s</td></tr>"
            % (r["rank"], _esc(r["brand_display"]), r["count"], _mom_label(r), badge)
        )
    new_html = ", ".join(_esc(b["brand_display"]) for b in report_data["new_brands"]) or "—"
    dropped_html = ", ".join(_esc(b["brand_display"]) for b in report_data["dropped_brands"]) or "—"
    unmatched_html = ", ".join(_esc(b["brand_display"]) for b in report_data.get("unmatched", [])) or "—"
    return (
        template
        .replace("{{MONTH_LABEL}}", _esc(month_label))
        .replace("{{GENERATED_DATE}}", _esc(generated_date))
        .replace("{{NARRATIVE}}", _esc(narrative or ""))
        .replace("{{ROWS}}", "\n".join(rows_html))
        .replace("{{NEW_BRANDS}}", new_html)
        .replace("{{DROPPED_BRANDS}}", dropped_html)
        .replace("{{UNMATCHED}}", unmatched_html)
    )
