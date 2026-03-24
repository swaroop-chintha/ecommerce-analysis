with raw_dates as (
    -- Simple date dimension generation since 2020 
    -- DuckDB specific syntax
    select 
        date_trunc('day', cast('2020-01-01' as timestamp) + interval (unnest(range(0, 3650))) day) as date_day
)
select
    date_day,
    extract(year from date_day) as year,
    extract(month from date_day) as month,
    extract(day from date_day) as day,
    extract(isodow from date_day) as day_of_week
from raw_dates
