---
name: db_connection_config
description: db connection sub-agent
tools: Read,Write
model: sonnet
---
Create Python database connection configuration.

Your task:
1. Create config/database.py with:
   - Connection parameters (host, port, database, user, password)
   - Connection pooling setup
   - Error handling
   - Environment variable support

2. Use psycopg2 for PostgreSQL connection
3. Add TimescaleDB-specific optimizations