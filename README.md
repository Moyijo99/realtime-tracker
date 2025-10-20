# 🚀 Real-Time Event Tracking Pipeline

A scalable real-time event tracking pipeline that processes user events through Kafka, stores them in PostgreSQL, transforms them with dbt in ClickHouse, and visualizes them in Metabase.

## 🏗️ Architecture
graph LR
    A[Event Producer] --> B[Kafka]
    B --> C[Consumer]
    C --> D[PostgreSQL]
    E[Airflow DAG] --> D
    E --> F[ClickHouse]
    F --> G[Metabase]

## ⚙️ Components

- Event Producer: Generates synthetic user events (Python + Faker)

- Apache Kafka: Message queue for event streaming

- Event Consumer: Processes events from Kafka to PostgreSQL

- PostgreSQL: Initial data storage

- Apache Airflow: Orchestrates data pipeline

- ClickHouse: OLAP database for analytics

- dbt: Data transformation

- Metabase: Data visualization

## 📋 Prerequisites

Docker and Docker Compose

Python 3.10+

Git

## 🚀 Quick Start
1. Clone the repository
git clone https://github.com/Moyijo99/realtime-tracker.git
cd realtime-tracker

2. Start the services
docker-compose up -d

3. Create Kafka topic
docker-compose exec kafka kafka-topics --create --topic events \
    --partitions 1 --replication-factor 1 --if-not-exists \
    --bootstrap-server localhost:9092

4. Access the services

🌀 Airflow: http://localhost:8080

(user: admin, password: admin)

📊 Metabase: http://localhost:3000

🗄️ ClickHouse: localhost:8123 (HTTP) or localhost:9000 (native)

## 📁 Project Structure

realtime-tracker/
├── dags/
│   └── events_pipeline_dag.py     # Airflow DAG definition
├── event_gen/                     # dbt project
│   ├── models/
│   │   ├── staging/              # Initial data models
│   │   └── marts/                # Final analytics models
│   └── dbt_project.yml
├── docker-compose.yml             # Service definitions
├── Dockerfile.airflow             # Airflow custom image
├── Dockerfile.consumer            # Kafka consumer image
├── Dockerfile.producer            # Event producer image
├── event_producer.py              # Event generation script
├── consumer.py                    # Kafka consumer script
└── requirements.txt               # Python dependencies

## 🔄 Pipeline Flow

1️⃣ Event Generation

The producer continuously generates synthetic user events

Events are published to the Kafka topic events

2️⃣ Event Processing

The consumer reads events from Kafka

Events are stored in PostgreSQL

3️⃣ Data Pipeline

The Airflow DAG runs hourly

Extracts data from PostgreSQL

Loads into ClickHouse

Runs dbt models for transformation

4️⃣ Analytics

Transformed data available in ClickHouse

Visualized through Metabase dashboards

## ⚙️ Configuration

- Environment Variables
    Kafka
    KAFKA_BOOTSTRAP_SERVERS=kafka:9092

- PostgreSQL
    POSTGRES_USER=airflow
    POSTGRES_PASSWORD=airflow
    POSTGRES_DB=airflow

- ClickHouse
    CLICKHOUSE_DB=events_db
    CLICKHOUSE_USER=default
    CLICKHOUSE_PASSWORD=""

- Airflow Connections

Required connections in Airflow:

    postgres_default
    clickhouse_default

## 🧠 Monitoring

Check producer logs
docker-compose logs -f producer

Check consumer logs
docker-compose logs -f consumer

Check Kafka messages
docker-compose exec kafka kafka-console-consumer \
    --bootstrap-server localhost:9092 \
    --topic events --from-beginning

Check PostgreSQL data
docker-compose exec postgres psql -U airflow -d airflow \
    -c "SELECT COUNT(*) FROM events;"

Check ClickHouse data
docker-compose exec clickhouse clickhouse-client \
    --query "SELECT COUNT(*) FROM events_db.events;"

## 🧩 Development

1. Modify Event Producer

- Edit event_producer.py to change event generation logic

- Adjust generation rate in the main loop

2. Update Transformations

- Modify dbt models under models/

- Run dbt manually:

    dbt run --profiles-dir /opt/airflow/.dbt

3. Adjust Pipeline Schedule

- Edit events_pipeline_dag.py

- Change schedule_interval to set frequency

## 🧰 Troubleshooting
Issue	Possible Cause	Solution
Kafka Connection Issues	Zookeeper not running	Ensure Zookeeper is active and check KAFKA_BOOTSTRAP_SERVERS
Missing Data in ClickHouse	Airflow DAG not triggered	Verify DAG status, PostgreSQL → ClickHouse transfer logs, and dbt execution
Consumer Not Processing	Kafka topic missing	Confirm topic exists, verify consumer group ID, and database connection

## 📜 License

MIT License
Free to use, modify, and distribute.

## 🤝 Contributing

1. Fork the repository

2. Create your feature branch

3. Commit your changes

4. Push to the branch

5. Create a Pull Request

💡 Built with ❤️ for real-time analytics, data engineering, and scalable event-driven systems.