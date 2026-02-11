#!/usr/bin/env bash
# Run the Weather Dashboard webapp
# Usage: ./scripts/run_webapp.sh [docker|dev]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MODE="${1:-docker}"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

case "$MODE" in
    docker)
        echo "Starting webapp services with Docker..."
        cd "$PROJECT_ROOT"
        docker-compose up -d timescaledb flask-api react-frontend
        echo ""
        echo "Services starting:"
        echo "  - TimescaleDB: localhost:${TIMESCALE_PORT:-5432}"
        echo "  - Flask API:   http://localhost:5000"
        echo "  - Swagger:     http://localhost:5000/docs"
        echo "  - Dashboard:   http://localhost:3000"
        echo ""
        echo "Check status: docker-compose ps"
        echo "View logs:    docker-compose logs -f"
        ;;
    dev)
        echo "Starting development servers..."

        # Start Flask dev server in background
        echo "Starting Flask API on port 5000..."
        cd "$PROJECT_ROOT/src/webapp"
        FLASK_ENV=development python app.py &
        FLASK_PID=$!

        # Start React dev server
        echo "Starting React dev server on port 3000..."
        cd "$PROJECT_ROOT/src/webapp/frontend"
        npm start &
        REACT_PID=$!

        echo ""
        echo "Development servers running:"
        echo "  - Flask API:  http://localhost:5000 (PID: $FLASK_PID)"
        echo "  - Dashboard:  http://localhost:3000 (PID: $REACT_PID)"
        echo ""
        echo "Press Ctrl+C to stop both servers."

        # Wait and cleanup on exit
        trap "kill $FLASK_PID $REACT_PID 2>/dev/null; exit" INT TERM
        wait
        ;;
    *)
        echo "Usage: $0 [docker|dev]"
        echo "  docker  - Run with Docker Compose (default)"
        echo "  dev     - Run Flask + React dev servers locally"
        exit 1
        ;;
esac
