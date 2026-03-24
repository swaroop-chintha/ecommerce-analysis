with source as (
    select * from {{ source('raw', 'products') }}
),
renamed as (
    select
        id as product_id,
        name,
        category,
        price,
        created_at
    from source
)
select * from renamed
