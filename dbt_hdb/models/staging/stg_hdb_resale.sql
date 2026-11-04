{{ config(materialized='view') }}

with latest_snapshot as (
    select run_id
    from raw.hdb_resale_snapshot
    order by loaded_at_utc desc
    limit 1
),

raw_trimmed as (
    select
        s.*,
        sha256(concat_ws('||',
            trim(s.month),
            trim(s.town),
            trim(s.flat_type),
            trim(s.block),
            trim(s.street_name),
            trim(s.storey_range),
            trim(s.floor_area_sqm),
            trim(s.flat_model),
            trim(s.lease_commence_date),
            trim(s.remaining_lease),
            trim(s.resale_price)
        )) as business_hash,
        row_number() over (
            partition by concat_ws('||',
                trim(s.month),
                trim(s.town),
                trim(s.flat_type),
                trim(s.block),
                trim(s.street_name),
                trim(s.storey_range),
                trim(s.floor_area_sqm),
                trim(s.flat_model),
                trim(s.lease_commence_date),
                trim(s.remaining_lease),
                trim(s.resale_price)
            )
            order by s.source_row_number
        ) as occurrence_no
    from raw.hdb_resale_snapshot s
    where s.run_id = (select run_id from latest_snapshot)
)

select
    sha256(concat_ws('||', business_hash, cast(occurrence_no as varchar))) as transaction_sk,
    business_hash,
    occurrence_no,
    trim(month) as month,
    cast(substring(trim(month), 1, 4) as integer) as transaction_year,
    cast(substring(trim(month), 6, 2) as integer) as transaction_month_num,
    upper(trim(town)) as town,
    upper(trim(flat_type)) as flat_type,
    upper(trim(block)) as block,
    upper(trim(street_name)) as street_name,
    trim(storey_range) as storey_range,
    try_cast(trim(floor_area_sqm) as double) as floor_area_sqm,
    trim(flat_model) as flat_model,
    try_cast(trim(lease_commence_date) as integer) as lease_commence_year,
    trim(remaining_lease) as remaining_lease_raw,
    try_cast(trim(resale_price) as double) as resale_price,
    source_row_number
from raw_trimmed

