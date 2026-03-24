import sqlite3
import pandas as pd
import httpx
import os
from datetime import datetime
from dotenv import load_dotenv
import pyarrow as pa
import pyarrow.parquet as pq

load_dotenv()

db_path = os.getenv('DB_PATH', 'data/ecommerce.db')
raw_data_path = os.getenv('RAW_DATA_PATH', 'data/raw')
dead_letter_path = os.getenv('DEAD_LETTER_PATH', 'data/dead_letter')
api_url = f"http://localhost:{os.getenv('MOCK_API_PORT', '8001')}"

def setup_dirs():
    os.makedirs(raw_data_path, exist_ok=True)
    os.makedirs(dead_letter_path, exist_ok=True)

def reject_invalid_rows(df, required_cols, run_date_str):
    """
    Returns valid_df, rejected_df
    """
    if df.empty:
        return df, pd.DataFrame()
        
    mask = df[required_cols].notnull().all(axis=1)
    valid_df = df[mask]
    rejected_df = df[~mask]
    
    if not rejected_df.empty:
        dl_file = os.path.join(dead_letter_path, f"{run_date_str}_rejected.parquet")
        # Ensure directory exists if needed
        os.makedirs(os.path.dirname(dl_file), exist_ok=True)
        
        # Append or write newly rejected rows
        if os.path.exists(dl_file):
            existing = pd.read_parquet(dl_file)
            combined = pd.concat([existing, rejected_df])
            combined.to_parquet(dl_file, index=False)
        else:
            rejected_df.to_parquet(dl_file, index=False)
            
    return valid_df, rejected_df

def ingest_orders(run_date_str):
    print("Ingesting orders from SQLite...")
    conn = sqlite3.connect(db_path)
    
    # Read orders
    orders_df = pd.read_sql_query("SELECT * FROM orders", conn)
    
    # Validate
    required_cols = ['order_id', 'user_id', 'status']
    valid_orders, rejected = reject_invalid_rows(orders_df, required_cols, run_date_str)
    
    conn.close()
    
    if not valid_orders.empty:
        # Extract year, month for partitioning
        valid_orders['created_at'] = pd.to_datetime(valid_orders['created_at'])
        valid_orders['year'] = valid_orders['created_at'].dt.year.astype(str)
        # zero-pad month
        valid_orders['month'] = valid_orders['created_at'].dt.month.astype(str).str.zfill(2)
        
        table = pa.Table.from_pandas(valid_orders)
        pq.write_to_dataset(
            table,
            root_path=os.path.join(raw_data_path, 'orders'),
            partition_cols=['year', 'month']
        )
        
    print(f"Orders -> Ingested: {len(valid_orders)}, Rejected: {len(rejected)}, Path: {os.path.join(raw_data_path, 'orders')}")

def ingest_products_and_inventory(run_date_str):
    print("Ingesting products and inventory from Mock API...")
    
    # Products
    try:
        all_products = []
        page = 1
        while True:
            response = httpx.get(f"{api_url}/products?page={page}&size=100")
            response.raise_for_status()
            data = response.json()
            if not data:
                break
            all_products.extend(data)
            page += 1
            
        products_df = pd.DataFrame(all_products)
        
        valid_products, rejected_products = reject_invalid_rows(products_df, ['product_id', 'name', 'price'], run_date_str)
        if not valid_products.empty:
            out_path = os.path.join(raw_data_path, 'products')
            os.makedirs(out_path, exist_ok=True)
            valid_products.to_parquet(os.path.join(out_path, 'products.parquet'), index=False)
        print(f"Products -> Ingested: {len(valid_products)}, Rejected: {len(rejected_products)}, Path: {os.path.join(raw_data_path, 'products/products.parquet')}")
    except Exception as e:
        print(f"Error fetching products: {e}")

    # Inventory
    try:
        response = httpx.get(f"{api_url}/inventory")
        response.raise_for_status()
        inventory_data = response.json()
        inventory_df = pd.DataFrame(inventory_data)
        
        valid_inv, rejected_inv = reject_invalid_rows(inventory_df, ['product_id', 'stock'], run_date_str)
        if not valid_inv.empty:
            out_path = os.path.join(raw_data_path, 'inventory')
            os.makedirs(out_path, exist_ok=True)
            valid_inv.to_parquet(os.path.join(out_path, f"{run_date_str}_inventory.parquet"), index=False)
        print(f"Inventory -> Ingested: {len(valid_inv)}, Rejected: {len(rejected_inv)}, Path: {os.path.join(raw_data_path, f'inventory/{run_date_str}_inventory.parquet')}")
    except Exception as e:
        print(f"Error fetching inventory: {e}")

if __name__ == "__main__":
    setup_dirs()
    run_date_str = datetime.now().strftime("%Y%m%d")
    ingest_orders(run_date_str)
    ingest_products_and_inventory(run_date_str)
    print("Batch ingestion completed.")
