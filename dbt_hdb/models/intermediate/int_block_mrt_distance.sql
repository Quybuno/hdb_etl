{{ config(materialized='table') }}

with blk as (
    select
        block,
        street_name,
        latitude,
        longitude,
        source as coord_source,
        match_type
    from {{ ref('stg_block_location') }}
    where latitude is not null and longitude is not null
),

mrt as (
    select
        station,
        exit_code,
        latitude,
        longitude
    from {{ ref('stg_mrt_exits') }}
    where latitude is not null and longitude is not null
),

cross_calc as (
    select
        b.block,
        b.street_name,
        b.latitude,
        b.longitude,
        b.coord_source,
        b.match_type,
        m.station as nearest_mrt_station,
        m.exit_code as nearest_mrt_exit,

        -- Haversine formula to nearest MRT exit (in meters)
        2.0 * 6371000.0 * asin(sqrt(
            sin(radians(m.latitude - b.latitude) / 2.0) * sin(radians(m.latitude - b.latitude) / 2.0) +
            cos(radians(b.latitude)) * cos(radians(m.latitude)) *
            sin(radians(m.longitude - b.longitude) / 2.0) * sin(radians(m.longitude - b.longitude) / 2.0)
        )) as mrt_distance_m,

        -- Haversine formula to CBD (Raffles Place MRT: 1.28393, 103.85144) (in km)
        2.0 * 6371.0 * asin(sqrt(
            sin(radians(1.28393 - b.latitude) / 2.0) * sin(radians(1.28393 - b.latitude) / 2.0) +
            cos(radians(b.latitude)) * cos(radians(1.28393)) *
            sin(radians(103.85144 - b.longitude) / 2.0) * sin(radians(103.85144 - b.longitude) / 2.0)
        )) as cbd_distance_km,

        row_number() over (
            partition by b.block, b.street_name
            order by (
                sin(radians(m.latitude - b.latitude) / 2.0) * sin(radians(m.latitude - b.latitude) / 2.0) +
                cos(radians(b.latitude)) * cos(radians(m.latitude)) *
                sin(radians(m.longitude - b.longitude) / 2.0) * sin(radians(m.longitude - b.longitude) / 2.0)
            ) asc
        ) as rank_mrt

    from blk b
    cross join mrt m
)

select
    block,
    street_name,
    latitude,
    longitude,
    coord_source,
    match_type,
    nearest_mrt_station,
    nearest_mrt_exit,
    round(mrt_distance_m, 1) as mrt_distance_m,
    round(cbd_distance_km, 2) as cbd_distance_km,
    case
        when mrt_distance_m < 400 then '< 400m'
        when mrt_distance_m < 800 then '400-799m'
        when mrt_distance_m < 1200 then '800-1199m'
        else '>= 1200m'
    end as mrt_band
from cross_calc
where rank_mrt = 1

