with source as (
    select * from {{ source('raw', 'orders') }}
),
renamed as (
    select
        id as order_id,
        user_id,
        created_at,
        status,
        total_amount
    from source
)
select * from renamed
