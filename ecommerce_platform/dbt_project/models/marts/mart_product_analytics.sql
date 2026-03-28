{{ config(materialized='table') }}

with events as (
    select
        product_key,
        count(distinct case when event_type = 'page_view' then event_id end) as views,
        count(distinct case when event_type = 'add_to_cart' then event_id end) as adds_to_cart
    from {{ ref('fact_events') }}
    group by 1
),

orders as (
    select
        product_key,
        sum(quantity) as purchases
    from {{ ref('fact_orders') }}
    group by 1
)

select 
    p.product_id,
    p.name,
    p.category,
    coalesce(e.views, 0) as views,
    coalesce(e.adds_to_cart, 0) as adds_to_cart,
    coalesce(o.purchases, 0) as purchases
from {{ ref('dim_products') }} p
left join events e on p.product_key = e.product_key
left join orders o on p.product_key = o.product_key
