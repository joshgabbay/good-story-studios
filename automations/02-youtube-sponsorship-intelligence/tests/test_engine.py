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


def _seed_two_months(conn):
    engine.init_schema(conn)
    may = [
        _row("2026-05", "https://yt/a", "betterhelp", "BetterHelp"),
        _row("2026-05", "https://yt/c", "betterhelp", "BetterHelp"),
        _row("2026-05", "https://yt/e", "nordvpn", "NordVPN"),
        _row("2026-05", "https://yt/b", "nordvpn", "NordVPN"),
        _row("2026-05", "https://yt/f", "squarespace", "Squarespace"),
        _row("2026-05", "https://yt/b2", "squarespace", "Squarespace"),
    ]
    june = [
        _row("2026-06", "https://yt/g", "betterhelp", "BetterHelp"),
        _row("2026-06", "https://yt/h", "betterhelp", "BetterHelp"),
        _row("2026-06", "https://yt/i", "betterhelp", "BetterHelp"),
        _row("2026-06", "https://yt/j", "nordvpn", "NordVPN"),
        _row("2026-06", "https://yt/k", "hellofresh", "HelloFresh"),
        _row("2026-06", "https://yt/l", "hellofresh", "HelloFresh"),
    ]
    engine.load_month(conn, "2026-05", may)
    engine.load_month(conn, "2026-06", june)


def test_rank_and_diff_baseline_first_month():
    conn = engine.connect(":memory:")
    engine.init_schema(conn)
    engine.load_month(conn, "2026-05", [_row("2026-05", "https://yt/a", "betterhelp", "BetterHelp")])
    out = engine.rank_and_diff(conn, "2026-05", top_n=25)
    assert out["is_baseline"] is True
    assert out["prior_month"] is None
    assert out["ranked"][0]["direction"] == "new"
    assert out["dropped_brands"] == []


def test_rank_and_diff_month_over_month():
    conn = engine.connect(":memory:")
    _seed_two_months(conn)
    out = engine.rank_and_diff(conn, "2026-06", top_n=25)
    assert out["is_baseline"] is False
    assert out["prior_month"] == "2026-05"

    by_canon = {r["brand_canonical"]: r for r in out["ranked"]}
    assert by_canon["betterhelp"]["count"] == 3
    assert by_canon["betterhelp"]["prior_count"] == 2
    assert by_canon["betterhelp"]["direction"] == "up"
    assert by_canon["betterhelp"]["pct_change"] == 50.0
    assert by_canon["nordvpn"]["direction"] == "down"
    assert by_canon["hellofresh"]["direction"] == "new"
    assert by_canon["hellofresh"]["pct_change"] is None

    new_displays = [b["brand_display"] for b in out["new_brands"]]
    dropped_displays = [b["brand_display"] for b in out["dropped_brands"]]
    assert "HelloFresh" in new_displays
    assert "Squarespace" in dropped_displays


def test_rank_and_diff_respects_top_n():
    conn = engine.connect(":memory:")
    _seed_two_months(conn)
    out = engine.rank_and_diff(conn, "2026-06", top_n=1)
    assert len(out["ranked"]) == 1
    assert out["ranked"][0]["brand_canonical"] == "betterhelp"
