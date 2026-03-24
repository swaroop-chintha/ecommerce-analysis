with source as (
    select * from source('raw', 'users')
),
renamed as (
    select
        id as user_id,
        name,
        email,
        address,
        created_at
    from source
)
select * from renamed
