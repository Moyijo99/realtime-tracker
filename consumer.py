from urllib.parse import urlparse
from kafka import KafkaConsumer
import psycopg2
import json

# Initialize Kafka consumer
consumer = KafkaConsumer(
    "events",
    bootstrap_servers="localhost:9092",
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    group_id="event-consumers"
)

# Connect to Postgres
conn = psycopg2.connect(
    dbname="airflow",
    user="airflow",
    password="airflow",
    host="postgres",
    port="5432"
)
cursor = conn.cursor()

# Create table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS events (
    event_id UUID PRIMARY KEY,
    user_id UUID,
    username TEXT,
    event_type TEXT,
    page_url TEXT,
    ip_address TEXT,
    timestamp TIMESTAMPTZ
)
""")
conn.commit()

def is_valid_event(event):
    """Check for missing or malformed fields."""
    required_fields = [
        "event_id", "user_id", "username",
        "event_type", "page_url", "ip_address", "timestamp"
    ]
    
    # All required fields must be present and non-empty
    for field in required_fields:
        if field not in event or event[field] in (None, "", "null"):
            print(f"Invalid event - missing {field}")
            return False

    # Optional: type checks
    if event["event_type"] not in ["page_view", "click", "form_submit"]:
        print(f"Invalid event type: {event['event_type']}")
        return False

    return True


def clean_event(event):
    """Clean and normalize event data."""
    event["username"] = event["username"].strip().lower()

    # Ensure page_url has a leading slash
    if not event["page_url"].startswith("/"):
        parsed = urlparse(event["page_url"])
        event["page_url"] = parsed.path or f"/{event['page_url']}"

    return event


print("Listening for events and inserting into Postgres...")

for message in consumer:
    event = message.value
    event = clean_event(event)


    if not is_valid_event(event):
        continue  # Skip invalid events

    try:
        cursor.execute("""
            INSERT INTO events (event_id, user_id, username, event_type, page_url, ip_address, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (event_id) DO NOTHING;
        """, (
            event["event_id"],
            event["user_id"],
            event["username"],
            event["event_type"],
            event["page_url"],
            event["ip_address"],
            event["timestamp"]
        ))
        conn.commit()
        print(f"Inserted event: {event['event_id']}")
    except Exception as e:
        print(f"Error inserting event: {e}")
        conn.rollback()