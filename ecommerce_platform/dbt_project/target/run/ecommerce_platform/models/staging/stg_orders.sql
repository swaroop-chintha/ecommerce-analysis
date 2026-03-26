
  
  create view "warehouse"."main"."stg_orders__dbt_tmp" as (
    with source as (
    select * from "warehouse"."raw"."orders"
),

staged as (
    select distinct
        cast(order_id as integer) as order_id,
        cast(user_id as integer) as user_id,
        cast(created_at as timestamp) as created_at,
        lower(trim(status)) as status,
        cast(total_amount as double) as total_amount
    from source
    where order_id is not null
      and user_id is not null
      and status is not null
      and total_amount > 0
)

select * from staged
  );
