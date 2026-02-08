# Weather Data Pipeline - Project Context

## Project Overview
Multi-agent system for automated weather data management.

## Technology Stack
- **Database**: TimescaleDB (PostgreSQL extension)
- **Processing**: Apache Spark 3.5.0
- **API**: Flask (Python 3.11)
- **Frontend**: React 18 + Node 20
- **Orchestration**: Claude Code Multi-Agent System

## Architecture
```
┌─────────────────────────────────────────┐
│       Master Orchestrator Agent         │
│  (Coordinates workflow & dependencies)  │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  DB Agent   │  │Spark Agent  │  │WebApp Agent │
│ TimescaleDB │  │  Processing │  │ Flask/React │
└─────────────┘  └─────────────┘  └─────────────┘
```

## Agent Responsibilities

### DB Agent
- Create TimescaleDB schemas
- Set up hypertables for time-series data
- Write data ingestion scripts
- Manage database migrations

### Spark Agent
- Configure Spark environment
- Create data processing jobs
- Implement aggregation logic
- Optimize query performance

### WebApp Agent
- Build Flask REST API
- Create React dashboard
- Implement data visualization
- Handle API authentication

### Master Orchestrator
- Coordinate agent execution order
- Manage dependencies (DB → Spark → WebApp)
- Handle errors and retries
- Generate progress reports