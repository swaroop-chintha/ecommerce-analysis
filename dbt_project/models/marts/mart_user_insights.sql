with user_orders as (
    select
        user_id,
        count(order_id) as total_orders,
        sum(total_amount) as lifetime_value,
        min(order_date) as first_order_date,
        max(order_date) as last_order_date
    from {{ ref('fact_orders') }}
    group by 1
)
select
    u.user_id,
    u.name,
    uo.total_orders,
    uo.lifetime_value,
    case
        when uo.total_orders > 1 then 'Repeat'
        else 'New'
    end as user_segment,
    uo.first_order_date,
    uo.last_order_date
from {{ ref('dim_users') }} u
join user_orders uo on u.user_id = uo.user_id
