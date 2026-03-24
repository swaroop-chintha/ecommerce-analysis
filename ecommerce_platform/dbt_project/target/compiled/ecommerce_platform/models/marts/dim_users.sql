with stg_users as (
    select * from "warehouse"."main"."stg_users"
)

select
    -- surrogate key
    md5(cast(user_id as varchar) || '-' || cast(created_at as varchar)) as user_key,
    user_id,
    name,
    email,
    city,
    state,
    created_at
from stg_users