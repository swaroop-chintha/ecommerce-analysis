
  
  create view "warehouse"."main"."stg_events__dbt_tmp" as (
    with source as (
    select * from "warehouse"."raw"."events"
),

staged as (
    select
        event_id,
        session_id,
        cast(user_id as integer) as user_id,
        event_type,
        page,
        cast(product_id as integer) as product_id,
        device,
        try_cast(ts as timestamp) as ts
    from source
    where event_id is not null 
      and event_type in ('page_view', 'product_click', 'add_to_cart', 'remove_from_cart', 'checkout_start', 'purchase_complete')
)

select * from staged
  );
