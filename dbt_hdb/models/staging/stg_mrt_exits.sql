{{ config(materialized='view') }}

select
    upper(trim(station)) as station,
    upper(trim(exit_code)) as exit_code,
    cast(latitude as double) as latitude,
    cast(longitude as double) as longitude
from raw.mrt_station_exits
where latitude is not null and longitude is not null

