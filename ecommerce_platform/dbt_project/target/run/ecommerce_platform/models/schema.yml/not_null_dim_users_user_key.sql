select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select user_key
from "warehouse"."main"."dim_users"
where user_key is null



      
    ) dbt_internal_test