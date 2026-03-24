from fastapi import FastAPI, HTTPException, Query
import sqlite3
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
db_path = os.getenv('DB_PATH', 'data/ecommerce.db')

app = FastAPI()

# In-memory inventory
inventory_store = {}

def get_db():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.on_event("startup")
async def startup_event():
    # Initialize inventory
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT product_id FROM products")
        products = cursor.fetchall()
        for p in products:
            import random
            inventory_store[p['product_id']] = random.randint(0, 500)
        conn.close()
    except Exception as e:
        print(f"Could not load products for inventory init: {e}")

    # Background task for inventory refresh
    async def refresh_inventory():
        while True:
            await asyncio.sleep(60)
            import random
            for product_id in inventory_store.keys():
                # Randomly adjust stock
                change = random.randint(-10, 20)
                inventory_store[product_id] = max(0, min(500, inventory_store[product_id] + change))
            print("Inventory refreshed in background.")

    asyncio.create_task(refresh_inventory())

@app.get("/products")
def get_products(page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=100)):
    conn = get_db()
    cursor = conn.cursor()
    offset = (page - 1) * size
    cursor.execute("SELECT * FROM products LIMIT ? OFFSET ?", (size, offset))
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return products

@app.get("/products/{product_id}")
def get_product(product_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return dict(product)

@app.get("/inventory")
def get_inventory():
    return [{"product_id": k, "stock": v} for k, v in inventory_store.items()]

@app.get("/health")
def health_check():
    return {"status": "ok"}
