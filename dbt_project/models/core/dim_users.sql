with staging as (
    select * from {{ ref('stg_users') }}
)
select
    user_id,
    name,
    email,
    address,
    created_at as user_created_at
from staging
