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
    if report_data.get("warning"):
        lines.append("⚠️ %s" % report_data["warning"])
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


def render_html(report_data, relationships, template, month_label, generated_date,
                narrative="", show_unmatched=True):
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

    warning = report_data.get("warning")
    warning_html = ('<div class="warn">⚠️ %s</div>' % _esc(warning)) if warning else ""

    # The "unmatched / review for aliasing" block is an internal QA aid. For an external
    # (client) recipient, omit the whole section.
    if show_unmatched:
        unmatched_html = ", ".join(_esc(b["brand_display"]) for b in report_data.get("unmatched", [])) or "—"
        unmatched_section = (
            '<div class="section"><strong>Top unmatched brands (review for aliasing):</strong> %s</div>'
            % unmatched_html
        )
    else:
        unmatched_section = ""

    return (
        template
        .replace("{{MONTH_LABEL}}", _esc(month_label))
        .replace("{{GENERATED_DATE}}", _esc(generated_date))
        .replace("{{NARRATIVE}}", _esc(narrative or ""))
        .replace("{{WARNING}}", warning_html)
        .replace("{{ROWS}}", "\n".join(rows_html))
        .replace("{{NEW_BRANDS}}", new_html)
        .replace("{{DROPPED_BRANDS}}", dropped_html)
        .replace("{{UNMATCHED_SECTION}}", unmatched_section)
    )
