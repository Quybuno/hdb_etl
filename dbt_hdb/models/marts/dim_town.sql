{{ config(materialized='table') }}

with distinct_towns as (
    select distinct town
    from {{ ref('int_resale_enriched') }}
)

select
    town,
    case
        when town in (
            'ANG MO KIO', 'BEDOK', 'BISHAN', 'BUKIT MERAH', 'BUKIT TIMAH',
            'CENTRAL AREA', 'CLEMENTI', 'GEYLANG', 'KALLANG/WHAMPOA',
            'MARINE PARADE', 'PASIR RIS', 'QUEENSTOWN', 'SERANGOON',
            'TAMPINES', 'TOA PAYOH'
        ) then 'Mature'
        else 'Non-Mature'
    end as estate_type
from distinct_towns
order by town
