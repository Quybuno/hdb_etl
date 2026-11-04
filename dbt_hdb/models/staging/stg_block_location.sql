{{ config(materialized='view') }}

select
    upper(trim(block)) as block,
    upper(trim(street_name)) as street_name,
    cast(lat as double) as latitude,
    cast(lon as double) as longitude,
    trim(source) as source,
    trim(matched_address) as matched_address,
    trim(match) as match_type
from raw.block_coordinates
where lat is not null and lon is not null
