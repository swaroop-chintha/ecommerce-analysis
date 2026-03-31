"""
Standalone Demo Data Generator
Creates realistic parquet files directly from Python, bypassing the full pipeline.
Used for Demo Mode dashboard — no DuckDB/dbt dependencies required.
"""
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

np.random.seed(42)

# ─── Validated Indian City-State Mapping ─────────────────────────────────────
CITY_STATE_MAP = {
    'Mumbai': 'Maharashtra', 'Pune': 'Maharashtra', 'Nagpur': 'Maharashtra',
    'Delhi': 'Delhi', 'Noida': 'Uttar Pradesh', 'Gurgaon': 'Haryana',
    'Bengaluru': 'Karnataka', 'Mysuru': 'Karnataka',
    'Hyderabad': 'Telangana', 'Visakhapatnam': 'Andhra Pradesh',
    'Chennai': 'Tamil Nadu', 'Coimbatore': 'Tamil Nadu',
    'Kolkata': 'West Bengal', 'Jaipur': 'Rajasthan',
    'Ahmedabad': 'Gujarat', 'Lucknow': 'Uttar Pradesh',
    'Kochi': 'Kerala', 'Chandigarh': 'Chandigarh',
    'Indore': 'Madhya Pradesh', 'Bhopal': 'Madhya Pradesh',
}

CITY_WEIGHTS = {
    'Mumbai': 20, 'Delhi': 18, 'Bengaluru': 14, 'Hyderabad': 12, 'Chennai': 10,
    'Kolkata': 8, 'Pune': 7, 'Ahmedabad': 5, 'Jaipur': 4, 'Lucknow': 4,
    'Kochi': 3, 'Coimbatore': 3, 'Noida': 3, 'Gurgaon': 3, 'Nagpur': 2,
    'Visakhapatnam': 2, 'Indore': 2, 'Bhopal': 1.5, 'Mysuru': 1.5, 'Chandigarh': 1,
}

CATEGORIES = ['Electronics', 'Clothing', 'Home & Kitchen', 'Books', 'Sports & Fitness']
CATEGORY_WEIGHTS = np.array([35, 25, 18, 12, 10], dtype=float)
CATEGORY_WEIGHTS /= CATEGORY_WEIGHTS.sum()

CATEGORY_PRICE_RANGES = {
    'Electronics': (500, 50000),
    'Clothing': (200, 5000),
    'Home & Kitchen': (150, 15000),
    'Books': (50, 2000),
    'Sports & Fitness': (300, 10000),
}

# View-to-purchase conversion rates per category
CATEGORY_CONVERSION = {
    'Electronics': {'view_to_cart': 0.18, 'cart_to_purchase': 0.45},
    'Clothing': {'view_to_cart': 0.25, 'cart_to_purchase': 0.38},
    'Home & Kitchen': {'view_to_cart': 0.15, 'cart_to_purchase': 0.50},
    'Books': {'view_to_cart': 0.30, 'cart_to_purchase': 0.55},
    'Sports & Fitness': {'view_to_cart': 0.12, 'cart_to_purchase': 0.42},
}


def generate_sales_dashboard(n_days=365):
    """Generate daily sales data with seasonal trends and growth."""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=n_days - 1)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    records = []
    for i, date in enumerate(dates):
        # Base: gradual growth over the year
        base_orders = 80 + (i / n_days) * 180
        
        # Q4 holiday spike (Oct-Dec)
        if date.month in [10, 11, 12]:
            base_orders *= 1.8
        # Diwali week spike (around Nov 1-10)
        if date.month == 11 and date.day <= 10:
            base_orders *= 2.2
        # Weekend boost
        if date.weekday() >= 5:
            base_orders *= 1.3
        # Monday dip
        if date.weekday() == 0:
            base_orders *= 0.85
            
        # Add noise
        orders = max(20, int(base_orders + np.random.normal(0, base_orders * 0.12)))
        
        # AOV varies by season (higher during holidays due to gift buying)
        base_aov = 2800
        if date.month in [10, 11, 12]:
            base_aov = 3500
        aov = base_aov + np.random.normal(0, 300)
        
        revenue = round(orders * aov, 2)
        records.append({'date_day': date, 'total_orders': orders, 'total_revenue': revenue})
    
    return pd.DataFrame(records)


