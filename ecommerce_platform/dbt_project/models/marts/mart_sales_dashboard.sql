{{ config(materialized='table') }}

select 
    order_date as date_day,
    count(distinct order_id) as total_orders,
    sum(order_total_amount) as total_revenue
from {{ ref('fact_orders') }}
group by 1
