

select 
    funnel_step,
    event_type,
    count(distinct session_id) as unique_sessions,
    count(event_id) as total_events
from "warehouse"."main"."fact_events"
where event_type in ('page_view', 'product_click', 'add_to_cart', 'checkout_start', 'purchase_complete')
group by 1, 2