-- Kiểm tra miền giá trị: diện tích sàn floor_area_sqm phải lớn hơn 0
select
    transaction_sk,
    floor_area_sqm
from {{ ref('fct_resale_transaction') }}
where floor_area_sqm <= 0

