#!/usr/bin/env bash
# Run the Spark weather data pipeline
# Usage: ./scripts/run_spark_pipeline.sh [process|aggregate|all]
#        ./scripts/run_spark_pipeline.sh --docker [process|aggregate|all]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MODE="${1:-all}"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

if [ "$MODE" = "--docker" ]; then
    # Run inside Docker container
    PIPELINE_MODE="${2:-all}"
    echo "Running Spark pipeline in Docker (mode: $PIPELINE_MODE)..."
    docker exec weather-spark spark-submit \
        --packages org.postgresql:postgresql:42.7.1 \
        /app/src/spark/run_pipeline.py "$PIPELINE_MODE"
else
    # Run locally
    echo "Running Spark pipeline locally (mode: $MODE)..."
    cd "$PROJECT_ROOT"
    spark-submit \
        --packages org.postgresql:postgresql:42.7.1 \
        src/spark/run_pipeline.py "$MODE"
fi

echo "Pipeline completed successfully."
