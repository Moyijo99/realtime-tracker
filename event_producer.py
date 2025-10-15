import json
from kafka import KafkaProducer
import time
import uuid
from datetime import datetime, timezone
from faker import Faker
import psycopg2
import random

fake = Faker()

EVENT_TYPES = ["page_view", "click", "form_submit"]

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def generate_event():
    return {
        "event_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "username": fake.user_name(),
        "event_type": random.choice(EVENT_TYPES),
        "page_url": fake.uri_path(),
        "ip_address": fake.ipv4(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def produce_events():
    while True:
        event = generate_event()
        producer.send("events", value=event)
        print(f"Sent event: {event}")
        producer.flush()
        time.sleep(random.uniform(0.5, 2))


if __name__ == "__main__":
    produce_events()