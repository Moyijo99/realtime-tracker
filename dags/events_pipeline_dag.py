"""
Events Analytics Pipeline DAG - Complete Automation
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine
from clickhouse_driver import Client
import logging
import os

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 10, 10),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'events_analytics_pipeline',
    default_args=default_args,
    description='Automated ETL pipeline for events analytics',
    schedule_interval='0 * * * *',
    catchup=False,
    tags=['analytics', 'events', 'clickhouse', 'dbt'],
)

def setup_clickhouse_schema(**context):
    """Create ClickHouse database and table schema"""
    logger = logging.getLogger(__name__)
    
    logger.info("Connecting to ClickHouse...")
    client = Client(host='clickhouse', port=9000, user='default', password='')
    
    logger.info("Creating database...")
    client.execute("CREATE DATABASE IF NOT EXISTS events_db")
    
    logger.info("Creating raw events table...")
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
        SETTINGS index_granularity = 8192
    """)
    
    logger.info("✓ ClickHouse schema setup complete")
    client.disconnect()

def extract_and_load_to_clickhouse(**context):
    """Extract data from PostgreSQL and load into ClickHouse"""
    logger = logging.getLogger(__name__)
    
    # Use environment variables for connection
    pg_conn_string = f"postgresql+psycopg2://{os.getenv('POSTGRES_USER', 'airflow')}:{os.getenv('POSTGRES_PASSWORD', 'airflow')}@{os.getenv('POSTGRES_HOST', 'postgres')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'airflow')}"
    
    logger.info("Connecting to PostgreSQL...")
    pg_engine = create_engine(pg_conn_string)
    
    logger.info("Extracting data from PostgreSQL...")
    query = "SELECT * FROM events"
    events_df = pd.read_sql(query, pg_engine)
    
    if 'timestamp' in events_df.columns:
        events_df["timestamp"] = pd.to_datetime(events_df["timestamp"]).dt.tz_localize(None)
    
    # Convert UUID columns to strings
    for col in ['event_id', 'user_id']:
        if col in events_df.columns:
            events_df[col] = events_df[col].astype(str)
    
    logger.info(f"Extracted {len(events_df)} rows from PostgreSQL")
    
    logger.info("Connecting to ClickHouse...")
    client = Client(host='clickhouse', port=9000, user='default', password='')
    
    logger.info("Clearing existing data...")
    client.execute("TRUNCATE TABLE events_db.events")
    
    logger.info("Loading data into ClickHouse...")
    batch_size = 1000
    for i in range(0, len(events_df), batch_size):
        batch = events_df.iloc[i:i+batch_size]
        data = batch[['event_id', 'user_id', 'username', 'event_type', 'page_url', 'ip_address', 'timestamp']].values.tolist()
        
        client.execute("INSERT INTO events_db.events VALUES", data)
        logger.info(f"Inserted batch {i//batch_size + 1}/{(len(events_df)-1)//batch_size + 1}")
    
    count = client.execute("SELECT COUNT(*) FROM events_db.events")[0][0]
    logger.info(f"✓ Successfully loaded {count} rows into ClickHouse")
    
    context['task_instance'].xcom_push(key='record_count', value=count)
    client.disconnect()
    
    return count

def verify_clickhouse_data(**context):
    """Verify data was loaded correctly"""
    logger = logging.getLogger(__name__)
    
    client = Client(host='clickhouse', port=9000, user='default', password='')
    
    count = client.execute("SELECT COUNT(*) FROM events_db.events")[0][0]
    logger.info(f"Total records in ClickHouse: {count}")
    
    date_range = client.execute("""
        SELECT 
            MIN(timestamp) as earliest,
            MAX(timestamp) as latest,
            COUNT(DISTINCT user_id) as unique_users
        FROM events_db.events
    """)[0]
    logger.info(f"Date range: {date_range[0]} to {date_range[1]}")
    logger.info(f"Unique users: {date_range[2]}")
    
    client.disconnect()
    
    if count == 0:
        raise ValueError("No data found in ClickHouse!")
    
    return count

setup_task = PythonOperator(
    task_id='setup_clickhouse_schema',
    python_callable=setup_clickhouse_schema,
    dag=dag,
)

extract_load_task = PythonOperator(
    task_id='extract_and_load_to_clickhouse',
    python_callable=extract_and_load_to_clickhouse,
    dag=dag,
)

verify_task = PythonOperator(
    task_id='verify_clickhouse_data',
    python_callable=verify_clickhouse_data,
    dag=dag,
)

# Updated dbt command with explicit paths
dbt_run_task = BashOperator(
    task_id='dbt_run',
    bash_command='cd /opt/airflow/event_gen && /home/airflow/.local/bin/dbt run --profiles-dir /opt/airflow/.dbt --project-dir /opt/airflow/event_gen',
    dag=dag,
)

dbt_test_task = BashOperator(
    task_id='dbt_test',
    bash_command='cd /opt/airflow/event_gen && /home/airflow/.local/bin/dbt test --profiles-dir /opt/airflow/.dbt --project-dir /opt/airflow/event_gen',
    dag=dag,
)

dbt_docs_task = BashOperator(
    task_id='dbt_docs_generate',
    bash_command='cd /opt/airflow/event_gen && /home/airflow/.local/bin/dbt docs generate --profiles-dir /opt/airflow/.dbt --project-dir /opt/airflow/event_gen',
    dag=dag,
)

# Define task dependencies
setup_task >> extract_load_task >> verify_task >> dbt_run_task >> dbt_test_task >> dbt_docs_task
