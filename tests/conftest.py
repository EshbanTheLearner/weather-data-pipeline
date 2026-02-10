"""Pytest fixtures for Flask Weather API tests."""

import sys
import os
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from contextlib import contextmanager

import pytest

# ---------------------------------------------------------------------------
# Path setup: The Flask app (src/webapp/app.py) does
#     from config.database import check_connection, close_pool, get_db_connection, init_pool
# which resolves to src/webapp/config/database.py when the working directory
# is src/webapp.  However, the project root also has a config/ package (for
# Spark), and when pytest runs from the project root that one shadows the
# webapp config.  We fix this by:
#   1. Inserting the webapp dir at the FRONT of sys.path
#   2. Removing any stale 'config' entry so Python re-resolves it from the
#      webapp directory on the next import.
# ---------------------------------------------------------------------------
_webapp_dir = os.path.join(os.path.dirname(__file__), "..", "src", "webapp")
sys.path.insert(0, os.path.abspath(_webapp_dir))

# Evict any previously-cached 'config' package so the webapp one is found
for _mod_name in list(sys.modules):
    if _mod_name == "config" or _mod_name.startswith("config."):
        del sys.modules[_mod_name]

# Now force-import so that patch() targets the correct module
import config.database  # noqa: E402,F401


@pytest.fixture()
def mock_db():
    """Patch the database layer so tests run without a real database.

    The Flask app uses the pattern:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(...)
                rows = cur.fetchall()

    get_db_connection is a @contextmanager that yields a connection.
    conn.cursor() returns a context manager that yields a cursor.
    We must replicate this nesting exactly.

    Because app.py does `from config.database import get_db_connection`,
    the reference is copied into the app module.  We must patch BOTH the
    canonical location (config.database) AND the imported reference (app).
    """
    mock_cursor = MagicMock()
    mock_cursor.description = [
        ("timestamp",), ("location_id",), ("temperature",),
        ("humidity",), ("pressure",), ("wind_speed",),
    ]
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []

    mock_conn = MagicMock()
    # conn.cursor() must return a context manager yielding the mock_cursor
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    @contextmanager
    def fake_get_db_connection():
        yield mock_conn

    with patch("config.database.init_pool") as mock_init, \
         patch("config.database.close_pool"), \
         patch("config.database.check_connection", return_value=True), \
         patch("config.database.get_db_connection", side_effect=fake_get_db_connection), \
         patch("app.get_db_connection", side_effect=fake_get_db_connection), \
         patch("app.check_connection", return_value=True), \
         patch("app.init_pool") as mock_init2, \
         patch("app.close_pool"):

        yield {
            "cursor": mock_cursor,
            "conn": mock_conn,
            "init_pool": mock_init,
        }


@pytest.fixture()
def app(mock_db):
    """Create a Flask test application with mocked database."""
    from app import app as flask_app
    flask_app.config["TESTING"] = True
    flask_app._pool_ready = True
    return flask_app


@pytest.fixture()
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture()
def sample_weather_row():
    """A single weather_data row as returned by psycopg2."""
    return (
        datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        "LOC001",
        22.5,
        65.0,
        1013.2,
        3.4,
    )


@pytest.fixture()
def sample_aggregated_row():
    """A single aggregated_weather row."""
    return (
        datetime(2025, 1, 15, 0, 0, 0, tzinfo=timezone.utc),  # bucket
        "LOC001",        # location_id
        "daily",         # period_type
        22.5,            # avg_temperature
        18.0,            # min_temperature
        27.0,            # max_temperature
        65.0,            # avg_humidity
        50.0,            # min_humidity
        80.0,            # max_humidity
        1013.2,          # avg_pressure
        3.4,             # avg_wind_speed
        8.2,             # max_wind_speed
        144,             # sample_count
        datetime(2025, 1, 15, 6, 0, 0, tzinfo=timezone.utc),  # processed_at
    )
