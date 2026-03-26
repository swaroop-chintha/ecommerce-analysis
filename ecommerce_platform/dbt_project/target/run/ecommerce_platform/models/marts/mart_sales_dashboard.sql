
  
    
    

    create  table
      "warehouse"."main"."mart_sales_dashboard__dbt_tmp"
  
    as (
      

select 
    order_date as date_day,
    count(distinct order_id) as total_orders,
    sum(order_total_amount) as total_revenue
from "warehouse"."main"."fact_orders"
group by 1
    );
  
  