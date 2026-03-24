import duckdb
import great_expectations as ge
import os
import sys
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv('DB_PATH', 'data/ecommerce.db')

def colored_print(text, success):
    if success:
        print(f"\033[92m[PASS] {text}\033[0m")
    else:
        print(f"\033[91m[FAIL] {text}\033[0m")

def run_checks():
    print(f"Connecting to DuckDB at {DB_PATH}")
    conn = duckdb.connect(DB_PATH)
    
    try:
        orders_df = conn.execute("SELECT * FROM fact_orders").df()
        users_df = conn.execute("SELECT user_id FROM dim_users").df()
    except Exception as e:
        print(f"Error reading tables: {e}")
        sys.exit(1)
        
    conn.close()
    
    ge_orders = ge.from_pandas(orders_df)
    
    all_passed = True
    print("\n--- Running fact_orders Data Quality Checks ---")
    
    res = ge_orders.expect_column_values_to_not_be_null('order_id')
    colored_print("order_id is not null", res.success)
    all_passed = all_passed and res.success
    
    res = ge_orders.expect_column_values_to_not_be_null('user_id')
    colored_print("user_id is not null", res.success)
    all_passed = all_passed and res.success
    
    res = ge_orders.expect_column_values_to_be_between('total_amount', min_value=0.01)
    colored_print("total_amount is strictly positive (> 0)", res.success)
    all_passed = all_passed and res.success
    
    # Referential integrity
    valid_users = users_df['user_id'].tolist()
    res = ge_orders.expect_column_values_to_be_in_set('user_id', valid_users)
    colored_print("referential integrity: user_id exists in dim_users", res.success)
    all_passed = all_passed and res.success
    
    if not all_passed:
        print("\n[FAILED] Data quality checks failed!")
        sys.exit(1)
    else:
        print("\n[SUCCESS] All data quality checks passed!")
        sys.exit(0)

if __name__ == '__main__':
    run_checks()
