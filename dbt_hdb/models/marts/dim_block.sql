{{ config(materialized='table') }}

with block_town as (
    select
        block,
        street_name,
        town,
        row_number() over (partition by block, street_name order by month desc) as rn
    from {{ ref('int_resale_enriched') }}
),

distinct_blocks as (
    select
        g.block,
        g.street_name,
        bt.town,
        g.latitude,
        g.longitude,
        g.coord_source,
        g.match_type,
        g.nearest_mrt_station,
        g.nearest_mrt_exit,
        g.mrt_distance_m,
        g.mrt_band,
        g.cbd_distance_km
    from {{ ref('int_block_mrt_distance') }} g
    left join (select block, street_name, town from block_town where rn = 1) bt
        on g.block = bt.block
        and g.street_name = bt.street_name
)

select * from distinct_blocks
order by town, street_name, block

