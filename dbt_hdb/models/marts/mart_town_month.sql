{{ config(materialized='table') }}

select
    town,
    month,
    transaction_year,
    transaction_month_num,
    flat_type,
    lease_band_5yr,
    count(*) as transaction_count,
    median(resale_price) as median_resale_price,
    round(avg(resale_price), 2) as avg_resale_price,
    median(price_per_sqm) as median_price_per_sqm,
    round(avg(price_per_sqm), 2) as avg_price_per_sqm,
    round(avg(remaining_lease_years), 2) as avg_remaining_lease_years,
    round(avg(floor_area_sqm), 2) as avg_floor_area_sqm
from {{ ref('fct_resale_transaction') }}
group by
    town,
    month,
    transaction_year,
    transaction_month_num,
    flat_type,
    lease_band_5yr

