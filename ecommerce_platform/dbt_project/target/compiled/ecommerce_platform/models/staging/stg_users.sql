with source as (
    -- Users were generated in SQLite directly, but not ingested into raw! 
    -- wait, the instructions: stg_users.sql - clean nulls, standardize city names
    -- but batch_ingest.py didn't ingest users!
    -- Let's extract users from sqlite here using dbt-duckdb sqlite extension or just read directly from the sqlite file.
    select * from sqlite_scan('../data/ecommerce.db', 'users')
),

staged as (
    select
        cast(user_id as integer) as user_id,
        name,
        email,
        trim(city) as city,
        state,
        cast(created_at as timestamp) as created_at
    from source
    where user_id is not null
)

select * from staged