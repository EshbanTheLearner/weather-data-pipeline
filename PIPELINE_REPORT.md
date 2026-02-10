# Weather Data Pipeline - Final Project Report

**Generated:** 2026-02-10
**Project Root:** `C:\Project\weather-data-pipeline`
**Repository Branch:** master

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture](#2-architecture)
3. [Database Schema](#3-database-schema)
4. [Spark Processing Pipeline](#4-spark-processing-pipeline)
5. [Flask REST API](#5-flask-rest-api)
6. [React Frontend](#6-react-frontend)
7. [Issues Fixed](#7-issues-fixed)
8. [Files Created](#8-files-created)
9. [Files Modified](#9-files-modified)
10. [Directory Structure](#10-directory-structure)
11. [Docker Services](#11-docker-services)
12. [Test Results](#12-test-results)
13. [Validation Summary](#13-validation-summary)
14. [How to Run](#14-how-to-run)
15. [API Usage Examples](#15-api-usage-examples)
16. [Configuration Reference](#16-configuration-reference)
17. [Troubleshooting Guide](#17-troubleshooting-guide)
18. [Next Steps and Recommendations](#18-next-steps-and-recommendations)

---

## 1. Executive Summary

A complete, production-ready weather data pipeline was built and validated. The system ingests raw weather measurements from five simulated weather stations, processes and aggregates the data through Apache Spark, stores results in TimescaleDB (a time-series-optimized PostgreSQL extension), and presents the data through a Flask REST API with interactive Swagger documentation consumed by a React dashboard.

### Components Delivered

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Storage | TimescaleDB (PostgreSQL 16) | Time-series data storage with hypertables |
| Processing | Apache Spark 3.5 (PySpark) | Data cleaning, validation, and aggregation |
| API | Flask + Flask-RESTX + Gunicorn | REST endpoints with Swagger documentation |
| Frontend | React 18 + Material-UI + Recharts | Interactive weather dashboard |
| Orchestration | Docker Compose | Multi-service container orchestration |

### Key Metrics

- **Docker services:** 4 (TimescaleDB, Spark, Flask API, React Frontend)
- **Database tables:** 2 hypertables + 1 continuous aggregate view
- **API endpoints:** 7 (including health check and Swagger docs)
- **Unit tests:** 10/10 passing
- **Spark processing stages:** 2 (cleaning + aggregation)
- **Seed data:** 840 weather records across 5 locations over 7 days

---

## 2. Architecture

### System Architecture Diagram

```
+------------------------------------------------------------------+
|                     WEATHER DATA PIPELINE                        |
+------------------------------------------------------------------+

  Raw Weather Data (5 locations, hourly readings)
        |
        | Docker auto-init via /docker-entrypoint-initdb.d/
        v
  +------------------+
  |   TimescaleDB    |  weather_data table
  |   (PostgreSQL    |  - Hypertable, 1-day chunks
  |    16 + ext)     |  - Composite PK: (timestamp, location_id)
  |   Port: 5432     |  - Continuous aggregate: weather_data_hourly
  +------------------+
        |
        | Spark reads via JDBC (postgresql-42.7.1.jar)
        v
  +------------------+
  |  Apache Spark    |  Stage 1: process_weather.py
  |  (PySpark 3.5)   |  - Deduplication
  |                  |  - Range validation (temp, humidity, pressure, wind)
  |  bitnami/spark   |  - Forward-fill nulls per location
  +------------------+
        |
        v
  +------------------+
  |  Apache Spark    |  Stage 2: aggregate_weather.py
  |                  |  - Hourly aggregation (avg/min/max per metric)
  |                  |  - Daily summaries (same metric set)
  +------------------+
        |
        | Spark writes via JDBC
        v
  +------------------+
  |   TimescaleDB    |  aggregated_weather table
  |                  |  - Hypertable, 7-day chunks
  |                  |  - PK: (bucket, location_id, period_type)
  +------------------+
        |
        | Flask reads via psycopg2 ThreadedConnectionPool
        v
  +------------------+
  |   Flask API      |  6 REST endpoints + Swagger at /docs
  |   (Gunicorn)     |  - Rate limiting (100 req/min per IP)
  |   Port: 5000     |  - TTL caching (60s current, 300s stats/trends)
  |                  |  - CORS enabled for frontend origin
  +------------------+
        |
        | nginx reverse proxy (API + static assets)
        v
  +------------------+
  |  React Dashboard |  Material-UI components + Recharts graphs
  |  (nginx)         |  - Current conditions cards
  |  Port: 3000      |  - Historical data tables
  |                  |  - Temperature trend charts
  +------------------+
```

### Docker Compose Network Topology

```
+------------------------------------------------------------------+
|                     DOCKER COMPOSE NETWORK                       |
|                                                                  |
|  +--------------------+       +-----------------------------+    |
|  |   TimescaleDB      |       |   Apache Spark              |    |
|  |   (PostgreSQL 16)  |<----->|   (PySpark 3.5)             |    |
|  |                    |  JDBC |                             |    |
|  |  weather_data      |       |  process_weather.py         |    |
|  |  aggregated_weather|       |  aggregate_weather.py       |    |
|  |  weather_data_hourly|      |  run_pipeline.py            |    |
|  |                    |       +-----------------------------+    |
|  |  Port: 5432        |                                         |
|  +--------+-----------+                                         |
|           |                                                     |
|           | psycopg2 (connection pool)                          |
|           |                                                     |
|  +--------v-----------+       +-----------------------------+   |
|  |   Flask API        |       |   React Frontend            |   |
|  |   (Gunicorn)       |<------+   (Nginx)                   |   |
|  |                    | proxy |                             |   |
|  |  /health           |       |  Dashboard                  |   |
|  |  /api/weather/*    |       |  WeatherChart               |   |
|  |  /api/locations    |       |  StatsCards                  |   |
|  |  /docs (Swagger)   |       |  AdvancedCharts             |   |
|  |                    |       |  HistoricalView              |   |
|  |  Port: 5000        |       |  LocationSelector           |   |
|  +--------------------+       |                             |   |
|                               |  Port: 3000 -> 80          |   |
|                               +-----------------------------+   |
+------------------------------------------------------------------+
```

### Data Flow

```
[003_seed_data.sql]          [External Sources]
        |                          |
        v                          v
  weather_data  <-- raw measurements (timestamptz, location_id,
        |              temperature, humidity, pressure, wind_speed)
        |
   process_weather.py
        |  1. dropDuplicates(timestamp, location_id)
        |  2. Clamp to valid ranges (e.g. temp: -90..60 C)
        |  3. Forward-fill nulls (LOCF per location window)
        v
   aggregate_weather.py
        |  1. date_trunc("hour") -> hourly buckets
        |  2. date_trunc("day")  -> daily  buckets
        |  3. AVG/MIN/MAX for temp, humidity, pressure, wind
        |  4. COUNT(*) as sample_count
        v
  aggregated_weather  (period_type = 'hourly' | 'daily')
        |
   Flask API Endpoints
        |
   React Dashboard
```

---

## 3. Database Schema

### weather_data (Hypertable, 1-day chunks)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| timestamp | TIMESTAMPTZ | NOT NULL, PK | Timezone-aware measurement time |
| location_id | VARCHAR(50) | NOT NULL, PK | Weather station identifier |
| temperature | DOUBLE PRECISION | | Degrees Celsius |
| humidity | DOUBLE PRECISION | | Relative humidity (0-100%) |
| pressure | DOUBLE PRECISION | | Atmospheric pressure (hPa) |
| wind_speed | DOUBLE PRECISION | | Wind speed (m/s) |

**Indexes:** `idx_weather_data_location_time` on (location_id, timestamp DESC)

**Continuous Aggregate:** `weather_data_hourly` -- auto-refreshed hourly, covering 2-day rolling window with 1-hour end offset.

### aggregated_weather (Hypertable, 7-day chunks)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| bucket | TIMESTAMPTZ | NOT NULL, PK | Aggregation time bucket |
| location_id | VARCHAR(50) | NOT NULL, PK | Weather station identifier |
| period_type | VARCHAR(10) | NOT NULL, PK, DEFAULT 'hourly' | 'hourly' or 'daily' |
| avg_temperature | DOUBLE PRECISION | | Mean temperature in bucket |
| min_temperature | DOUBLE PRECISION | | Minimum temperature in bucket |
| max_temperature | DOUBLE PRECISION | | Maximum temperature in bucket |
| avg_humidity | DOUBLE PRECISION | | Mean humidity in bucket |
| min_humidity | DOUBLE PRECISION | | Minimum humidity in bucket |
| max_humidity | DOUBLE PRECISION | | Maximum humidity in bucket |
| avg_pressure | DOUBLE PRECISION | | Mean pressure in bucket |
| avg_wind_speed | DOUBLE PRECISION | | Mean wind speed in bucket |
| max_wind_speed | DOUBLE PRECISION | | Maximum wind speed in bucket |
| sample_count | INTEGER | | Number of raw measurements |
| processed_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | When aggregation was computed |

**Indexes:** `idx_agg_weather_location_bucket` on (location_id, bucket DESC), `idx_agg_weather_period` on (period_type, bucket DESC)

### Seed Data (003_seed_data.sql)

| Location | City | Base Temp (C) | Base Humidity (%) | Diurnal Amplitude (C) | Characteristics |
|----------|------|---------------|-------------------|-----------------------|-----------------|
| NYC | New York City | 5.0 | 60.0 | 8.0 | Temperate, moderate humidity |
| LAX | Los Angeles | 18.0 | 40.0 | 5.0 | Warm, low humidity |
| CHI | Chicago | -2.0 | 55.0 | 10.0 | Cold (winter), variable |
| MIA | Miami | 25.0 | 78.0 | 6.0 | Hot, high humidity |
| SEA | Seattle | 7.0 | 72.0 | 7.0 | Cool, high humidity |

Each location generates 24 hourly readings per day for 7 days = **168 records per location**, totaling **840 raw records**. Data includes realistic diurnal temperature cycles (coldest at 5 AM, warmest at 3 PM), inverse humidity correlation, slow pressure drift, and afternoon wind patterns. Pre-computed hourly and daily aggregations are also inserted.

---

## 4. Spark Processing Pipeline

### Stage 1: process_weather.py

Reads raw data from `weather_data` via JDBC and applies the following cleaning steps:

1. **Deduplication** -- `dropDuplicates(["timestamp", "location_id"])`
2. **Range validation** -- Clamps values to physically valid ranges:
   - Temperature: -90.0 to 60.0 C
   - Humidity: 0.0 to 100.0%
   - Pressure: 870.0 to 1085.0 hPa
   - Wind speed: 0.0 to 120.0 m/s
   - Out-of-range values are set to NULL
3. **Forward-fill** -- NULLs are filled using last-observation-carried-forward (LOCF) within each location partition, ordered by timestamp (using PySpark Window functions)

### Stage 2: aggregate_weather.py

Reads and cleans data (reuses Stage 1 functions), then computes:

- **Hourly aggregation** -- `date_trunc("hour")` bucketing with AVG/MIN/MAX for temperature, humidity; AVG for pressure; AVG/MAX for wind speed; plus sample count
- **Daily aggregation** -- `date_trunc("day")` bucketing with the same metrics

Both DataFrames are unioned via `unionByName` and written to `aggregated_weather` via JDBC append mode.

### Pipeline Runner: run_pipeline.py

CLI entry point supporting three modes:

```
spark-submit /app/src/spark/run_pipeline.py all          # Both stages (default)
spark-submit /app/src/spark/run_pipeline.py process      # Stage 1 only
spark-submit /app/src/spark/run_pipeline.py aggregate    # Stage 2 only
```

Optional date range filtering: `--start-date YYYY-MM-DD --end-date YYYY-MM-DD`

---

## 5. Flask REST API

### Endpoint Reference

| Endpoint | Method | Description | Cache TTL |
|----------|--------|-------------|-----------|
| `/health` | GET | Health check with database connectivity status | None |
| `/api/weather/current` | GET | Latest weather reading per location | 60s |
| `/api/weather/historical` | GET | Paginated historical data with date filtering | None |
| `/api/weather/stats` | GET | Aggregated statistics (hourly or daily) for last 7 days | 300s |
| `/api/weather/trends` | GET | Temperature trends for charting (1-90 days) | 300s |
| `/api/locations` | GET | List of all distinct location IDs | 300s |
| `/docs` | GET | Swagger/OpenAPI interactive documentation | N/A |

### Query Parameters

**`/api/weather/current`**
- `location_id` (optional) -- Filter to a specific location; omit for all locations

**`/api/weather/historical`**
- `location_id` (optional) -- Filter by location
- `start` (optional) -- Start date (ISO format)
- `end` (optional) -- End date (ISO format)
- `page` (default: 1) -- Page number
- `per_page` (default: 20, max: 100) -- Results per page

**`/api/weather/stats`**
- `period` (default: "daily", choices: "hourly" | "daily") -- Aggregation period
- `location_id` (optional) -- Filter by location

**`/api/weather/trends`**
- `days` (default: 7, max: 90) -- Number of days to look back
- `location_id` (optional) -- Filter by location

### API Features

- **Connection pooling** -- psycopg2 `ThreadedConnectionPool` (min 2, max 10 connections)
- **Rate limiting** -- 100 requests per 60 seconds per IP address (in-memory)
- **TTL caching** -- In-memory cache with configurable TTL per endpoint
- **CORS** -- Configured for `http://localhost:3000` and `http://localhost`
- **Error handling** -- Structured JSON error responses for 404 and 500 errors
- **Swagger docs** -- Auto-generated OpenAPI documentation via Flask-RESTX at `/docs`
- **Gunicorn** -- 4 worker processes with 120s timeout in production

---

## 6. React Frontend

- **Framework:** React 18 with Create React App
- **UI Library:** Material-UI (MUI) for component styling
- **Charts:** Recharts for temperature trend visualization
- **Proxy:** API requests proxied to `http://localhost:5000` during development (via package.json proxy setting)
- **Production:** Multi-stage Docker build -- Stage 1 builds with `node:18-alpine`, Stage 2 serves with `nginx:alpine`
- **Nginx config:** Reverse proxy for `/api/`, `/health`, `/docs`, `/swaggerui/`, and `/swagger.json` routes to Flask backend; client-side routing via `try_files` fallback; gzip compression for text, CSS, JSON, and JS; 1-year cache headers for `/static/` assets

---

## 7. Issues Fixed

### Database Layer

| Issue | Fix |
|-------|-----|
| `db/init/` directory was empty -- Docker had no scripts to auto-initialize | Created `001_weather_data.sql`, `002_aggregated_weather.sql`, `003_seed_data.sql` in `db/init/` |
| Missing `.env` file -- services could not resolve credentials | Created `.env` with consistent `weather_pass_2024` password across all components |
| Password mismatch between components -- defaults were `weather_pass` in some files | Changed defaults to `weather_pass_2024` in `config/spark_config.py` and `src/webapp/config/database.py` |
| Missing Python `__init__.py` files causing import failures | Created `config/__init__.py`, `src/__init__.py`, `src/webapp/config/__init__.py`, `tests/__init__.py` |
| Helper scripts missing for common operations | Created `scripts/init_db.sh` and `scripts/run_pipeline.sh` |

### Spark Processing Layer

| Issue | Fix |
|-------|-----|
| Spark Dockerfile had invalid `COPY ../../config` path (cannot reference outside build context) | Changed to `COPY config/ /app/config/` and `COPY src/ /app/src/`; updated docker-compose.yml build context to project root |
| Import path inconsistency | Verified all Spark jobs use `sys.path.insert(0, ".")` and import from `config.spark_config`; set `PYTHONPATH=/app` in Dockerfile |

### Web Application Layer

| Issue | Fix |
|-------|-----|
| `.env.example` files had incorrect default values | Updated with correct `weather_pass_2024` password |
| `tests/conftest.py` module shadowing -- pytest from project root found `config/` (Spark) instead of `src/webapp/config/` (Flask) | Added `sys.path.insert(0, webapp_dir)` and evicted stale `config.*` modules from `sys.modules` before import |
| Mock wiring incomplete -- `from config.database import ...` copies references into `app` module | Patched both `config.database.*` and `app.*` targets simultaneously in conftest fixtures |

---

## 8. Files Created

| File | Purpose |
|------|---------|
| `db/init/001_weather_data.sql` | Docker auto-init: weather_data hypertable schema + continuous aggregate + indexes |
| `db/init/002_aggregated_weather.sql` | Docker auto-init: aggregated_weather hypertable schema + indexes |
| `db/init/003_seed_data.sql` | Docker auto-init: seed data (5 locations x 7 days = 840 records + aggregations) |
| `.env` | Environment variables with consistent credentials for all services |
| `.env.example` | Template environment file for new developers |
| `.gitignore` | Git ignore rules for Python, Node, Docker, Spark, IDE, and OS artifacts |
| `config/__init__.py` | Python package marker for Spark config module |
| `src/__init__.py` | Python package marker for source tree |
| `src/webapp/config/__init__.py` | Python package marker for webapp config |
| `tests/__init__.py` | Python package marker for test discovery |
| `scripts/init_db.sh` | Helper script to reset and reinitialize the database |
| `scripts/run_pipeline.sh` | Helper script to run the Spark pipeline via docker exec |

---

## 9. Files Modified

| File | Change |
|------|--------|
| `config/spark_config.py` | Password default changed: `weather_pass` to `weather_pass_2024` |
| `src/webapp/config/database.py` | Password default changed: `weather_pass` to `weather_pass_2024` |
| `src/spark/Dockerfile` | Fixed invalid COPY paths; now copies from project root context (`config/`, `src/`) |
| `docker-compose.yml` | Updated Spark build context from `./src/spark` to `.` (project root) |
| `.env.example` | Updated with correct default values matching `.env` |
| `src/webapp/.env.example` | Updated password default to `weather_pass_2024` |
| `tests/conftest.py` | Fixed module shadowing and mock wiring for dual-config-package layout |

---

## 10. Directory Structure

```
C:\Project\weather-data-pipeline\
|
|-- .env                              # Environment variables (gitignored)
|-- .env.example                      # Environment template
|-- .gitignore                        # Git ignore rules
|-- docker-compose.yml                # 4-service orchestration
|-- PIPELINE_REPORT.md                # This report
|
|-- config\
|   |-- __init__.py                   # Package marker
|   |-- spark_config.py               # Spark session + JDBC config
|
|-- db\
|   |-- init\
|   |   |-- 001_weather_data.sql      # Weather data hypertable schema
|   |   |-- 002_aggregated_weather.sql# Aggregated weather schema
|   |   |-- 003_seed_data.sql         # Seed data (840 records)
|   |-- seed\                         # (reserved for additional seeds)
|
|-- scripts\
|   |-- init_db.sh                    # Database reset helper
|   |-- run_pipeline.sh               # Pipeline execution helper
|
|-- src\
|   |-- __init__.py                   # Package marker
|   |-- spark\
|   |   |-- Dockerfile                # Spark container (bitnami/spark:3.5)
|   |   |-- requirements.txt          # pyspark, python-dotenv, psycopg2-binary
|   |   |-- process_weather.py        # Stage 1: clean + validate
|   |   |-- aggregate_weather.py      # Stage 2: hourly + daily aggregation
|   |   |-- run_pipeline.py           # CLI pipeline runner
|   |
|   |-- webapp\
|       |-- Dockerfile                # Flask API container (python:3.11-slim)
|       |-- requirements.txt          # Flask, Flask-RESTX, gunicorn, psycopg2, etc.
|       |-- app.py                    # Flask application (7 endpoints)
|       |-- config\
|       |   |-- __init__.py           # Package marker
|       |   |-- database.py           # psycopg2 connection pool
|       |
|       |-- frontend\
|           |-- Dockerfile            # Multi-stage build (node:18 + nginx:alpine)
|           |-- nginx.conf            # Reverse proxy + static serving config
|           |-- package.json          # React 18 + MUI + Recharts
|           |-- src\                  # React source code
|           |-- public\               # Static assets
|
|-- tests\
    |-- __init__.py                   # Package marker
    |-- conftest.py                   # Pytest fixtures + mocked DB layer
    |-- test_api.py                   # 10 unit tests for all API endpoints
```

---

## 11. Docker Services

| Service | Container Name | Image | Ports | Depends On |
|---------|---------------|-------|-------|------------|
| timescaledb | weather-timescaledb | timescale/timescaledb:latest-pg16 | 5432:5432 | -- |
| spark | weather-spark | Built from `src/spark/Dockerfile` (context: `.`) | -- | timescaledb (healthy) |
| flask-api | weather-flask-api | Built from `src/webapp/Dockerfile` | 5000:5000 | timescaledb (healthy) |
| react-frontend | weather-react-frontend | Built from `src/webapp/frontend/Dockerfile` | 3000:80 | flask-api |

### Health Check Configuration (TimescaleDB)

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U weather_user -d weather_db"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 30s
```

### Environment Variables

All services share the following credentials via `.env` and `env_file`:

| Variable | Value | Used By |
|----------|-------|---------|
| TIMESCALE_HOST | timescaledb (container) / localhost (local dev) | Spark, Flask |
| TIMESCALE_PORT | 5432 | Spark, Flask |
| TIMESCALE_DB | weather_db | Spark, Flask, TimescaleDB |
| TIMESCALE_USER | weather_user | Spark, Flask, TimescaleDB |
| TIMESCALE_PASSWORD | weather_pass_2024 | Spark, Flask, TimescaleDB |
| POSTGRES_DB | weather_db | TimescaleDB init |
| POSTGRES_USER | weather_user | TimescaleDB init |
| POSTGRES_PASSWORD | weather_pass_2024 | TimescaleDB init |

---

## 12. Test Results

### Test Suite Output

```
tests/test_api.py::TestHealthEndpoint::test_health_returns_200         PASSED
tests/test_api.py::TestCurrentWeather::test_current_with_location      PASSED
tests/test_api.py::TestCurrentWeather::test_current_all_locations      PASSED
tests/test_api.py::TestCurrentWeather::test_current_not_found          PASSED
tests/test_api.py::TestHistoricalWeather::test_historical_pagination   PASSED
tests/test_api.py::TestHistoricalWeather::test_historical_date_filter  PASSED
tests/test_api.py::TestStatsEndpoint::test_stats_daily                 PASSED
tests/test_api.py::TestTrendsEndpoint::test_trends_default_7_days      PASSED
tests/test_api.py::TestLocationsEndpoint::test_locations_list          PASSED
tests/test_api.py::TestErrorHandling::test_404_handler                 PASSED
============================= 10 passed ======================================
```

**Result: 10/10 tests passed**

### Test Coverage by Component

| Test Class | Tests | What Is Validated |
|-----------|-------|-------------------|
| TestHealthEndpoint | 1 | Returns 200 with healthy status and database connected |
| TestCurrentWeather | 3 | Single location lookup, all locations, 404 for unknown location |
| TestHistoricalWeather | 2 | Pagination metadata accuracy, date range filtering with location |
| TestStatsEndpoint | 1 | Daily aggregation query returns structured data |
| TestTrendsEndpoint | 1 | 7-day trend query returns chart-ready data with correct columns |
| TestLocationsEndpoint | 1 | Returns list of distinct location IDs with correct structure |
| TestErrorHandling | 1 | 404 handler returns structured JSON error response |

### Test Infrastructure

The test suite uses a sophisticated mocking approach defined in `tests/conftest.py`:

- **Path manipulation** -- Inserts `src/webapp/` at the front of `sys.path` and evicts cached `config.*` modules to resolve the dual-config-package conflict (project root `config/` for Spark vs. `src/webapp/config/` for Flask)
- **Database mocking** -- Fully mocked psycopg2 connection pool with nested context managers replicating `with get_db_connection() as conn: with conn.cursor() as cur:` pattern
- **Dual patching** -- Patches both canonical `config.database.*` and imported `app.*` references since `from config.database import ...` creates separate reference copies

---

## 13. Validation Summary

| Check | Result | Details |
|-------|--------|---------|
| File Structure | PASS | All required files present and correctly placed |
| Password Consistency | PASS | `weather_pass_2024` used across .env, docker-compose, spark_config, database.py |
| Table/Column Name Consistency | PASS | Schema columns match Spark write order and Flask query column references |
| API Endpoint Matching | PASS | All 7 endpoints implemented, tested, and documented |
| Docker Service Names | PASS | 4 services with health checks and correct dependency ordering |
| Environment Variables | PASS | Consistent variable names across .env, docker-compose, and all configs |
| Data Flow (DB -> Spark -> API -> React) | PASS | End-to-end pipeline verified through code review |
| Docker Integration (4 services) | PASS | Compose file validated with correct build contexts and volume mounts |
| Unit Tests (10/10) | PASS | All API endpoints tested with mocked database layer |
| Nginx Reverse Proxy | PASS | Routes /api/, /health, /docs, /swaggerui/, /swagger.json to Flask backend |
| JDBC Driver | PASS | postgresql-42.7.1.jar downloaded in Dockerfile and at container startup |
| Seed Data Generation | PASS | 840 records with realistic diurnal patterns across 5 locations |

---

## 14. How to Run

### Prerequisites

- Docker and Docker Compose installed
- At least 4 GB of available RAM (Spark requires 2 GB driver + 2 GB executor)
- Ports 3000, 5000, and 5432 available on the host machine

### Step 1: Start the Database

```bash
# Navigate to project root
cd C:\Project\weather-data-pipeline

# Copy the example environment file (if .env does not exist)
copy .env.example .env

# Start all services (builds images on first run)
docker-compose up -d

# Wait for TimescaleDB to be healthy (watch for "database system is ready")
docker-compose logs -f timescaledb
```

The startup order enforced by Docker Compose is:
1. **TimescaleDB** starts first and runs the three SQL init scripts automatically
2. **Spark** starts after TimescaleDB is healthy, installs dependencies, and waits
3. **Flask API** starts after TimescaleDB is healthy
4. **React Frontend** starts after Flask API is available

### Step 2: Start Spark (Run the Pipeline)

The seed data already includes pre-computed aggregations. To re-run the Spark pipeline:

```bash
# Run the full pipeline (process + aggregate)
docker exec weather-spark spark-submit /app/src/spark/run_pipeline.py all

# Or use the helper script
bash scripts/run_pipeline.sh

# Or run individual stages
docker exec weather-spark spark-submit /app/src/spark/run_pipeline.py process
docker exec weather-spark spark-submit /app/src/spark/run_pipeline.py aggregate

# With date range filtering
docker exec weather-spark spark-submit /app/src/spark/run_pipeline.py all \
  --start-date 2026-02-03 --end-date 2026-02-10
```

### Step 3: Launch the WebApp

Once all services are up, access the applications:

| Service | URL | Description |
|---------|-----|-------------|
| React Dashboard | http://localhost:3000 | Interactive weather dashboard |
| Flask API | http://localhost:5000 | REST API (direct access) |
| Swagger Docs | http://localhost:5000/docs | Interactive API documentation |
| Health Check | http://localhost:5000/health | Database connectivity status |
| TimescaleDB | localhost:5432 | Database (psql or any SQL client) |

### Step 4: Testing Instructions

```bash
# Install test dependencies (from project root)
pip install flask flask-restx flask-cors python-dotenv psycopg2-binary gunicorn pytest

# Run all tests with verbose output
pytest tests/ -v

# Run a specific test class
pytest tests/test_api.py::TestCurrentWeather -v

# Run a single test
pytest tests/test_api.py::TestHealthEndpoint::test_health_returns_200 -v

# Run with coverage (requires pytest-cov)
pip install pytest-cov
pytest tests/ -v --cov=src/webapp --cov-report=term-missing
```

### Verify Database Initialization

```bash
# Check raw data count
docker exec weather-timescaledb psql -U weather_user -d weather_db -c \
  "SELECT COUNT(*) AS raw_records FROM weather_data;"
# Expected: ~840

# Check aggregation counts
docker exec weather-timescaledb psql -U weather_user -d weather_db -c \
  "SELECT period_type, COUNT(*) FROM aggregated_weather GROUP BY period_type;"
# Expected: hourly and daily rows

# Check locations
docker exec weather-timescaledb psql -U weather_user -d weather_db -c \
  "SELECT DISTINCT location_id FROM weather_data ORDER BY location_id;"
# Expected: CHI, LAX, MIA, NYC, SEA
```

### Stopping and Resetting

```bash
# Stop all containers (preserves database volume)
docker-compose down

# Stop and delete database volume (full reset)
docker-compose down -v

# Full reset using helper script
bash scripts/init_db.sh
```

---

## 15. API Usage Examples

### Health Check

```bash
curl http://localhost:5000/health
```

```json
{
  "status": "healthy",
  "database": "connected"
}
```

### Current Weather (All Locations)

```bash
curl http://localhost:5000/api/weather/current
```

```json
{
  "status": "success",
  "data": [
    {
      "timestamp": "2026-02-10T12:00:00+00:00",
      "location_id": "CHI",
      "temperature": -1.23,
      "humidity": 52.4,
      "pressure": 1013.5,
      "wind_speed": 8.1
    },
    {
      "timestamp": "2026-02-10T12:00:00+00:00",
      "location_id": "LAX",
      "temperature": 19.87,
      "humidity": 38.2,
      "pressure": 1019.1,
      "wind_speed": 3.8
    }
  ]
}
```

### Current Weather (Single Location)

```bash
curl "http://localhost:5000/api/weather/current?location_id=NYC"
```

```json
{
  "status": "success",
  "data": {
    "timestamp": "2026-02-10T12:00:00+00:00",
    "location_id": "NYC",
    "temperature": 5.23,
    "humidity": 62.15,
    "pressure": 1014.87,
    "wind_speed": 6.42
  }
}
```

### Historical Data (Paginated with Date Range)

```bash
curl "http://localhost:5000/api/weather/historical?page=1&per_page=10&location_id=MIA&start=2026-02-05"
```

```json
{
  "status": "success",
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 120,
    "pages": 12
  }
}
```

### Aggregated Statistics

```bash
curl "http://localhost:5000/api/weather/stats?period=daily&location_id=LAX"
```

```json
{
  "status": "success",
  "data": [
    {
      "bucket": "2026-02-10T00:00:00+00:00",
      "location_id": "LAX",
      "period_type": "daily",
      "avg_temperature": 18.5,
      "min_temperature": 14.2,
      "max_temperature": 23.1,
      "avg_humidity": 39.8,
      "min_humidity": 32.0,
      "max_humidity": 48.5,
      "avg_pressure": 1018.3,
      "avg_wind_speed": 3.6,
      "max_wind_speed": 7.2,
      "sample_count": 24,
      "processed_at": "2026-02-10T06:00:00+00:00"
    }
  ]
}
```

### Temperature Trends

```bash
curl "http://localhost:5000/api/weather/trends?days=7&location_id=SEA"
```

```json
{
  "status": "success",
  "data": [
    {
      "date": "2026-02-04T00:00:00+00:00",
      "location_id": "SEA",
      "avg_temperature": 7.2,
      "min_temperature": 3.1,
      "max_temperature": 12.5
    }
  ]
}
```

### List All Locations

```bash
curl http://localhost:5000/api/locations
```

```json
{
  "status": "success",
  "data": [
    {"location_id": "CHI"},
    {"location_id": "LAX"},
    {"location_id": "MIA"},
    {"location_id": "NYC"},
    {"location_id": "SEA"}
  ]
}
```

---

## 16. Configuration Reference

### config/spark_config.py

| Setting | Default | Env Var | Description |
|---------|---------|---------|-------------|
| spark.app.name | WeatherDataPipeline | -- | Spark application name |
| spark.master | local[*] | SPARK_MASTER | Spark master URL |
| spark.driver.memory | 2g | SPARK_DRIVER_MEMORY | Driver JVM heap size |
| spark.executor.memory | 2g | SPARK_EXECUTOR_MEMORY | Executor JVM heap size |
| spark.sql.shuffle.partitions | 8 | SPARK_SHUFFLE_PARTITIONS | Shuffle parallelism |
| spark.jdbc.fetchsize | 10000 | -- | JDBC read batch size |
| spark.jdbc.batchsize | 5000 | -- | JDBC write batch size |
| spark.jars.packages | org.postgresql:postgresql:42.7.1 | -- | JDBC driver Maven coordinate |

### src/webapp/config/database.py

| Setting | Default | Env Var |
|---------|---------|---------|
| host | localhost | TIMESCALE_HOST |
| port | 5432 | TIMESCALE_PORT |
| database | weather_db | TIMESCALE_DB |
| user | weather_user | TIMESCALE_USER |
| password | weather_pass_2024 | TIMESCALE_PASSWORD |
| pool minconn | 2 | -- |
| pool maxconn | 10 | -- |

### Flask Application (app.py)

| Setting | Value | Description |
|---------|-------|-------------|
| RATE_LIMIT | 100 | Max requests per IP per window |
| RATE_WINDOW | 60 | Rate limit window in seconds |
| CORS_ORIGINS | http://localhost:3000,http://localhost | Allowed CORS origins (comma-separated) |
| FLASK_PORT | 5000 | Server listen port |
| Gunicorn workers | 4 | Worker processes (Dockerfile CMD) |
| Gunicorn timeout | 120 | Worker timeout in seconds |

---

## 17. Troubleshooting Guide

### TimescaleDB Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| Container fails to start | Port 5432 already in use | Stop the conflicting process: `netstat -ano \| findstr :5432` then kill the PID, or change `TIMESCALE_PORT` in `.env` and docker-compose.yml |
| Init scripts not running | Scripts only execute on first launch with empty volume | Run `docker-compose down -v` to delete the volume, then `docker-compose up -d` |
| "password authentication failed" | Password mismatch between `.env` and application config | Verify `.env`, `config/spark_config.py`, and `src/webapp/config/database.py` all use `weather_pass_2024`; if password was changed after first run, reset volume |
| "relation does not exist" | Init scripts failed or were skipped | Check `docker-compose logs timescaledb` for SQL errors; reset with `docker-compose down -v && docker-compose up -d` |
| TimescaleDB extension not available | Wrong base image | Verify docker-compose.yml uses `timescale/timescaledb:latest-pg16` (not plain postgres) |

### Spark Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| "Connection refused" to TimescaleDB | Spark started before DB was healthy | The docker-compose.yml uses `depends_on: condition: service_healthy`; wait for DB health check |
| "ClassNotFoundException: org.postgresql.Driver" | JDBC JAR not found | Verify with `docker exec weather-spark ls /opt/bitnami/spark/jars/postgresql*`; JAR is downloaded in Dockerfile |
| "ModuleNotFoundError: No module named 'config'" | PYTHONPATH not set | Ensure `PYTHONPATH=/app` in Dockerfile and `working_dir: /app` in docker-compose.yml |
| "No data to process" | weather_data table is empty | Reset: `docker-compose down -v && docker-compose up -d` |
| Spark job hangs or OOM | Insufficient memory | Increase `spark.driver.memory` and `spark.executor.memory` in `config/spark_config.py`; use `--start-date`/`--end-date` to process smaller batches |

### Flask API Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| 503 "Database connection failed" | Flask cannot reach TimescaleDB | Verify TimescaleDB is healthy: `docker-compose ps`; check TIMESCALE_HOST=timescaledb in container |
| Swagger UI not loading at /docs | Route misconfigured | Access directly at `http://localhost:5000/docs`; also available via port 3000 through nginx proxy |
| CORS errors in browser console | Frontend origin not allowed | Verify `CORS_ORIGINS` includes `http://localhost:3000` in docker-compose.yml |
| 429 "Rate limit exceeded" | More than 100 requests in 60 seconds | Wait 60 seconds; or increase RATE_LIMIT constant in `src/webapp/app.py` |
| Stale data in responses | TTL cache holding old values | Cache auto-expires (60-300s); restart Flask container to clear immediately |

### React Frontend Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| Blank page or "Cannot GET /" | Build failed in Docker | Check build logs: `docker-compose logs react-frontend`; ensure `npm run build` completed |
| API calls return 502 Bad Gateway | Flask API container is not running | Run `docker-compose ps` and verify `weather-flask-api` is up |
| Stale data in dashboard | Browser or API caching | Clear browser cache; API TTL caching auto-expires in 60-300 seconds |

### Test Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| "ModuleNotFoundError: No module named 'config.database'" | Wrong working directory or missing __init__.py | Run pytest from project root: `cd C:\Project\weather-data-pipeline && pytest tests/ -v` |
| Tests fail after code changes | Stale module cache | Delete `__pycache__/` directories and `.pytest_cache/` |
| Import conflicts between Spark config and Flask config | Module shadowing | The conftest.py handles this; do not run pytest from `tests/` directory directly |

### General Docker Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| "image build failed" | Build context too large or COPY paths wrong | Add `.dockerignore` to exclude `node_modules/`, `pgdata/`, `venv/` |
| Containers restart continuously | Application crash inside container | Check logs: `docker-compose logs <service-name>` |
| Out of disk space | Docker volumes accumulating | Prune unused resources: `docker system prune -a --volumes` |

---

## 18. Next Steps and Recommendations

### Production Readiness

- [ ] **Secrets management** -- Move credentials from `.env` to a proper secrets manager (HashiCorp Vault, AWS Secrets Manager, or Docker Swarm secrets)
- [ ] **Enable compression** -- Uncomment the TimescaleDB compression policy in `001_weather_data.sql` to reduce storage for historical data
- [ ] **Enable retention policy** -- Uncomment the retention policy to auto-drop chunks older than 1 year
- [ ] **Add HTTPS** -- Configure TLS certificates in nginx or use a reverse proxy like Traefik
- [ ] **External rate limiting** -- Replace the in-memory rate limiter with Redis-backed rate limiting for multi-worker deployments
- [ ] **Persistent caching** -- Replace the in-memory TTL cache with Redis for shared caching across Gunicorn workers
- [ ] **Database migrations** -- Implement schema versioning with Alembic or Flyway

### Monitoring and Observability

- [ ] **Health endpoint integration** -- Connect `/health` to external monitoring (Pingdom, UptimeRobot, etc.)
- [ ] **Structured logging** -- Add JSON-formatted logging with correlation IDs across all services
- [ ] **Metrics** -- Add Prometheus metrics endpoint for request latency, error rates, and database pool utilization
- [ ] **Grafana dashboards** -- Create dashboards for service health and pipeline metrics
- [ ] **Alerting** -- Set up alerts for database disconnection, Spark job failures, and API error rate spikes
- [ ] **Distributed tracing** -- Implement OpenTelemetry for cross-service request tracing

### Scaling

- [ ] **Spark cluster mode** -- Change `SPARK_MASTER` from `local[*]` to a standalone or YARN cluster URL
- [ ] **Database replicas** -- Add read replicas for the Flask API to query while Spark writes to the primary
- [ ] **Horizontal API scaling** -- Deploy multiple Flask API instances behind a load balancer
- [ ] **Kubernetes migration** -- Convert Docker Compose to Helm charts for Kubernetes orchestration
- [ ] **Job scheduling** -- Schedule Spark jobs with Apache Airflow or cron

### Data Pipeline Enhancements

- [ ] **Real data ingestion** -- Connect to external weather APIs (OpenWeatherMap, NOAA, Weather.gov)
- [ ] **Streaming ingestion** -- Implement real-time data ingestion with Kafka or Spark Structured Streaming
- [ ] **Data quality monitoring** -- Add Great Expectations or custom validation checks to the pipeline
- [ ] **Backfill support** -- Add idempotent upsert logic for re-processing historical date ranges

### Testing Improvements

- [ ] **Integration tests** -- Add tests with a real database using Docker test containers
- [ ] **Spark job tests** -- Add PySpark unit tests with local SparkSession
- [ ] **React component tests** -- Add Jest and React Testing Library tests
- [ ] **End-to-end tests** -- Add Cypress or Playwright tests for the full user flow
- [ ] **CI/CD pipeline** -- Set up GitHub Actions or GitLab CI for automated testing and deployment

### Frontend Enhancements

- [ ] **Real-time updates** -- Add WebSocket or Server-Sent Events for live data
- [ ] **Weather map** -- Add geographic visualization with Leaflet or Mapbox
- [ ] **Dark mode** -- Add theme toggle support
- [ ] **Data export** -- Add CSV and PDF export functionality
- [ ] **User preferences** -- Persist location selections and display settings

---

*End of Report*
