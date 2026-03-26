import duckdb
import os
import pandas as pd

DB_PATH = os.getenv('DB_PATH', 'data/ecommerce.db')
DEMO_DATA_DIR = 'data/demo'

os.makedirs(DEMO_DATA_DIR, exist_ok=True)

print("Exporting mart tables to Parquet for Demo Mode...")

try:
    conn = duckdb.connect(DB_PATH, read_only=True)
    
    # Export Sales Dashboard
    sales_df = conn.execute("SELECT * FROM main.mart_sales_dashboard").df()
    sales_df.to_parquet(os.path.join(DEMO_DATA_DIR, 'mart_sales_dashboard.parquet'))
    
    # Export Conversion Funnel
    funnel_df = conn.execute("SELECT * FROM main.mart_conversion_funnel").df()
    funnel_df.to_parquet(os.path.join(DEMO_DATA_DIR, 'mart_conversion_funnel.parquet'))
    
    # Export User Insights
    users_df = conn.execute("SELECT * FROM main.mart_user_insights").df()
    users_df.to_parquet(os.path.join(DEMO_DATA_DIR, 'mart_user_insights.parquet'))
    
    # Export Top Products (Core Layer since no explicit mart exists for this view)
    prods_df = conn.execute("""
        SELECT p.product_name, p.category, sum(f.total_amount) as revenue
        FROM main.fact_orders f
        JOIN main.dim_products p ON f.product_id = p.product_id
        GROUP BY 1, 2 ORDER BY 3 DESC
    """).df()
    prods_df.to_parquet(os.path.join(DEMO_DATA_DIR, 'mart_product_analytics.parquet'))

    conn.close()
    print("Demo data exported successfully.")

except Exception as e:
    print(f"Error exporting data: {e}")
