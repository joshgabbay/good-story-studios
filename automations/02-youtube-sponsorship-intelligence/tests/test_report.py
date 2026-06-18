import os
from pipeline import report

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "..", "email-template.html")

REPORT = {
    "month": "2026-06", "prior_month": "2026-05", "is_baseline": False,
    "ranked": [
        {"rank": 1, "brand_canonical": "betterhelp", "brand_display": "BetterHelp",
         "count": 3, "prior_count": 2, "delta": 1, "pct_change": 50.0, "direction": "up"},
        {"rank": 2, "brand_canonical": "hellofresh", "brand_display": "HelloFresh",
         "count": 2, "prior_count": 0, "delta": 2, "pct_change": None, "direction": "new"},
    ],
    "new_brands": [{"brand_display": "HelloFresh", "count": 2}],
    "dropped_brands": [{"brand_display": "Squarespace", "prior_count": 2}],
    "unmatched": [{"brand_display": "MysteryCo", "count": 5}],
}
RELATIONSHIPS = {
    "betterhelp": {"has_relationship": True, "stage": "In conversation"},
    "hellofresh": {"has_relationship": False, "stage": None},
}


def test_render_slack_contains_movers_and_flags():
    text = report.render_slack(REPORT, RELATIONSHIPS, "June 2026")
    assert "June 2026" in text
    assert "BetterHelp" in text
    assert "HelloFresh" in text
    assert "Squarespace" in text  # dropped
    assert "MysteryCo" in text  # unmatched alias candidate
    assert "In conversation" in text  # relationship stage surfaced


def test_render_html_fills_template():
    with open(TEMPLATE_PATH, encoding="utf-8") as fh:
        template = fh.read()
    html = report.render_html(REPORT, RELATIONSHIPS, template, "June 2026", "June 18, 2026",
                              narrative="BetterHelp leads with 3.")
    # No template placeholders left unfilled.
    for ph in ("{{ROWS}}", "{{MONTH_LABEL}}", "{{UNMATCHED_SECTION}}", "{{WARNING}}", "{{NARRATIVE}}"):
        assert ph not in html
    assert "June 2026" in html
    assert "BetterHelp" in html
    assert "HelloFresh" in html
    assert "Squarespace" in html
    assert "MysteryCo" in html  # unmatched section rendered (internal default)
    assert "BetterHelp leads with 3." in html


def test_render_html_external_omits_unmatched_section():
    with open(TEMPLATE_PATH, encoding="utf-8") as fh:
        template = fh.read()
    html = report.render_html(REPORT, RELATIONSHIPS, template, "June 2026", "June 18, 2026",
                              narrative="x", show_unmatched=False)
    assert "MysteryCo" not in html
    assert "review for aliasing" not in html
    assert "{{UNMATCHED_SECTION}}" not in html  # placeholder still filled (with empty string)
    assert "BetterHelp" in html  # rest of the report is intact


def test_render_html_warning_banner_shown_when_present():
    with open(TEMPLATE_PATH, encoding="utf-8") as fh:
        template = fh.read()
    data = dict(REPORT, warning="No video length data found — every video was counted as long-form.")
    html = report.render_html(data, RELATIONSHIPS, template, "June 2026", "June 18, 2026")
    assert "No video length data found" in html
    assert 'class="warn"' in html


def test_render_slack_includes_warning():
    data = dict(REPORT, warning="No video length data found — every video was counted as long-form.")
    text = report.render_slack(data, RELATIONSHIPS, "June 2026")
    assert "⚠️" in text and "No video length data found" in text
