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
