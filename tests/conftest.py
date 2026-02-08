"""Pytest fixtures for Flask Weather API tests."""

import sys
import os
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest

# Ensure the webapp package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "webapp"))


@pytest.fixture()
def mock_db():
    """Patch the database layer so tests run without a real database."""
    mock_cursor = MagicMock()
    mock_cursor.description = [
        ("timestamp",), ("location_id",), ("temperature",),
        ("humidity",), ("pressure",), ("wind_speed",),
    ]
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []

    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    with patch("config.database.init_pool") as mock_init, \
         patch("config.database.close_pool"), \
         patch("config.database.check_connection", return_value=True), \
         patch("config.database.get_db_connection") as mock_get_conn:

        mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)

        yield {
            "cursor": mock_cursor,
            "conn": mock_conn,
            "init_pool": mock_init,
            "get_conn": mock_get_conn,
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
