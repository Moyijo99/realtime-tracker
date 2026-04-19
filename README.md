# Real-Time Event Tracking Pipeline

A production-style data engineering project that simulates the core event ingestion and analytics stack used by product and growth teams. User events flow from a Kafka message queue through a consumer service into PostgreSQL, then get extracted, loaded, and transformed via Airflow and dbt into ClickHouse for analytics — all visualized in Metabase.

> **Why this stack?** Kafka decouples event ingestion from processing, allowing the pipeline to handle bursts without data loss. ClickHouse is chosen over querying PostgreSQL directly because it's purpose-built for aggregation over large event volumes — queries that take seconds in Postgres run in milliseconds in ClickHouse. dbt enforces SQL-based transformation logic as version-controlled code rather than ad hoc queries.

---

## Architecture

```
Event Producer (Python/Faker)
        │
        ▼
   Apache Kafka          ← message queue, decouples ingestion from processing
        │
        ▼
  Kafka Consumer
        │
        ▼
   PostgreSQL            ← operational store / Airflow metadata
        │
        ▼  (Airflow DAG — hourly)
   ClickHouse            ← OLAP store optimised for analytics queries
        │
        ▼
  dbt models             ← staging → mart transformation layer
        │
        ▼
    Metabase              ← dashboards & visualisation
```

---

## Pipeline Stages

**1. Event Generation**
A Python producer using `Faker` continuously generates synthetic user events (page views, clicks, conversions) and publishes them to the `events` Kafka topic.

**2. Event Ingestion**
A Kafka consumer reads from the topic and writes raw events into PostgreSQL. PostgreSQL acts as the operational store and source of truth before analytics processing.

**3. Orchestration & Load**
An Airflow DAG runs hourly to extract new events from PostgreSQL and load them into ClickHouse. This ELT separation means the raw data is always preserved and reprocessable.

**4. Transformation**
dbt models layer on top of ClickHouse:
- `staging/` — light cleaning and type casting of raw events
- `marts/` — aggregated models ready for dashboard consumption

**5. Visualisation**
Metabase connects directly to ClickHouse marts for real-time dashboards.

---

## Tech Stack

| Layer | Tool | Purpose |
|---|---|---|
| Ingestion | Apache Kafka | Event streaming & decoupling |
| Storage | PostgreSQL | Operational / raw event store |
| Orchestration | Apache Airflow | Scheduling & pipeline monitoring |
| OLAP | ClickHouse | High-performance analytics queries |
| Transformation | dbt | Version-controlled SQL models |
| Visualisation | Metabase | Dashboards |
| Synthetic Data | Python + Faker | Event simulation |

---

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.10+
- Git

### Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/Moyijo99/realtime-tracker.git
cd realtime-tracker

# 2. Start all services
docker-compose up -d

# 3. Create the Kafka topic
docker-compose exec kafka kafka-topics \
  --create --topic events \
  --partitions 1 --replication-factor 1 \
  --if-not-exists \
  --bootstrap-server localhost:9092
```

### Access Services

| Service | URL | Credentials |
|---|---|---|
| Airflow | http://localhost:8080 | admin / admin |
| Metabase | http://localhost:3000 | — |
| ClickHouse (HTTP) | http://localhost:8123 | — |
| ClickHouse (native) | localhost:9000 | — |

---

## Project Structure

```
realtime-tracker/
├── dags/
│   └── events_pipeline_dag.py   # Airflow DAG: PostgreSQL → ClickHouse → dbt
├── event_gen/                    # dbt project
│   ├── models/
│   │   ├── staging/              # Type casting, deduplication
│   │   └── marts/                # Aggregated analytics models
│   └── dbt_project.yml
├── event_producer.py             # Synthetic event generation (Faker)
├── consumer.py                   # Kafka consumer → PostgreSQL
├── docker-compose.yml            # Full service stack
├── Dockerfile.airflow
├── Dockerfile.consumer
├── Dockerfile.producer
└── requirements.txt
```

---

## Environment Variables

```env
# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# PostgreSQL
POSTGRES_USER=airflow
POSTGRES_PASSWORD=airflow
POSTGRES_DB=airflow

# ClickHouse
CLICKHOUSE_DB=events_db
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=
```

Airflow also requires two connections configured in the UI:
- `postgres_default`
- `clickhouse_default`

---

## Monitoring & Debugging

```bash
# Stream producer / consumer logs
docker-compose logs -f producer
docker-compose logs -f consumer

# Verify Kafka messages
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic events --from-beginning

# Check row counts
docker-compose exec postgres psql -U airflow -d airflow \
  -c "SELECT COUNT(*) FROM events;"

docker-compose exec clickhouse clickhouse-client \
  --query "SELECT COUNT(*) FROM events_db.events;"
```

### Common Issues

| Symptom | Likely Cause | Fix |
|---|---|---|
| Kafka connection refused | Zookeeper not healthy | Check `KAFKA_BOOTSTRAP_SERVERS`; wait for Zookeeper startup |
| Missing data in ClickHouse | DAG not triggered or failed | Check Airflow DAG logs; verify Postgres → ClickHouse transfer |
| Consumer not processing | Topic doesn't exist | Confirm topic was created; check consumer group ID in logs |

---

## Extending the Project

**Change event schema** — edit `event_producer.py` and update the corresponding dbt staging model to reflect new fields.

**Adjust pipeline frequency** — modify `schedule_interval` in `events_pipeline_dag.py`.

**Add dbt models** — place new `.sql` files under `models/` and run:
```bash
dbt run --profiles-dir /opt/airflow/.dbt
```

---

## License

MIT — free to use, modify, and distribute.
