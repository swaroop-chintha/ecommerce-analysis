import sqlite3
import random
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import os
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

db_path = os.getenv('DB_PATH', 'data/ecommerce.db')
fake = Faker('en_IN')

# Ensure directories exist
os.makedirs(os.path.dirname(db_path), exist_ok=True)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# ─── Validated Indian City-State Mapping ─────────────────────────────────────
CITY_STATE_MAP = {
    'Mumbai': 'Maharashtra',
    'Pune': 'Maharashtra',
    'Nagpur': 'Maharashtra',
    'Delhi': 'Delhi',
    'Noida': 'Uttar Pradesh',
    'Gurgaon': 'Haryana',
    'Bengaluru': 'Karnataka',
    'Mysuru': 'Karnataka',
    'Hyderabad': 'Telangana',
    'Visakhapatnam': 'Andhra Pradesh',
    'Chennai': 'Tamil Nadu',
    'Coimbatore': 'Tamil Nadu',
    'Kolkata': 'West Bengal',
    'Jaipur': 'Rajasthan',
    'Ahmedabad': 'Gujarat',
    'Lucknow': 'Uttar Pradesh',
    'Kochi': 'Kerala',
    'Chandigarh': 'Chandigarh',
    'Indore': 'Madhya Pradesh',
    'Bhopal': 'Madhya Pradesh',
}

# Population-weighted city probabilities
CITY_WEIGHTS = {
    'Mumbai': 20, 'Delhi': 18, 'Bengaluru': 14, 'Hyderabad': 12, 'Chennai': 10,
    'Kolkata': 8, 'Pune': 7, 'Ahmedabad': 5, 'Jaipur': 4, 'Lucknow': 4,
    'Kochi': 3, 'Coimbatore': 3, 'Noida': 3, 'Gurgaon': 3, 'Nagpur': 2,
    'Visakhapatnam': 2, 'Indore': 2, 'Bhopal': 1.5, 'Mysuru': 1.5, 'Chandigarh': 1,
}

CITIES = list(CITY_WEIGHTS.keys())
CITY_W = list(CITY_WEIGHTS.values())

# ─── Category Configuration ──────────────────────────────────────────────────
CATEGORIES = ['Electronics', 'Clothing', 'Home', 'Books', 'Sports']
CATEGORY_WEIGHTS = [35, 25, 18, 12, 10]

CATEGORY_PRICE_RANGES = {
    'Electronics': (500, 50000),
    'Clothing': (200, 5000),
    'Home': (150, 15000),
    'Books': (50, 2000),
    'Sports': (300, 10000),
}


def setup_db():
    cursor.executescript('''
    DROP TABLE IF EXISTS users;
    DROP TABLE IF EXISTS products;
    DROP TABLE IF EXISTS orders;
    DROP TABLE IF EXISTS order_items;
    
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        city TEXT,
        state TEXT,
        created_at TIMESTAMP
    );
    
    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY,
        name TEXT,
        category TEXT,
        price REAL,
        brand TEXT
    );
    
    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        created_at TIMESTAMP,
        status TEXT,
        total_amount REAL,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    
    CREATE TABLE order_items (
        item_id INTEGER PRIMARY KEY,
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        unit_price REAL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );
    ''')
    conn.commit()


def generate_users(n=10000):
    users = []
    for _ in range(n):
        city = random.choices(CITIES, weights=CITY_W)[0]
        state = CITY_STATE_MAP[city]
        users.append((
            fake.name(),
            fake.email(),
            city,
            state,
            fake.date_time_between(start_date='-2y', end_date='now').isoformat()
        ))
    cursor.executemany('INSERT INTO users (name, email, city, state, created_at) VALUES (?, ?, ?, ?, ?)', users)
    conn.commit()
    print(f"Generated {n} users with validated city-state pairs.")


def generate_products(n=500):
    products = []
    for _ in range(n):
        category = random.choices(CATEGORIES, weights=CATEGORY_WEIGHTS)[0]
        price_min, price_max = CATEGORY_PRICE_RANGES[category]
        raw_price = np.random.lognormal(mean=np.log((price_min + price_max) / 4), sigma=0.6)
        price = max(price_min, min(price_max, round(raw_price, 2)))
        products.append((
            fake.word().capitalize() + ' ' + fake.word().capitalize(),
            category,
            price,
            fake.company()
        ))
    cursor.executemany('INSERT INTO products (name, category, price, brand) VALUES (?, ?, ?, ?)', products)
    conn.commit()
    print(f"Generated {n} products with weighted categories.")


