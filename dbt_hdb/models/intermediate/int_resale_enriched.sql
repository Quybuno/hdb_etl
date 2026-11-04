{{ config(materialized='view') }}

with resale as (
    select * from {{ ref('int_resale_parsed') }}
),

geo as (
    select * from {{ ref('int_block_mrt_distance') }}
)

select
    r.*,
    g.latitude as block_latitude,
    g.longitude as block_longitude,
    g.coord_source,
    g.match_type,
    g.nearest_mrt_station,
    g.nearest_mrt_exit,
    g.mrt_distance_m,
    g.mrt_band,
    g.cbd_distance_km
from resale r
left join geo g
    on r.block = g.block
    and r.street_name = g.street_name
