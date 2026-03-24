import json
import time
import random
import uuid
from datetime import datetime
import os
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic
from dotenv import load_dotenv

load_dotenv()

topic = os.getenv('KAFKA_TOPIC', 'clickstream')
broker = os.getenv('KAFKA_BROKER', 'localhost:9092')
fallback_path = os.getenv('RAW_DATA_PATH', 'data/raw') + '/events/events.jsonl'

os.makedirs(os.path.dirname(fallback_path), exist_ok=True)

try:
    producer = Producer({'bootstrap.servers': broker})
    # Attempt to deliver a test message to see if kafka is up
    # We will just use the producer to send in the loop
    kafka_available = True
except Exception as e:
    print(f"Kafka not available: {e}. Using fallback.")
    kafka_available = False

def delivery_report(err, msg):
    if err is not None:
        pass

def generate_session(user_id=None):
    if user_id is None:
        user_id = random.randint(1, 10000)
        
    session_id = str(uuid.uuid4())
    device = random.choice(['mobile', 'desktop', 'tablet'])
    
    # Realistic funnel sequence
    # 1. page_view (home)
    # 2. product_click
    # 3. page_view (product detail)
    # 4. add_to_cart
    # 5. checkout_start
    # 6. purchase_complete
    
    funnel = [
        ('page_view', 'home', None),
        ('product_click', 'home', random.randint(1, 500)),
        ('page_view', 'product_detail', None) # We'll fill product_id later
    ]
    
    # Decisions to drop off
    if random.random() > 0.3:
        funnel.append(('add_to_cart', 'product_detail', None))
        if random.random() > 0.4:
            funnel.append(('checkout_start', 'checkout', None))
            if random.random() > 0.2:
                funnel.append(('purchase_complete', 'checkout', None))
            else:
                if random.random() > 0.5:
                    funnel.append(('remove_from_cart', 'cart', None))

    events = []
    current_product = funnel[1][2]
    
    for event_type, page, prod_id in funnel:
        if prod_id is None and event_type != 'page_view' or page == 'product_detail' or event_type in ['add_to_cart', 'checkout_start', 'purchase_complete', 'remove_from_cart']:
            prod_id = current_product
        elif page == 'home' and event_type == 'page_view':
            prod_id = None
            
        events.append({
            'event_id': str(uuid.uuid4()),
            'session_id': session_id,
            'user_id': user_id,
            'event_type': event_type,
            'page': page,
            'product_id': prod_id,
            'device': device,
            'ts': datetime.now().isoformat()
        })
    return events

if __name__ == '__main__':
    print("Starting event generation...")
    # Because session logic dictates a sequence, and we want 1 event / 0.5s overall
    # We can keep a queue of active sessions or just emit one session's events over time.
    # To keep it simple, we'll queue events from sessions and yield them.
    event_queue = []
    
    count = 0
    while True:
        if not event_queue:
            # Generate a few sessions
            for _ in range(3):
                event_queue.extend(generate_session())
            # Sort by slightly jittered timestamps or keep sequential
            
        event = event_queue.pop(0)
        # update 'ts' to now
        event['ts'] = datetime.now().isoformat()
        
        event_json = json.dumps(event)
        
        if kafka_available:
            try:
                producer.produce(topic, event_json.encode('utf-8'), callback=delivery_report)
                producer.poll(0)
            except Exception as e:
                # Write to fallback
                with open(fallback_path, 'a') as f:
                    f.write(event_json + '\n')
        else:
            with open(fallback_path, 'a') as f:
                f.write(event_json + '\n')
                
        count += 1
        if count % 100 == 0:
            print(f"Generated {count} events...")
            
        # Increased sleep to 3.0s to prevent Mac overheating during continuous streaming
        time.sleep(3.0)
