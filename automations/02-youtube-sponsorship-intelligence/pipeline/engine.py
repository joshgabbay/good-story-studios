import sqlite3


def connect(db_path=":memory:"):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS sponsorship_rows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT NOT NULL,
            video_title TEXT, video_url TEXT, channel TEXT,
            brand_canonical TEXT NOT NULL, brand_display TEXT,
            publish_date TEXT, length_seconds INTEGER, is_long_form INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS brand_monthly_counts (
            month TEXT NOT NULL,
            brand_canonical TEXT NOT NULL,
            brand_display TEXT,
            sponsorship_count INTEGER NOT NULL,
            PRIMARY KEY (month, brand_canonical)
        );
        """
    )
    conn.commit()


def load_month(conn, month, rows):
    """Idempotent: replace this month's raw rows and re-aggregate long-form counts."""
    conn.execute("DELETE FROM sponsorship_rows WHERE month = ?", (month,))
    conn.execute("DELETE FROM brand_monthly_counts WHERE month = ?", (month,))
    conn.executemany(
        """INSERT INTO sponsorship_rows
           (month, video_title, video_url, channel, brand_canonical, brand_display,
            publish_date, length_seconds, is_long_form)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        [(r["month"], r["video_title"], r["video_url"], r["channel"], r["brand_canonical"],
          r["brand_display"], r["publish_date"], r["length_seconds"], 1 if r["is_long_form"] else 0)
         for r in rows],
    )
    conn.execute(
        """INSERT INTO brand_monthly_counts (month, brand_canonical, brand_display, sponsorship_count)
           SELECT month, brand_canonical, MIN(brand_display), COUNT(*)
           FROM sponsorship_rows
           WHERE month = ? AND is_long_form = 1
           GROUP BY month, brand_canonical""",
        (month,),
    )
    conn.commit()


def _counts_for_month(conn, month):
    rows = conn.execute(
        "SELECT brand_canonical, brand_display, sponsorship_count FROM brand_monthly_counts WHERE month = ?",
        (month,),
    ).fetchall()
    return {canon: {"display": display, "count": count} for canon, display, count in rows}


def _prior_month(conn, month):
    row = conn.execute(
        "SELECT MAX(month) FROM brand_monthly_counts WHERE month < ?", (month,)
    ).fetchone()
    return row[0] if row and row[0] else None


def rank_and_diff(conn, month, top_n):
    current = _counts_for_month(conn, month)
    prior_month = _prior_month(conn, month)
    prior = _counts_for_month(conn, prior_month) if prior_month else {}
    is_baseline = prior_month is None

    ordered = sorted(current.items(), key=lambda kv: (-kv[1]["count"], kv[0]))
    ranked = []
    for i, (canon, cur) in enumerate(ordered[:top_n], start=1):
        prior_count = prior.get(canon, {}).get("count", 0)
        delta = cur["count"] - prior_count
        if prior_count == 0:
            direction, pct = "new", None
        elif delta > 0:
            direction, pct = "up", round(delta / prior_count * 100, 1)
        elif delta < 0:
            direction, pct = "down", round(delta / prior_count * 100, 1)
        else:
            direction, pct = "same", 0.0
        ranked.append({
            "rank": i, "brand_canonical": canon, "brand_display": cur["display"],
            "count": cur["count"], "prior_count": prior_count, "delta": delta,
            "pct_change": pct, "direction": direction,
        })

    # `ordered` is sorted by count desc; cap to top_n so a 25k-row month doesn't emit
    # hundreds of tiny new brands. Baseline has nothing to compare against.
    new_brands = (
        [{"brand_display": cur["display"], "count": cur["count"]}
         for canon, cur in ordered if canon not in prior][:top_n]
        if not is_baseline else []
    )

    dropped = [
        {"brand_display": p["display"], "prior_count": p["count"]}
        for canon, p in sorted(prior.items(), key=lambda kv: -kv[1]["count"])
        if canon not in current
    ][:top_n]

    return {
        "month": month, "prior_month": prior_month, "is_baseline": is_baseline,
        "ranked": ranked, "new_brands": new_brands, "dropped_brands": dropped,
    }
