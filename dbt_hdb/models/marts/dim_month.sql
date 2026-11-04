{{ config(materialized='table') }}

with distinct_months as (
    select distinct
        month,
        transaction_year,
        transaction_month_num
    from {{ ref('int_resale_enriched') }}
)

select
    month,
    transaction_year,
    transaction_month_num,
    case
        when transaction_month_num in (1, 2, 3) then 'Q1'
        when transaction_month_num in (4, 5, 6) then 'Q2'
        when transaction_month_num in (7, 8, 9) then 'Q3'
        else 'Q4'
    end as quarter,
    concat(cast(transaction_year as varchar), '-', 
        case
            when transaction_month_num in (1, 2, 3) then 'Q1'
            when transaction_month_num in (4, 5, 6) then 'Q2'
            when transaction_month_num in (7, 8, 9) then 'Q3'
            else 'Q4'
        end
    ) as year_quarter
from distinct_months
order by month