def generate_product_analytics(n_products=500):
    """Generate product-level analytics with category weighting and realistic funnels."""
    products = []
    
    for pid in range(1, n_products + 1):
        # Weighted category assignment
        category = np.random.choice(CATEGORIES, p=CATEGORY_WEIGHTS)
        price_min, price_max = CATEGORY_PRICE_RANGES[category]
        
        # Log-normal price distribution
        price = np.clip(
            np.random.lognormal(mean=np.log((price_min + price_max) / 4), sigma=0.6),
            price_min, price_max
        )
        
        # Power-law view distribution (few products have lots of views, many have few)
        views = int(np.random.pareto(a=1.5) * 200 + 50)
        views = min(views, 25000)  # Cap outliers
        
        # Category-specific conversion rates with per-product noise
        conv = CATEGORY_CONVERSION[category]
        cart_rate = conv['view_to_cart'] * np.random.uniform(0.7, 1.4)
        purchase_rate = conv['cart_to_purchase'] * np.random.uniform(0.6, 1.3)
        
        adds_to_cart = max(0, int(views * cart_rate + np.random.normal(0, 3)))
        purchases = max(0, int(adds_to_cart * purchase_rate + np.random.normal(0, 2)))
        
        # Product name: use category-relevant naming
        name_parts = {
            'Electronics': ['Pro', 'Ultra', 'Smart', 'Max', 'Nano', 'Tech', 'Digital', 'Wireless'],
            'Clothing': ['Classic', 'Premium', 'Comfort', 'Style', 'Urban', 'Casual', 'Elite'],
            'Home & Kitchen': ['Deluxe', 'Modern', 'Essential', 'Chef', 'Home', 'Compact', 'Premium'],
            'Books': ['Advanced', 'Complete', 'Essential', 'Modern', 'Practical', 'Concise'],
            'Sports & Fitness': ['Pro', 'Active', 'Endurance', 'Power', 'Flex', 'Peak', 'Elite'],
        }
        noun_parts = {
            'Electronics': ['Speaker', 'Charger', 'Headphone', 'Monitor', 'Keyboard', 'Mouse', 'Camera', 'Tablet'],
            'Clothing': ['Shirt', 'Jacket', 'Kurta', 'Jeans', 'Saree', 'T-Shirt', 'Dress', 'Hoodie'],
            'Home & Kitchen': ['Blender', 'Lamp', 'Cookware', 'Organizer', 'Cushion', 'Pan Set', 'Decor'],
            'Books': ['Guide', 'Handbook', 'Manual', 'Textbook', 'Novel', 'Reference', 'Edition'],
            'Sports & Fitness': ['Shoes', 'Mat', 'Dumbbell', 'Band', 'Tracker', 'Bottle', 'Gloves'],
        }
        
        name = np.random.choice(name_parts[category]) + ' ' + np.random.choice(noun_parts[category])
        
        products.append({
            'product_id': pid,
            'name': name,
            'category': category,
            'price': round(price, 2),
            'views': views,
            'adds_to_cart': adds_to_cart,
            'purchases': purchases,
        })
    
    return pd.DataFrame(products)


def generate_conversion_funnel():
    """Generate conversion funnel with realistic drop-off rates."""
    # Based on industry-standard e-commerce funnel benchmarks
    total_visitors = 150000
    
    stages = {
        'page_view': total_visitors,
        'product_click': int(total_visitors * 0.57),    # 57% click-through
        'add_to_cart': int(total_visitors * 0.28),       # 28% add to cart
        'checkout_start': int(total_visitors * 0.12),    # 12% start checkout
        'purchase_complete': int(total_visitors * 0.065), # 6.5% complete purchase
    }
    
    records = []
    for step, sessions in stages.items():
        # Total events slightly higher than unique sessions (some repeat actions)
        multiplier = np.random.uniform(1.1, 1.5)
        total_events = int(sessions * multiplier)
        records.append({
            'funnel_step': step,
            'unique_sessions': sessions,
            'total_events': total_events,
        })
    
    return pd.DataFrame(records)


