---
name: spark_aggregator
description: spark aggregator sub-agent
tools: Read,Write
model: sonnet
---
Create aggregation jobs for weather statistics.

Your task:
1. Create src/spark/aggregate_weather.py:
   - Hourly aggregations (avg, min, max temp)
   - Daily summaries
   - Weekly trends
   - Write to aggregated_weather table

2. Use window functions efficiently
3. Optimize for query performance