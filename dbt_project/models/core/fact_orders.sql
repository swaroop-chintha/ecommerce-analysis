with orders as (
    select * from {{ ref('stg_orders') }}
),
users as (
    select * from {{ ref('dim_users') }}
)
select
    o.order_id,
    o.user_id,
    o.created_at as order_created_at,
    o.status,
    o.total_amount,
    date_trunc('day', cast(o.created_at as timestamp)) as order_date
from orders o
