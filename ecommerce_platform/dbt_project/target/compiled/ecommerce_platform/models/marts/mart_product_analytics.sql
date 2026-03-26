

select 
    p.product_id,
    p.name,
    p.category,
    count(distinct case when e.event_type = 'page_view' then e.event_id end) as views,
    count(distinct case when e.event_type = 'add_to_cart' then e.event_id end) as adds_to_cart,
    count(distinct case when e.event_type = 'purchase_complete' then e.event_id end) as purchases
from "warehouse"."main"."dim_products" p
left join "warehouse"."main"."fact_events" e on p.product_key = e.product_key
group by 1, 2, 3