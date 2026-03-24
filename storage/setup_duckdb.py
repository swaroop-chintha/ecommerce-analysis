import duckdb
import os
from dotenv import load_dotenv

load_dotenv()

duckdb_path = os.getenv('WAREHOUSE_PATH', 'data/warehouse.duckdb')
raw_data_path = os.getenv('RAW_DATA_PATH', 'data/raw')

os.makedirs(os.path.dirname(duckdb_path), exist_ok=True)

def setup_duckdb():
    print(f"Connecting to DuckDB at {duckdb_path}")
    conn = duckdb.connect(duckdb_path)
    
    # Create schemas
    conn.execute("CREATE SCHEMA IF NOT EXISTS raw")
    conn.execute("CREATE SCHEMA IF NOT EXISTS staging")
    conn.execute("CREATE SCHEMA IF NOT EXISTS marts")
    
    # Load Orders
    orders_path = os.path.join(raw_data_path, 'orders', '**', '*.parquet')
    if os.path.exists(os.path.join(raw_data_path, 'orders')):
        print("Loading raw.orders")
        conn.execute("DROP TABLE IF EXISTS raw.orders")
        conn.execute(f"CREATE TABLE raw.orders AS SELECT * FROM read_parquet('{orders_path}', hive_partitioning=1)")
    
    # Load Products
    products_path = os.path.join(raw_data_path, 'products', '*.parquet')
    if os.path.exists(os.path.join(raw_data_path, 'products')):
        print("Loading raw.products")
        conn.execute("DROP TABLE IF EXISTS raw.products")
        conn.execute(f"CREATE TABLE raw.products AS SELECT * FROM read_parquet('{products_path}')")
        
    # Load Inventory
    inventory_path = os.path.join(raw_data_path, 'inventory', '*.parquet')
    if os.path.exists(os.path.join(raw_data_path, 'inventory')):
        print("Loading raw.inventory")
        conn.execute("DROP TABLE IF EXISTS raw.inventory")
        conn.execute(f"CREATE TABLE raw.inventory AS SELECT * FROM read_parquet('{inventory_path}')")
        
    # Load Events (if parquet exists, or create table)
    # The stream_ingest.py creates raw.events directly, but if we need to load from raw we could.
    # We will just ensure the table exists or report its count.
    conn.execute('''
        CREATE TABLE IF NOT EXISTS raw.events (
            event_id VARCHAR,
            session_id VARCHAR,
            user_id INTEGER,
            event_type VARCHAR,
            page VARCHAR,
            product_id INTEGER,
            device VARCHAR,
            ts VARCHAR
        )
    ''')
    # If there are JSONL fallback files that need to be loaded:
    events_jsonl = os.path.join(raw_data_path, 'events', 'events.jsonl')
    if os.path.exists(events_jsonl):
        print("Loading raw.events from fallback JSONL")
        # Load JSONL into the table (avoiding duplicates if possible, or just insert)
        conn.execute(f"INSERT INTO raw.events SELECT * FROM read_json_auto('{events_jsonl}')")
        
    print("\n--- Row Counts ---")
    tables = ['orders', 'products', 'inventory', 'events']
    for t in tables:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM raw.{t}").fetchone()[0]
            print(f"raw.{t}: {count} rows")
        except Exception as e:
            print(f"raw.{t}: Could not count ({e})")
            
    conn.close()

if __name__ == '__main__':
    setup_duckdb()
