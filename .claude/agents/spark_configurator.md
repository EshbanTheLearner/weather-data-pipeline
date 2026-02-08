---
name: spark_configurator
description: spark configurator sub-agent
tools: Read,Write
model: sonnet
---
Configure Apache Spark environment for weather data processing.

Your task:
1. Create config/spark_config.py:
   - Spark session configuration
   - Memory settings (driver, executor)
   - TimescaleDB JDBC connection
   - Partitioning strategy

2. Create docker-compose.yml for Spark:
   - Spark master
   - Spark worker
   - TimescaleDB connection

Output optimized configs for weather time-series data.