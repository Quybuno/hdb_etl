{{ config(materialized='table') }}

with max_m as (
    select max(strptime(month || '-01', '%Y-%m-%d')) as latest_date
    from {{ ref('fct_resale_transaction') }}
),

cutoff as (
    select strftime(latest_date - interval 11 month, '%Y-%m') as min_month
    from max_m
),

recent_tx as (
    select *
    from {{ ref('fct_resale_transaction') }}
    where month >= (select min_month from cutoff)
)

select
    town,
    block,
    street_name,
    flat_type,
    lease_band_5yr,
    mrt_band,
    nearest_mrt_station,
    mrt_distance_m,
    cbd_distance_km,
    block_latitude,
    block_longitude,
    count(*) as recent_transaction_count,
    min(resale_price) as min_resale_price,
    median(resale_price) as median_resale_price,
    max(resale_price) as max_resale_price,
    round(avg(resale_price), 2) as avg_resale_price,
    round(avg(remaining_lease_years), 1) as avg_remaining_lease_years,
    round(avg(floor_area_sqm), 1) as avg_floor_area_sqm,
    min(month) as earliest_month_in_window,
    max(month) as latest_month_in_window
from recent_tx
group by
    town,
    block,
    street_name,
    flat_type,
    lease_band_5yr,
    mrt_band,
    nearest_mrt_station,
    mrt_distance_m,
    cbd_distance_km,
    block_latitude,
    block_longitude

