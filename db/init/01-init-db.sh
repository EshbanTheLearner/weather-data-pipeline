#!/bin/bash
# ============================================================================
# Database Initialization Script
# ============================================================================
# Runs schema migrations from db/schema/ then seed data from db/seed/.
# Executed automatically by PostgreSQL's docker-entrypoint-initdb.d on
# first container start.
#
# Canonical source files:
#   /db/schema/*.sql  - Table definitions, hypertables, indexes
#   /db/seed/*.sql    - Seed/sample data
# ============================================================================

set -e

echo "============================================"
echo "  Initializing Weather & Air Quality DB"
echo "============================================"

echo ""
echo ">>> Applying schemas..."
for f in /db/schema/*.sql; do
    echo "  - $(basename "$f")"
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$f" || true
done

echo ""
echo ">>> Loading seed data..."
for f in /db/seed/*.sql; do
    # Skip the run_seed.sh helper script
    case "$f" in *.sql) ;; *) continue ;; esac
    echo "  - $(basename "$f")"
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$f" || true
done

echo ""
echo "============================================"
echo "  Database initialization complete!"
echo "============================================"
