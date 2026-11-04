{{ config(materialized='table') }}

with runs as (
    select
        run_id,
        run_date,
        min(loaded_at_utc) as loaded_at_utc,
        count(*) as row_count
    from raw.hdb_resale_snapshot
    group by run_id, run_date
),
ranked as (
    select
        *,
        lag(row_count) over (order by loaded_at_utc) as prev_row_count
    from runs
)
select
    run_id,
    run_date,
    loaded_at_utc,
    row_count,
    prev_row_count,
    coalesce(row_count - prev_row_count, 0) as row_delta,
    case
        when prev_row_count is null or prev_row_count = 0 then 0.0
        else round((row_count - prev_row_count) * 100.0 / prev_row_count, 2)
    end as delta_pct
from ranked

