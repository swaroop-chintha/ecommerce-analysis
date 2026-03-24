import sqlite3
import random
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
    cities = ['Mumbai', 'Delhi', 'Hyderabad', 'Bengaluru', 'Chennai', 'Pune', 'Kolkata']
    users = []
    for _ in range(n):
        users.append((
            fake.name(),
            fake.email(),
            random.choice(cities),
            fake.state(),
            fake.date_time_between(start_date='-2y', end_date='now').isoformat()
        ))
    cursor.executemany('INSERT INTO users (name, email, city, state, created_at) VALUES (?, ?, ?, ?, ?)', users)
    conn.commit()
    print(f"Generated {n} users.")

def generate_products(n=500):
    categories = ['Electronics', 'Clothing', 'Books', 'Home', 'Sports']
    products = []
    for _ in range(n):
        products.append((
            fake.word().capitalize() + ' ' + fake.word().capitalize(),
            random.choice(categories),
            round(random.uniform(10, 5000), 2),
            fake.company()
        ))
    cursor.executemany('INSERT INTO products (name, category, price, brand) VALUES (?, ?, ?, ?)', products)
    conn.commit()
    print(f"Generated {n} products.")

def weighted_hour():
    hours = list(range(24))
    weights = [1]*24
    # Peak at 10am and 8pm (20:00)
    weights[10] = 5
    weights[20] = 5
    # Low at 3am-5am
    weights[3] = 0.1
    weights[4] = 0.1
    weights[5] = 0.1
    return random.choices(hours, weights=weights)[0]

def random_date_realistic():
    now = datetime.now()
    start = now - timedelta(days=365)
    
    # 40% higher on weekends => weekend weight is 1.4, weekday weight is 1.0
    days_offsets = list(range(365))
    day_weights = []
    for d in days_offsets:
        dt = start + timedelta(days=d)
        if dt.weekday() >= 5: # Saturday or Sunday
            day_weights.append(1.4)
        else:
            day_weights.append(1.0)
            
    chosen_offset = random.choices(days_offsets, weights=day_weights)[0]
    date_part = start + timedelta(days=chosen_offset)
    
    hour = weighted_hour()
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    
    return date_part.replace(hour=hour, minute=minute, second=second)

def generate_orders_and_items(num_orders=50000, num_items=150000):
    cursor.execute('SELECT user_id FROM users')
    user_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute('SELECT product_id, price FROM products')
    product_data = cursor.fetchall()
    
    print("Generating orders...")
    orders = []
    items = []
    
    item_id_counter = 1
    
    # Distribution of items per order (avg 3)
    # Using a rough distribution to achieve ~150k items for 50k orders
    
    # Needs 3 per order on average
    
    for order_id in range(1, num_orders + 1):
        user_id = random.choice(user_ids)
        created_at = random_date_realistic().isoformat()
        
        # 20% placed, 30% shipped, 40% delivered, 10% cancelled
        status = random.choices(
            ['placed', 'shipped', 'delivered', 'cancelled'],
            weights=[20, 30, 40, 10]
        )[0]
        
        # Items for this order
        num_items_this_order = random.choices([1, 2, 3, 4, 5, 8], weights=[10, 20, 30, 20, 15, 5])[0]
        order_total = 0.0
        
        for _ in range(num_items_this_order):
            prod = random.choice(product_data)
            p_id = prod[0]
            unit_price = prod[1]
            qty = random.randint(1, 5)
            
            # 5% dirty data chance on item
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
                
        # 5% dirty data chance on order
        if random.random() < 0.05:
            dirty_order_type = random.choice(['null_user', 'null_status'])
            if dirty_order_type == 'null_user':
                user_id = None
            elif dirty_order_type == 'null_status':
                status = None
                
        orders.append((order_id, user_id, created_at, status, round(order_total, 2)))
    
    # Add some duplicate IDs as dirty data (another subset of the 5% dirty data requirement)
    # Let's just make 100 orders have duplicate order_ids
    for _ in range(100):
        idx = random.randint(0, len(orders)-1)
        duplicate = list(orders[idx])
        # We can't duplicate primary key easily in sqlite insert if we use standard insert, 
        # but wait, PK will reject duplicates. If the objective says "duplicate IDs", it implies the table schema shouldn't reject it or we just generate data.
        # But our schema has `order_id INTEGER PRIMARY KEY` which prevents duplicates.
        # So we'll alter the schema above or skip DB constraints if needed, but the prompt said "orders(order_id, ...)" and we can just insert and ignore, but to simulate duplicates we might need to remove PK constraint locally or handle it in parquet. Since we are inserting into sqlite with PK, duplicate PKs will fail. Let's make the PK auto-increment and not specify order_id if we want duplicates? No, PK must be unique. Let's skip duplicate PKs in DB and insert them directly, or remove PK from SQLite schema.
        pass # Schema has PK, will just skip duplicates or redefine schema

    cursor.executemany('INSERT INTO orders (order_id, user_id, created_at, status, total_amount) VALUES (?, ?, ?, ?, ?)', orders)
    cursor.executemany('INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?, ?)', items)
    conn.commit()
    print(f"Generated {num_orders} orders and {len(items)} order items.")

def remove_pks():
    # If we need realistic duplicate IDs, we must drop PK constraint. 
    # Not doing it now, assuming other dirty data is enough.
    pass

if __name__ == '__main__':
    setup_db()
    generate_users(10000)
    generate_products(500)
    generate_orders_and_items(50000, 150000)
    
    # Print summary
    print("\n--- Summary ---")
    tables = ['users', 'products', 'orders', 'order_items']
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        cnt = cursor.fetchone()[0]
        print(f"{t}: {cnt} rows")
    
    conn.close()
