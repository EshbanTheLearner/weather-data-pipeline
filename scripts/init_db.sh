#!/bin/bash
# Reset and reinitialize the database
docker-compose down -v
docker-compose up -d timescaledb
echo "Waiting for TimescaleDB to initialize..."
sleep 10
echo "Database initialized!"
