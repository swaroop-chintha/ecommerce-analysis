with events as (
    select * from "warehouse"."main"."stg_events"
),

products as (
    select * from "warehouse"."main"."dim_products"
)

select
    e.event_id,
    e.session_id,
    e.user_id,
    e.event_type,
    case
        when e.event_type = 'page_view' then 1
        when e.event_type = 'product_click' then 2
        when e.event_type = 'add_to_cart' then 3
        when e.event_type = 'checkout_start' then 4
        when e.event_type = 'purchase_complete' then 5
        when e.event_type = 'remove_from_cart' then 0
        else null
    end as funnel_step,
    e.page,
    p.product_key,
    e.product_id,
    e.device,
    e.ts
from events e
left join products p on e.product_id = p.product_id