def generate_user_insights(n_users=10000):
    """Generate user data with validated city-state pairs and correlated metrics."""
    cities = list(CITY_WEIGHTS.keys())
    weights = np.array(list(CITY_WEIGHTS.values()), dtype=float)
    weights /= weights.sum()
    
    users = []
    for uid in range(1, n_users + 1):
        city = np.random.choice(cities, p=weights)
        state = CITY_STATE_MAP[city]
        
        # Power-law order distribution: most users have few orders, few have many
        # Using a shifted Pareto to get realistic e-commerce distribution
        total_orders = max(0, int(np.random.pareto(a=1.8) * 3 + 1))
        total_orders = min(total_orders, 50)  # Cap at 50
        
        # Some users have 0 orders (browsed but never purchased)
        if np.random.random() < 0.08:
            total_orders = 0
        
        # Correlated LTV: base = orders * avg_order_value + noise
        if total_orders > 0:
            # AOV varies by "user tier"
            tier = np.random.choice(['budget', 'mid', 'premium'], p=[0.4, 0.4, 0.2])
            aov_map = {'budget': 1200, 'mid': 3500, 'premium': 8500}
            base_aov = aov_map[tier]
            aov_with_noise = base_aov * np.random.uniform(0.6, 1.5)
            ltv = total_orders * aov_with_noise
            # Add some randomness but maintain strong correlation
            ltv *= np.random.uniform(0.85, 1.15)
        else:
            ltv = 0.0
        
        users.append({
            'user_id': uid,
            'city': city,
            'state': state,
            'total_orders': total_orders,
            'lifetime_value': round(ltv, 2),
        })
    
    return pd.DataFrame(users)


def export_demo_data():
    """Generate and export all demo datasets to parquet files."""
    output_dir = 'data/demo'
    os.makedirs(output_dir, exist_ok=True)
    
    print("🚀 Generating demo data with realistic distributions...\n")
    
    # Generate all datasets
    datasets = {
        'mart_sales_dashboard': generate_sales_dashboard(),
        'mart_product_analytics': generate_product_analytics(),
        'mart_conversion_funnel': generate_conversion_funnel(),
        'mart_user_insights': generate_user_insights(),
    }
    
    for name, df in datasets.items():
        path = f"{output_dir}/{name}.parquet"
        df.to_parquet(path, index=False)
        print(f"  ✅ {name}: {df.shape[0]} rows → {path}")
    
    # Validation
    print("\n📊 Data Validation:")
    
    # 1. City-State consistency
    users = datasets['mart_user_insights']
    mismatches = users.apply(lambda r: CITY_STATE_MAP.get(r['city']) != r['state'], axis=1).sum()
    print(f"  City-State mismatches: {mismatches} (expected: 0)")
    
    # 2. LTV-Orders correlation
    active = users[users['total_orders'] > 0]
    corr = active['total_orders'].corr(active['lifetime_value'])
    print(f"  LTV-Orders correlation: {corr:.3f} (target: > 0.75)")
    
    # 3. Category distribution
    products = datasets['mart_product_analytics']
    print(f"  Category distribution:")
    for cat, count in products['category'].value_counts().items():
        print(f"    {cat}: {count} ({count/len(products)*100:.1f}%)")
    
    # 4. Funnel validation
    funnel = datasets['mart_conversion_funnel']
    vals = funnel['unique_sessions'].tolist()
    print(f"  Funnel: {' → '.join(str(v) for v in vals)}")
    print(f"  Overall conversion: {vals[-1]/vals[0]*100:.1f}%")
    
    print("\n✨ Demo data export complete!")


if __name__ == '__main__':
    export_demo_data()
