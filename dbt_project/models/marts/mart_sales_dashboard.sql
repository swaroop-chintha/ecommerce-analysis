with fact_orders as (
    select * from {{ ref('fact_orders') }}
),
dim_date as (
    select * from {{ ref('dim_date') }}
)
select
    d.date_day,
    count(distinct f.order_id) as total_orders,
    sum(f.total_amount) as total_revenue,
    avg(f.total_amount) as average_order_value
from fact_orders f
join dim_date d on f.order_date = d.date_day
group by 1
order by 1 desc
