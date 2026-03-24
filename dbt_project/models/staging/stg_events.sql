with source as (
    select * from {{ source('raw', 'clickstream') }}
),
renamed as (
    select
        event_id,
        session_id,
        user_id,
        event_type,
        page,
        product_id,
        device,
        ts as event_timestamp
    from source
)
select * from renamed
