{{ config(materialized='view') }}

with stg as (
    select * from {{ ref('stg_hdb_resale') }}
),

parsed as (
    select
        transaction_sk,
        business_hash,
        occurrence_no,
        month,
        transaction_year,
        transaction_month_num,
        town,
        flat_type,
        block,
        street_name,
        storey_range,
        floor_area_sqm,
        flat_model,
        lease_commence_year,
        remaining_lease_raw,
        resale_price,
        source_row_number,

        -- Parse remaining_lease_years
        case
            when remaining_lease_raw like '%year%' then
                coalesce(nullif(regexp_extract(remaining_lease_raw, '([0-9]+)\s*year', 1), '')::double, 0.0) +
                coalesce(nullif(regexp_extract(remaining_lease_raw, '([0-9]+)\s*month', 1), '')::double, 0.0) / 12.0
            else
                try_cast(remaining_lease_raw as double)
        end as remaining_lease_years,

        -- Parse storey_mid
        (try_cast(split_part(storey_range, ' TO ', 1) as double) +
         try_cast(split_part(storey_range, ' TO ', 2) as double)) / 2.0 as storey_mid,

        -- Flat age at time of sale
        transaction_year - lease_commence_year as flat_age,

        -- Price per square meter
        case
            when floor_area_sqm is not null and floor_area_sqm > 0
            then resale_price / floor_area_sqm
            else null
        end as price_per_sqm

    from stg
)

select
    *,
    case
        when remaining_lease_years < 50 then '<50'
        when remaining_lease_years < 55 then '50-54'
        when remaining_lease_years < 60 then '55-59'
        when remaining_lease_years < 65 then '60-64'
        when remaining_lease_years < 70 then '65-69'
        when remaining_lease_years < 75 then '70-74'
        when remaining_lease_years < 80 then '75-79'
        when remaining_lease_years < 85 then '80-84'
        when remaining_lease_years < 90 then '85-89'
        else '90+'
    end as lease_band_5yr
from parsed

