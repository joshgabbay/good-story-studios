from pipeline import engine


def _row(month, url, canon, display, long_form=True):
    return {
        "month": month, "video_title": "t", "video_url": url, "channel": "c",
        "brand_canonical": canon, "brand_display": display, "publish_date": "2026-05-01",
        "length_seconds": 700, "is_long_form": long_form,
    }


def test_load_month_aggregates_long_form_only():
    conn = engine.connect(":memory:")
    engine.init_schema(conn)
    rows = [
        _row("2026-05", "https://yt/a", "betterhelp", "BetterHelp"),
        _row("2026-05", "https://yt/c", "betterhelp", "BetterHelp"),
        _row("2026-05", "https://yt/d", "shortbrand", "ShortBrand", long_form=False),
    ]
    engine.load_month(conn, "2026-05", rows)
    counts = dict(conn.execute(
        "SELECT brand_canonical, sponsorship_count FROM brand_monthly_counts WHERE month='2026-05'"
    ).fetchall())
    assert counts == {"betterhelp": 2}  # short-form excluded from counts


def test_load_month_is_idempotent():
    conn = engine.connect(":memory:")
    engine.init_schema(conn)
    rows = [_row("2026-05", "https://yt/a", "betterhelp", "BetterHelp")]
    engine.load_month(conn, "2026-05", rows)
    engine.load_month(conn, "2026-05", rows)  # re-run same month
    total = conn.execute(
        "SELECT sponsorship_count FROM brand_monthly_counts WHERE month='2026-05' AND brand_canonical='betterhelp'"
    ).fetchone()[0]
    assert total == 1  # not doubled
