"""Unit tests for the Flask Weather API endpoints."""

import json
from datetime import datetime, timezone


class TestHealthEndpoint:
    def test_health_returns_200(self, client, mock_db):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"


class TestCurrentWeather:
    def test_current_with_location(self, client, mock_db, sample_weather_row):
        mock_db["cursor"].fetchone.return_value = sample_weather_row
        resp = client.get("/api/weather/current?location_id=LOC001")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "success"
        assert body["data"]["location_id"] == "LOC001"
        assert body["data"]["temperature"] == 22.5

    def test_current_all_locations(self, client, mock_db, sample_weather_row):
        mock_db["cursor"].fetchall.return_value = [sample_weather_row]
        resp = client.get("/api/weather/current")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "success"
        assert isinstance(body["data"], list)

    def test_current_not_found(self, client, mock_db):
        mock_db["cursor"].fetchone.return_value = None
        resp = client.get("/api/weather/current?location_id=UNKNOWN")
        assert resp.status_code == 404
        body = resp.get_json()
        assert body["status"] == "error"


class TestHistoricalWeather:
    def test_historical_pagination(self, client, mock_db, sample_weather_row):
        mock_db["cursor"].fetchone.return_value = (50,)  # count
        mock_db["cursor"].fetchall.return_value = [sample_weather_row] * 5
        resp = client.get("/api/weather/historical?page=1&per_page=5")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "success"
        assert "pagination" in body
        assert body["pagination"]["page"] == 1
        assert body["pagination"]["per_page"] == 5
        assert body["pagination"]["total"] == 50

    def test_historical_date_filter(self, client, mock_db, sample_weather_row):
        mock_db["cursor"].fetchone.return_value = (1,)
        mock_db["cursor"].fetchall.return_value = [sample_weather_row]
        resp = client.get(
            "/api/weather/historical?start=2025-01-01&end=2025-01-31&location_id=LOC001"
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "success"


class TestStatsEndpoint:
    def test_stats_daily(self, client, mock_db, sample_aggregated_row):
        mock_db["cursor"].description = [
            ("bucket",), ("location_id",), ("period_type",),
            ("avg_temperature",), ("min_temperature",), ("max_temperature",),
            ("avg_humidity",), ("min_humidity",), ("max_humidity",),
            ("avg_pressure",), ("avg_wind_speed",), ("max_wind_speed",),
            ("sample_count",), ("processed_at",),
        ]
        mock_db["cursor"].fetchall.return_value = [sample_aggregated_row]
        resp = client.get("/api/weather/stats?period=daily")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "success"
        assert len(body["data"]) == 1


class TestTrendsEndpoint:
    def test_trends_default_7_days(self, client, mock_db):
        row = (
            datetime(2025, 1, 15, 0, 0, 0, tzinfo=timezone.utc),
            "LOC001", 22.5, 18.0, 27.0,
        )
        mock_db["cursor"].description = [
            ("date",), ("location_id",),
            ("avg_temperature",), ("min_temperature",), ("max_temperature",),
        ]
        mock_db["cursor"].fetchall.return_value = [row]
        resp = client.get("/api/weather/trends?days=7")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "success"
        assert len(body["data"]) == 1


class TestLocationsEndpoint:
    def test_locations_list(self, client, mock_db):
        mock_db["cursor"].fetchall.return_value = [("LOC001",), ("LOC002",)]
        resp = client.get("/api/locations")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "success"
        assert len(body["data"]) == 2
        assert body["data"][0]["location_id"] == "LOC001"


class TestErrorHandling:
    def test_404_handler(self, client):
        resp = client.get("/nonexistent")
        assert resp.status_code == 404
        body = resp.get_json()
        assert body["status"] == "error"
