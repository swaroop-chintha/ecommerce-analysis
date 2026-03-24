with staging as (
    select * from {{ ref('stg_products') }}
)
select
    product_id,
    name as product_name,
    category,
    price,
    created_at as product_created_at
from staging
