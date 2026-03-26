with source_products as (
    select * from {{ source('raw', 'products') }}
),

source_inventory as (
    select * from {{ source('raw', 'inventory') }}
),

staged as (
    select
        cast(p.product_id as integer) as product_id,
        p.name,
        upper(substr(trim(p.category), 1, 1)) || lower(substr(trim(p.category), 2)) as category,
        cast(p.price as double) as price,
        p.brand,
        cast(i.stock as integer) as stock
    from source_products p
    left join source_inventory i on p.product_id = i.product_id
    where p.product_id is not null
)

select * from staged
