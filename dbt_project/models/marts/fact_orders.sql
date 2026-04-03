with orders as (
    select * from {{ ref('stg_orders') }}
),

order_items as (
    select * from sqlite_scan('{{ env_var("DB_PATH", "../data/ecommerce.db") }}', 'order_items')
),

users as (
    select * from {{ ref('dim_users') }}
),

products as (
    select * from {{ ref('dim_products') }}
)

select
    cast(i.item_id as integer) as item_id,
    o.order_id,
    u.user_key,
    p.product_key,
    cast(o.created_at as date) as order_date,
    o.created_at as order_timestamp,
    o.status,
    cast(i.quantity as integer) as quantity,
    cast(i.unit_price as double) as unit_price,
    cast(i.quantity * i.unit_price as double) as item_revenue,
    o.total_amount as order_total_amount
from orders o
join order_items i on o.order_id = i.order_id
left join users u on o.user_id = u.user_id
left join products p on i.product_id = p.product_id
