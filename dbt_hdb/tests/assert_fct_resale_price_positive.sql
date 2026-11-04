-- Kiểm tra miền giá trị: giá bán lại resale_price phải lớn hơn 0
select
    transaction_sk,
    resale_price
from {{ ref('fct_resale_transaction') }}
where resale_price <= 0

