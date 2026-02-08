# Agent Specifications

## 1. Database Agent (db_agent)

### Purpose
Manage all TimescaleDB operations including schema creation, data ingestion, and migrations.

### Responsibilities
- Create database schema
- Set up hypertables for weather_data
- Write Python scripts for data ingestion
- Configure database connections
- Handle database errors

### Input
- Database requirements (schema design)
- API endpoints for weather data
- Connection credentials

### Output
- Database schema files (.sql)
- Python ingestion scripts
- Connection configuration
- Migration scripts

### Tools Required
- Read: View existing database files
- Write: Create schema and scripts
- Bash: Test database connections, run migrations

### Model
- Claude Sonnet (balanced for DB tasks)

---

## 2. Spark Processing Agent (spark_agent)

### Purpose
Create and manage Apache Spark jobs for data processing and aggregation.

### Responsibilities
- Configure Spark environment
- Create data processing jobs
- Implement aggregation logic (hourly/daily stats)
- Optimize Spark performance
- Handle large-scale data processing

### Input
- Data processing requirements
- Database schema (from db_agent)
- Aggregation specifications

### Output
- Spark job configurations
- PySpark scripts
- Data transformation logic
- Performance optimization configs

### Tools Required
- Read: View existing Spark configs
- Write: Create PySpark scripts
- Bash: Test Spark jobs locally

### Model
- Claude Sonnet (good for data processing logic)

---

## 3. WebApp Agent (webapp_agent)

### Purpose
Build Flask API backend and React frontend dashboard.

### Responsibilities
- Create Flask REST API endpoints
- Implement React dashboard components
- Design data visualization
- Configure API authentication
- Build responsive UI

### Input
- API specifications
- Database schema (from db_agent)
- Processed data format (from spark_agent)

### Output
- Flask application code
- React components
- API documentation
- Frontend build configuration

### Tools Required
- Read: View existing web files
- Write: Create Flask/React code
- Bash: Run development servers, install packages

### Model
- Claude Sonnet (versatile for full-stack)

---

## 4. Master Orchestrator (orchestrator)

### Purpose
Coordinate all agents, manage workflow dependencies, and ensure proper execution order.

### Responsibilities
- Analyze user requirements
- Determine agent execution order
- Delegate tasks to specialized agents
- Validate agent outputs
- Handle errors and retries
- Generate final reports

### Workflow
1. Parse user request
2. Identify which agents are needed
3. Determine dependency order (DB → Spark → WebApp)
4. Execute agents sequentially
5. Validate each agent's output
6. Coordinate inter-agent communication
7. Report final status

### Tools Required
- Read: View all project files
- Write: Create coordination logs
- Bash: Execute validation scripts

### Model
- Claude Opus (complex orchestration logic)