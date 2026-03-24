with events as (
    select * from {{ ref('stg_events') }}
),
session_aggregates as (
    select
        page,
        event_type,
        count(event_id) as total_events,
        count(distinct session_id) as unique_sessions,
        count(distinct user_id) as unique_users
    from events
    group by 1, 2
)
select
    s.*,
    (select count(distinct session_id) from events where event_type = 'purchase_complete') * 100.0 / nullif((select count(distinct session_id) from events where event_type = 'page_view'), 0) as overall_conversion_rate
from session_aggregates s
order by unique_sessions desc
