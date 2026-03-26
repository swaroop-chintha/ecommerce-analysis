{{ config(materialized='table') }}

select 
    u.user_id,
    u.city,
    u.state,
    count(distinct o.order_id) as total_orders,
    sum(o.order_total_amount) as lifetime_value
from {{ ref('dim_users') }} u
left join {{ ref('fact_orders') }} o on u.user_key = o.user_key
group by 1, 2, 3
