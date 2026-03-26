select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

with all_values as (

    select
        event_type as value_field,
        count(*) as n_records

    from "warehouse"."main"."fact_events"
    group by event_type

)

select *
from all_values
where value_field not in (
    'page_view','product_click','add_to_cart','remove_from_cart','checkout_start','purchase_complete'
)



      
    ) dbt_internal_test