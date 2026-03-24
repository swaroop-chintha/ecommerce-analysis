import json
import duckdb
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

duckdb_path = os.getenv('WAREHOUSE_PATH', 'data/warehouse.duckdb')
dead_letter_path = os.getenv('DEAD_LETTER_PATH', 'data/dead_letter') + '/events'
raw_data_path = os.getenv('RAW_DATA_PATH', 'data/raw')
kafka_broker = os.getenv('KAFKA_BROKER', 'localhost:9092')
topic = os.getenv('KAFKA_TOPIC', 'clickstream')

os.makedirs(dead_letter_path, exist_ok=True)
os.makedirs(os.path.dirname(duckdb_path), exist_ok=True)

# Connect & init DuckDB
conn = duckdb.connect(duckdb_path)
conn.execute('CREATE SCHEMA IF NOT EXISTS raw')
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

required_keys = {'event_id', 'session_id', 'user_id', 'event_type', 'ts'}

def validate_and_insert(record_str):
    try:
        record = json.loads(record_str)
        # Check required fields
        if not required_keys.issubset(record.keys()) or not all(record[k] for k in required_keys):
            raise ValueError("Missing required fields")
            
        # Insert
        conn.execute('''
        INSERT INTO raw.events
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record.get('event_id'),
            record.get('session_id'),
            record.get('user_id'),
            record.get('event_type'),
            record.get('page'),
            record.get('product_id'),
            record.get('device'),
            record.get('ts')
        ))
        return True
    except Exception as e:
        # Write to dead letter
        dl_file = os.path.join(dead_letter_path, f"{datetime.now().strftime('%Y%m%d')}_rejected.jsonl")
        with open(dl_file, 'a') as f:
            f.write(record_str.strip() + '\n')
        return False

def consume_stream():
    count = 0
    try:
        from confluent_kafka import Consumer
        c = Consumer({
            'bootstrap.servers': kafka_broker,
            'group.id': 'duckdb_ingest',
            'auto.offset.reset': 'earliest'
        })
        c.subscribe([topic])
        print("Connected to Kafka. Consuming...")
        
        while True:
            msg = c.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue
                
            val = msg.value().decode('utf-8')
            if validate_and_insert(val):
                count += 1
                if count % 100 == 0:
                    print(f"Ingested {count} events...")
    except ImportError:
        print("confluent_kafka not installed, trying fallback")
    except Exception as e:
        print(f"Kafka error: {e}. Falling back to events.jsonl")
        fallback_file = os.path.join(raw_data_path, 'events', 'events.jsonl')
        if not os.path.exists(fallback_file):
            print("No fallback file found.")
            return
            
        # Tail the file
        with open(fallback_file, 'r') as f:
            for line in f:
                if validate_and_insert(line):
                    count += 1
                    if count % 100 == 0:
                        print(f"Ingested {count} events from fallback...")

if __name__ == '__main__':
    consume_stream()
