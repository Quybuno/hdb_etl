-- Kiểm tra miền giá trị: thời hạn thuê remaining_lease_years phải trong khoảng (0, 99]
select
    transaction_sk,
    remaining_lease_years
from {{ ref('fct_resale_transaction') }}
where remaining_lease_years <= 0 or remaining_lease_years > 99

