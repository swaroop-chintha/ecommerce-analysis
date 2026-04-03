
  
  create view "warehouse"."main"."stg_products__dbt_tmp" as (
    with source_products as (
    select * from sqlite_scan('../data/ecommerce.db', 'products')
),

source_inventory as (
    -- Mock inventory using sqlite products ids
    select product_id as id, 100 as stock from sqlite_scan('../data/ecommerce.db', 'products')
),

staged as (
    select
        cast(p.product_id as integer) as product_id,
        p.name,
        upper(substr(trim(p.category), 1, 1)) || lower(substr(trim(p.category), 2)) as category,
        cast(p.price as double) as price,
        'Demo Brand' as brand,
        cast(i.stock as integer) as stock
    from source_products p
    left join source_inventory i on p.product_id = i.id
    where p.product_id is not null
)

select * from staged
  );
