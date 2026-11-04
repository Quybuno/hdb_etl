{{ config(materialized='table') }}

with max_m as (
    select max(month) as latest_source_month
    from {{ ref('fct_resale_transaction') }}
)
select
    latest_source_month,
    current_date as check_date,
    date_diff('month', strptime(latest_source_month || '-01', '%Y-%m-%d'), current_date) as lag_calendar_months,
    case
        when date_diff('month', strptime(latest_source_month || '-01', '%Y-%m-%d'), current_date) <= 2
        then 'FRESH'
        else 'STALE_WARNING'
    end as freshness_status
from max_m
