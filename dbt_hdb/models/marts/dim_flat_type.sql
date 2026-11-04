{{ config(materialized='table') }}

with distinct_flat_types as (
    select distinct flat_type
    from {{ ref('int_resale_enriched') }}
)

select
    flat_type,
    case
        when flat_type = '1 ROOM' then 1
        when flat_type = '2 ROOM' then 2
        when flat_type = '3 ROOM' then 3
        when flat_type = '4 ROOM' then 4
        when flat_type = '5 ROOM' then 5
        when flat_type = 'EXECUTIVE' then 6
        when flat_type = 'MULTI-GENERATION' then 7
        else null
    end as flat_type_rank
from distinct_flat_types
order by flat_type_rank

