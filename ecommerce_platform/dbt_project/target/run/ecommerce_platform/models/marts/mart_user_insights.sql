
  
    
    

    create  table
      "warehouse"."main"."mart_user_insights__dbt_tmp"
  
    as (
      

select 
    u.user_id,
    u.city,
    u.state,
    count(distinct o.order_id) as total_orders,
    sum(o.order_total_amount) as lifetime_value
from "warehouse"."main"."dim_users" u
left join "warehouse"."main"."fact_orders" o on u.user_key = o.user_key
group by 1, 2, 3
    );
  
  