def weighted_hour():
    hours = list(range(24))
    weights = [1]*24
    weights[10] = 5
    weights[20] = 5
    weights[3] = 0.1
    weights[4] = 0.1
    weights[5] = 0.1
    return random.choices(hours, weights=weights)[0]


def random_date_realistic():
    now = datetime.now()
    start = now - timedelta(days=365)
    
    days_offsets = list(range(365))
    day_weights = []
    for d in days_offsets:
        dt = start + timedelta(days=d)
        weight = 1.0 + (d / 365.0) * 2.0
        if dt.month in [10, 11, 12]:
            weight *= 2.5
        if dt.weekday() >= 5:
            weight *= 1.5
        day_weights.append(weight)
            
    chosen_offset = random.choices(days_offsets, weights=day_weights)[0]
    date_part = start + timedelta(days=chosen_offset)
    
    hour = weighted_hour()
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    
    return date_part.replace(hour=hour, minute=minute, second=second)


def generate_orders_and_items(num_orders=50000, num_items=150000):
    cursor.execute('SELECT user_id FROM users')
    user_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute('SELECT product_id, price, category FROM products')
    product_data = cursor.fetchall()
    
    products_by_cat = {}
    for pid, price, cat in product_data:
        products_by_cat.setdefault(cat, []).append((pid, price))
    
    print("Generating orders...")
    orders = []
    items = []
    
    item_id_counter = 1
    
    for order_id in range(1, num_orders + 1):
        user_id = random.choice(user_ids)
        created_at = random_date_realistic().isoformat()
        
        status = random.choices(
            ['placed', 'shipped', 'delivered', 'cancelled'],
            weights=[20, 30, 40, 10]
        )[0]
        
        num_items_this_order = random.choices([1, 2, 3, 4, 5, 8], weights=[10, 20, 30, 20, 15, 5])[0]
        order_total = 0.0
        
        for _ in range(num_items_this_order):
            cat = random.choices(CATEGORIES, weights=CATEGORY_WEIGHTS)[0]
            if cat in products_by_cat and products_by_cat[cat]:
                prod = random.choice(products_by_cat[cat])
            else:
                prod = random.choice([(p[0], p[1]) for p in product_data])
            p_id = prod[0]
            unit_price = prod[1]
            qty = random.randint(1, 5)
            
            if random.random() < 0.05:
                dirty_type = random.choice(['null_price', 'negative_price'])
                if dirty_type == 'null_price':
                    unit_price = None
                elif dirty_type == 'negative_price':
                    unit_price = -abs(unit_price)
            
            items.append((item_id_counter, order_id, p_id, qty, unit_price))
            item_id_counter += 1
            if unit_price is not None and unit_price > 0:
                order_total += unit_price * qty
                
        if random.random() < 0.05:
            dirty_order_type = random.choice(['null_user', 'null_status'])
            if dirty_order_type == 'null_user':
                user_id = None
            elif dirty_order_type == 'null_status':
                status = None
                
        orders.append((order_id, user_id, created_at, status, round(order_total, 2)))
    
    cursor.executemany('INSERT INTO orders (order_id, user_id, created_at, status, total_amount) VALUES (?, ?, ?, ?, ?)', orders)
    cursor.executemany('INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?, ?)', items)
    conn.commit()
    print(f"Generated {num_orders} orders and {len(items)} order items.")


if __name__ == '__main__':
    setup_db()
    generate_users(10000)
    generate_products(500)
    generate_orders_and_items(50000, 150000)
    
    print("\n--- Summary ---")
    tables = ['users', 'products', 'orders', 'order_items']
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        cnt = cursor.fetchone()[0]
        print(f"{t}: {cnt} rows")
    
    cursor.execute("SELECT DISTINCT city, state FROM users")
    pairs = cursor.fetchall()
    print(f"\nCity-State pairs ({len(pairs)} unique):")
    for city, state in sorted(pairs):
        expected = CITY_STATE_MAP.get(city, 'UNKNOWN')
        status = "✅" if state == expected else "❌"
        print(f"  {status} {city} → {state}")
    
    conn.close()
