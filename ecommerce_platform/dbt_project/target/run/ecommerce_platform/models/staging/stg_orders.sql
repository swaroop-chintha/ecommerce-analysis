
  
  create view "warehouse"."main"."stg_orders__dbt_tmp" as (
    with source as (
    select * from sqlite_scan('../data/ecommerce.db', 'orders')
),

staged as (
    select
        order_id,
        user_id,
        status,
        -- Need to parse the ISO string to proper timestamp if it's text
        cast(created_at as timestamp) as created_at,
        cast(total_amount as double) as total_amount
    from source
    where order_id is not null
      and user_id is not null
      and status is not null
      and total_amount > 0
)

select * from staged
  );
