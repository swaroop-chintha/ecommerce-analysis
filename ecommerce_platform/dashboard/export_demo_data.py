import pandas as pd
import duckdb
import os
import subprocess

def export_demo_data():
    db_path = 'data/warehouse.duckdb'
    if not os.path.exists(db_path) and os.path.exists('../data/warehouse.duckdb'):
        db_path = '../data/warehouse.duckdb'
    
    con = duckdb.connect(db_path)
    os.makedirs('data/demo', exist_ok=True)
    
    tables = [
        'mart_sales_dashboard',
        'mart_product_analytics',
        'mart_conversion_funnel',
        'mart_user_insights'
    ]
    
    success = True
    for table in tables:
        try:
            df = con.execute(f"SELECT * FROM {table}").df()
        except duckdb.CatalogException:
            print(f"Table {table} not found, running dbt run...")
            subprocess.run(["../venv/bin/dbt", "run"], cwd="dbt_project")
            try:
                df = con.execute(f"SELECT * FROM {table}").df()
            except Exception as e:
                print(f"Failed to load {table} even after dbt run: {e}")
                success = False
                continue
        
        out_path = f"data/demo/{table}.parquet"
        df.to_parquet(out_path, index=False)
        print(f"Exported {table} to {out_path}")

if __name__ == '__main__':
    export_demo_data()
