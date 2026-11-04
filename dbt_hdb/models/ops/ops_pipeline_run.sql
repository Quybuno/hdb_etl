{{ config(materialized='table') }}

select
    run_id,
    run_date,
    min(loaded_at_utc) as loaded_at_utc,
    count(*) as total_rows_loaded
from raw.hdb_resale_snapshot
group by run_id, run_date

