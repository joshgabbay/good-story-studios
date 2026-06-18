from pipeline import engine, history_store


def _conn():
    conn = engine.connect(":memory:")
    engine.init_schema(conn)
    return conn


def test_pull_prior_counts_loads_history_for_mom():
    conn = _conn()
    # Simulate durable storage holding a prior month (May).
    stored = [
        {"month": "2026-05", "brand_canonical": "betterhelp", "brand_display": "BetterHelp",
         "sponsorship_count": 2},
        {"month": "2026-05", "brand_canonical": "nordvpn", "brand_display": "NordVPN",
         "sponsorship_count": 5},
    ]
    n = history_store.pull_prior_counts(conn, lambda: stored)
    assert n == 2

    # Now load June locally and confirm month-over-month sees the pulled May history.
    june_rows = [
        {"month": "2026-06", "video_title": "t", "video_url": "u1", "channel": "c",
         "brand_canonical": "betterhelp", "brand_display": "BetterHelp", "publish_date": "x",
         "length_seconds": 700, "is_long_form": True},
    ]
    engine.load_month(conn, "2026-06", june_rows)
    out = engine.rank_and_diff(conn, "2026-06", top_n=25)
    assert out["prior_month"] == "2026-05"
    bh = {r["brand_canonical"]: r for r in out["ranked"]}["betterhelp"]
    assert bh["prior_count"] == 2 and bh["count"] == 1 and bh["direction"] == "down"


def test_pull_is_idempotent():
    conn = _conn()
    stored = [{"month": "2026-05", "brand_canonical": "betterhelp",
               "brand_display": "BetterHelp", "sponsorship_count": 2}]
    history_store.pull_prior_counts(conn, lambda: stored)
    history_store.pull_prior_counts(conn, lambda: stored)  # second pull
    total = conn.execute(
        "SELECT sponsorship_count FROM brand_monthly_counts "
        "WHERE month='2026-05' AND brand_canonical='betterhelp'"
    ).fetchone()[0]
    assert total == 2  # replaced, not doubled


def test_push_month_counts_hands_local_counts_to_upsert():
    conn = _conn()
    rows = [
        {"month": "2026-06", "video_title": "t", "video_url": "u1", "channel": "c",
         "brand_canonical": "betterhelp", "brand_display": "BetterHelp", "publish_date": "x",
         "length_seconds": 700, "is_long_form": True},
        {"month": "2026-06", "video_title": "t", "video_url": "u2", "channel": "c",
         "brand_canonical": "betterhelp", "brand_display": "BetterHelp", "publish_date": "x",
         "length_seconds": 700, "is_long_form": True},
    ]
    engine.load_month(conn, "2026-06", rows)

    captured = {}
    def fake_upsert(pushed):
        captured["rows"] = pushed

    n = history_store.push_month_counts(conn, "2026-06", fake_upsert)
    assert n == 1
    assert captured["rows"] == [
        {"month": "2026-06", "brand_canonical": "betterhelp",
         "brand_display": "BetterHelp", "sponsorship_count": 2}
    ]
