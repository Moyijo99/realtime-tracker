import pandas as pd
from sqlalchemy import create_engine
from clickhouse_driver import Client
import uuid

# Connect to PostgreSQL (source)
pg_engine = create_engine("postgresql+psycopg2://postgres:postgres@localhost/events")

# Read event data
print("Reading data from PostgreSQL...")
events_df = pd.read_sql("SELECT * FROM events;", pg_engine)
events_df["timestamp"] = events_df["timestamp"].dt.tz_localize(None)
print(f"Loaded {len(events_df)} events")

# Connect to ClickHouse
print("Connecting to ClickHouse...")
client = Client(host='localhost', port=9000, user='default', password='')

# Create database and table
print("Creating database and table...")
client.execute("CREATE DATABASE IF NOT EXISTS events_db")

client.execute("""
    CREATE TABLE IF NOT EXISTS events_db.events (
        event_id String,
        user_id String,
        username String,
        event_type String,
        page_url String,
        ip_address String,
        timestamp DateTime
    ) ENGINE = MergeTree()
    ORDER BY (timestamp, user_id)
""")


for col in events_df.columns:
    if events_df[col].dtype == "object":
        # If the column contains UUIDs, convert them to strings
        if len(events_df[col].dropna()) > 0 and isinstance(events_df[col].dropna().iloc[0], uuid.UUID):
            events_df[col] = events_df[col].astype(str)

print("Inserting data...")
data = events_df.values.tolist()

client.execute(
    "INSERT INTO events_db.events VALUES",
    data
)

# Verify
count = client.execute("SELECT COUNT(*) FROM events_db.events")[0][0]
print(f"✓ Successfully loaded {count} rows into ClickHouse")

# Show sample
print("\nSample data:")
result = client.execute("SELECT * FROM events_db.events LIMIT 5")
print(pd.DataFrame(result, columns=events_df.columns))

client.disconnect()