"""
Database connection pool for the Flask Weather API.

Uses psycopg2 connection pooling with the same environment variables
as the Spark pipeline configuration.
"""

import os
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool

_connection_pool = None

DB_CONFIG = {
    "host": os.getenv("TIMESCALE_HOST", "localhost"),
    "port": os.getenv("TIMESCALE_PORT", "5432"),
    "database": os.getenv("TIMESCALE_DB", "weather_db"),
    "user": os.getenv("TIMESCALE_USER", "weather_user"),
    "password": os.getenv("TIMESCALE_PASSWORD", "weather_pass_2024"),
}


def init_pool(minconn=2, maxconn=10):
    """Initialize the connection pool."""
    global _connection_pool
    _connection_pool = pool.ThreadedConnectionPool(
        minconn,
        maxconn,
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        dbname=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )
    return _connection_pool


def close_pool():
    """Close all connections in the pool."""
    global _connection_pool
    if _connection_pool:
        _connection_pool.closeall()
        _connection_pool = None


@contextmanager
def get_db_connection():
    """Context manager that provides a database connection from the pool."""
    conn = _connection_pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _connection_pool.putconn(conn)


def check_connection():
    """Verify database connectivity. Returns True if healthy."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return True
    except Exception:
        return False
