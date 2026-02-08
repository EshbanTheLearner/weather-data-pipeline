---
name: spark_processor
description: spark processor sub-agent
tools: Read,Write
model: sonnet
---
Create PySpark script for weather data processing.

Your task:
1. Create src/spark/process_weather.py:
   - Read from TimescaleDB
   - Data cleaning and validation
   - Temperature unit conversions
   - Missing data handling
   - Write processed data back

2. Use Spark DataFrame API
3. Optimize for time-series data