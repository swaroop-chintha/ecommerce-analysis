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
        
        if table == 'mart_conversion_funnel' and (df.empty or df['unique_sessions'].sum() < 1000 or (df['unique_sessions'] == 0).any()):
            print("Funnel data has very low/no volume. Injecting fallback demo data...")
            df = pd.DataFrame({
                'funnel_step': ['page_view', 'product_click', 'add_to_cart', 'checkout_start', 'purchase_complete'],
                'unique_sessions': [15000, 8500, 4200, 1800, 1200],
                'total_events': [20000, 12000, 5000, 2000, 1200]
            })
            
        if table == 'mart_product_analytics':
            if 'views' in df.columns and (df['views'].sum() < 1000 or df['adds_to_cart'].sum() < 500):
                print("Product analytics has very low views/adds volume. Synthesizing fallback data from purchases...")
                import numpy as np
                df['views'] = (df['purchases'] * np.random.randint(5, 15, size=len(df)) + np.random.randint(50, 200, size=len(df))).astype(int)
                df['adds_to_cart'] = (df['views'] * np.random.uniform(0.1, 0.4, size=len(df))).astype(int)
        
        out_path = f"data/demo/{table}.parquet"
        df.to_parquet(out_path, index=False)
        print(f"Exported {table} to {out_path}")

if __name__ == '__main__':
    export_demo_data()
