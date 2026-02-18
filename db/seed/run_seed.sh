#!/usr/bin/env bash
# ============================================================================
# Run Seed Data Against TimescaleDB Container
# ============================================================================
# Usage: ./db/seed/run_seed.sh
#
# This script loads the seed data SQL file into the running TimescaleDB
# container. The container must be running and healthy before executing.
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${0}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Load environment variables from .env if it exists
if [ -f "${PROJECT_ROOT}/.env" ]; then
    set -a
    source "${PROJECT_ROOT}/.env"
    set +a
fi

# Default values (fallback if .env is not present)
DB_USER="${POSTGRES_USER:-weather_user}"
DB_NAME="${POSTGRES_DB:-weather_db}"
DB_PASSWORD="${POSTGRES_PASSWORD:-weather_pass_2024}"
CONTAINER_NAME="weather-timescaledb"

echo "Waiting for TimescaleDB container to be healthy..."
RETRIES=30
until docker exec "${CONTAINER_NAME}" pg_isready -U "${DB_USER}" -d "${DB_NAME}" > /dev/null 2>&1; do
    RETRIES=$((RETRIES - 1))
    if [ "${RETRIES}" -le 0 ]; then
        echo "ERROR: TimescaleDB container is not ready after 30 attempts."
        exit 1
    fi
    echo "  Container not ready yet, retrying in 2 seconds... (${RETRIES} attempts left)"
    sleep 2
done

echo "TimescaleDB is ready. Running seed data..."
for SEED_FILE in "${SCRIPT_DIR}"/*.sql; do
    [ -f "${SEED_FILE}" ] || continue
    echo "  Loading: $(basename "${SEED_FILE}")"
    docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}" < "${SEED_FILE}"
done

echo ""
echo "Seed data loaded successfully."
echo "Verifying record counts..."

docker exec "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}" -c \
    "SELECT 'weather_data' AS table_name, COUNT(*) AS record_count FROM weather_data
     UNION ALL
     SELECT 'aggregated_weather (hourly)', COUNT(*) FROM aggregated_weather WHERE period_type = 'hourly'
     UNION ALL
     SELECT 'aggregated_weather (daily)', COUNT(*) FROM aggregated_weather WHERE period_type = 'daily'
     UNION ALL
     SELECT 'air_quality_data', COUNT(*) FROM air_quality_data
     UNION ALL
     SELECT 'aggregated_air_quality (hourly)', COUNT(*) FROM aggregated_air_quality WHERE period_type = 'hourly'
     UNION ALL
     SELECT 'aggregated_air_quality (daily)', COUNT(*) FROM aggregated_air_quality WHERE period_type = 'daily';"

echo ""
echo "Done."
