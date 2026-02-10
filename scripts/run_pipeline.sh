#!/bin/bash
# Run the Spark weather data pipeline
docker exec weather-spark spark-submit /app/src/spark/run_pipeline.py all
