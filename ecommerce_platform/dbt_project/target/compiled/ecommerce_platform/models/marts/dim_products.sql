with stg_products as (
    select * from "warehouse"."main"."stg_products"
)

select
    -- surrogate key
    md5(cast(product_id as varchar)) as product_key,
    product_id,
    name,
    category,
    price,
    brand,
    stock
from stg_products