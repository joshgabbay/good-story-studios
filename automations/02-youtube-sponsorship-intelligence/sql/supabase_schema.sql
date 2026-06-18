-- Supabase (Postgres) schema for the YouTube Sponsorship Intelligence digest.
--
-- Storage model (decided in the design spec): SQLite stays the per-run COMPUTE engine;
-- Supabase is only the durable CROSS-MONTH history store. Each run:
--   1. pulls prior months' brand_monthly_counts from Supabase into the local SQLite DB,
--   2. runs the tested pipeline/ to produce this month's rows + counts,
--   3. upserts this month's brand_monthly_counts back to Supabase (idempotent per month).
--
-- sponsorship_rows is optional in Supabase (the raw layer can stay local); persist it only
-- if you want the full raw history queryable in the warehouse. brand_monthly_counts is the
-- one table the month-over-month logic actually needs persisted.

create table if not exists brand_monthly_counts (
    month             text    not null,           -- 'YYYY-MM'
    brand_canonical   text    not null,
    brand_display     text,
    sponsorship_count integer not null,
    updated_at        timestamptz not null default now(),
    primary key (month, brand_canonical)
);

create index if not exists brand_monthly_counts_month_idx
    on brand_monthly_counts (month);

-- Optional raw layer (mirror of the local SQLite sponsorship_rows). Safe to skip for v1.
create table if not exists sponsorship_rows (
    id              bigserial primary key,
    month           text not null,
    video_title     text,
    video_url       text,
    channel         text,
    brand_canonical text not null,
    brand_display   text,
    publish_date    text,
    length_seconds  integer,
    is_long_form    boolean not null,
    ingested_at     timestamptz not null default now()
);

create index if not exists sponsorship_rows_month_idx
    on sponsorship_rows (month);

-- Idempotent monthly upsert (what step 3 above runs per brand):
--   insert into brand_monthly_counts (month, brand_canonical, brand_display, sponsorship_count)
--   values ($1, $2, $3, $4)
--   on conflict (month, brand_canonical)
--   do update set brand_display = excluded.brand_display,
--                 sponsorship_count = excluded.sponsorship_count,
--                 updated_at = now();
