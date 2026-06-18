"""Cross-month history sync between the local SQLite compute DB and durable storage (Supabase).

Storage model: SQLite is the per-run compute engine; Supabase only persists
``brand_monthly_counts`` across runs (the cloud routine's local DB is ephemeral). This module
is the seam:

  * ``pull_prior_counts`` loads previously-stored monthly counts INTO the local DB before a run,
    so month-over-month has history.
  * ``push_month_counts`` writes this month's counts OUT to durable storage after a run.

Both take an injected callable for the actual storage I/O, so the module is fully testable with
fakes today; at deploy the callables are backed by the Supabase MCP (a SELECT and an upsert).
The tested ``pipeline/`` code never changes.
"""


def pull_prior_counts(conn, fetch_counts):
    """Load durably-stored monthly counts into the local ``brand_monthly_counts`` table.

    ``fetch_counts()`` returns an iterable of dict rows with keys: ``month``,
    ``brand_canonical``, ``brand_display``, ``sponsorship_count``. Existing rows for the same
    (month, brand) are replaced. Returns the number of rows loaded.
    """
    rows = list(fetch_counts())
    conn.executemany(
        "INSERT OR REPLACE INTO brand_monthly_counts "
        "(month, brand_canonical, brand_display, sponsorship_count) VALUES (?, ?, ?, ?)",
        [(r["month"], r["brand_canonical"], r.get("brand_display"), r["sponsorship_count"])
         for r in rows],
    )
    conn.commit()
    return len(rows)


def push_month_counts(conn, month, upsert_counts):
    """Persist this month's counts to durable storage.

    Reads ``brand_monthly_counts`` for ``month`` from the local DB and hands them to
    ``upsert_counts(rows)`` (a callable that writes them durably — idempotent per (month,
    brand)). Returns the number of rows pushed.
    """
    cur = conn.execute(
        "SELECT month, brand_canonical, brand_display, sponsorship_count "
        "FROM brand_monthly_counts WHERE month = ? ORDER BY brand_canonical",
        (month,),
    )
    rows = [{"month": m, "brand_canonical": b, "brand_display": d, "sponsorship_count": c}
            for (m, b, d, c) in cur.fetchall()]
    upsert_counts(rows)
    return len(rows)
