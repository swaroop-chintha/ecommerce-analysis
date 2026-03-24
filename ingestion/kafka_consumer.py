import json
import logging
import os
import duckdb
from confluent_kafka import Consumer, KafkaException
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "clickstream")
DB_PATH = os.getenv("DB_PATH", "data/ecommerce.db")
DLQ_PATH = os.getenv("DEAD_LETTER_PATH", "data/dead_letter")

os.makedirs(DLQ_PATH, exist_ok=True)
dlq_file = os.path.join(DLQ_PATH, "clickstream_dlq.jsonl")

# Connect to DuckDB and ensure table exists
conn = duckdb.connect(DB_PATH)
conn.execute("""
    CREATE TABLE IF NOT EXISTS clickstream (
        event_id VARCHAR,
        session_id VARCHAR,
        user_id INTEGER,
        event_type VARCHAR,
        page VARCHAR,
        product_id INTEGER,
        device VARCHAR,
        ts TIMESTAMP
    );
""")

# Setup Kafka Consumer
consumer = Consumer({
    'bootstrap.servers': KAFKA_BROKER,
    'group.id': 'clickstream_ingestion_group',
    'auto.offset.reset': 'earliest'
})

consumer.subscribe([KAFKA_TOPIC])

def validate_event(event):
    """Basic schema validation"""
    required_keys = ['event_id', 'session_id', 'user_id', 'event_type', 'page', 'device', 'ts']
    if not all(k in event for k in required_keys):
        return False
    # Check typing loosely
    if not isinstance(event['user_id'], int):
        return False
    return True

def write_to_dlq(raw_msg, error_msg):
    """Write malformed payload to a Dead Letter Queue"""
    with open(dlq_file, 'a') as f:
        record = {
            "error": error_msg,
            "raw_payload": raw_msg
        }
        f.write(json.dumps(record) + "\\n")
    logging.warning(f"Sent message to DLQ: {error_msg}")

logging.info(f"Starting consumer on topic {KAFKA_TOPIC} broker {KAFKA_BROKER}...")

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            logging.error(f"Consumer error: {msg.error()}")
            continue

        raw_value = msg.value().decode('utf-8')
        try:
            event = json.loads(raw_value)
            if validate_event(event):
                # Ingest to DuckDB
                conn.execute(
                    "INSERT INTO clickstream VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    [
                        event['event_id'],
                        event['session_id'],
                        event['user_id'],
                        event['event_type'],
                        event['page'],
                        event.get('product_id'), # might be None
                        event['device'],
                        event['ts']
                    ]
                )
                logging.info(f"Ingested event {event['event_id']}")
            else:
                write_to_dlq(raw_value, "Schema validation failed")
        except json.JSONDecodeError:
            write_to_dlq(raw_value, "Invalid JSON format")
        except Exception as e:
            write_to_dlq(raw_value, f"Unexpected error: {str(e)}")

except KeyboardInterrupt:
    logging.info("Shutting down consumer...")
finally:
    consumer.close()
    conn.close()
