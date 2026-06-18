import json
import os
from pipeline import run

BASE = os.path.join(os.path.dirname(__file__), "..")


def test_end_to_end_two_months(tmp_path):
    db = str(tmp_path / "history.db")
    out_may = str(tmp_path / "may.html")
    out_jun = str(tmp_path / "jun.html")

    # Month 1 = baseline
    res_may = run.run_month(
        csv_path=os.path.join(BASE, "sample", "2026-05_sample.csv"),
        month="2026-05", config_path=os.path.join(BASE, "config.json"),
        aliases_path=os.path.join(BASE, "brand_aliases.seed.json"),
        known_brands_path=os.path.join(BASE, "known_brands.json"),
        template_path=os.path.join(BASE, "email-template.html"),
        db_path=db, out_html_path=out_may, month_label="May 2026", generated_date="June 1, 2026",
    )
    assert res_may["report"]["is_baseline"] is True
    assert os.path.exists(out_may)

    # Month 2 = comparison
    res_jun = run.run_month(
        csv_path=os.path.join(BASE, "sample", "2026-06_sample.csv"),
        month="2026-06", config_path=os.path.join(BASE, "config.json"),
        aliases_path=os.path.join(BASE, "brand_aliases.seed.json"),
        known_brands_path=os.path.join(BASE, "known_brands.json"),
        template_path=os.path.join(BASE, "email-template.html"),
        db_path=db, out_html_path=out_jun, month_label="June 2026", generated_date="July 1, 2026",
    )
    report = res_jun["report"]
    assert report["is_baseline"] is False
    by_canon = {r["brand_canonical"]: r for r in report["ranked"]}
    assert by_canon["betterhelp"]["count"] == 3
    assert by_canon["betterhelp"]["direction"] == "up"
    assert by_canon["nordvpn"]["direction"] == "down"
    assert any(b["brand_display"] == "HelloFresh" for b in report["new_brands"])
    assert any(b["brand_display"] == "Squarespace" for b in report["dropped_brands"])
    # HelloFresh has no alias entry → resolved by fallback → surfaced as an alias candidate.
    assert any(b["brand_display"] == "HelloFresh" for b in report["unmatched"])

    html = open(out_jun, encoding="utf-8").read()
    assert "BetterHelp" in html and "{{ROWS}}" not in html


def test_run_month_is_rerunnable(tmp_path):
    db = str(tmp_path / "history.db")
    args = dict(
        csv_path=os.path.join(BASE, "sample", "2026-05_sample.csv"), month="2026-05",
        config_path=os.path.join(BASE, "config.json"),
        aliases_path=os.path.join(BASE, "brand_aliases.seed.json"),
        known_brands_path=os.path.join(BASE, "known_brands.json"),
        template_path=os.path.join(BASE, "email-template.html"),
        db_path=db, out_html_path=str(tmp_path / "o.html"),
        month_label="May 2026", generated_date="June 1, 2026",
    )
    run.run_month(**args)
    res = run.run_month(**args)  # second identical run
    by_canon = {r["brand_canonical"]: r for r in res["report"]["ranked"]}
    assert by_canon["betterhelp"]["count"] == 2  # not doubled
