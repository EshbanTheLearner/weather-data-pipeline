"""Unit tests for the Flask Air Quality API endpoints."""

from datetime import datetime, timezone


class TestCurrentAirQuality:
    def test_current_with_location(self, client, mock_db, sample_air_quality_row):
        mock_db["cursor"].description = [
            ("timestamp",), ("location_id",), ("aqi",), ("aqi_category",),
            ("dominant_pollutant",), ("pm25",), ("pm10",), ("o3",),
            ("no2",), ("so2",), ("co",), ("source",),
        ]
        mock_db["cursor"].fetchone.return_value = sample_air_quality_row
        resp = client.get("/api/air-quality/current?location_id=LOC001")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "success"
        assert body["data"]["location_id"] == "LOC001"
        assert body["data"]["aqi"] == 42

    def test_current_all_locations(self, client, mock_db, sample_air_quality_row):
        mock_db["cursor"].description = [
            ("timestamp",), ("location_id",), ("aqi",), ("aqi_category",),
            ("dominant_pollutant",), ("pm25",), ("pm10",), ("o3",),
            ("no2",), ("so2",), ("co",), ("source",),
        ]
        mock_db["cursor"].fetchall.return_value = [sample_air_quality_row]
        resp = client.get("/api/air-quality/current")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "success"
        assert isinstance(body["data"], list)

    def test_current_not_found(self, client, mock_db):
        mock_db["cursor"].fetchone.return_value = None
        resp = client.get("/api/air-quality/current?location_id=UNKNOWN")
        assert resp.status_code == 404
        body = resp.get_json()
        assert body["status"] == "error"


class TestAirQualityHistorical:
    def test_historical_pagination(self, client, mock_db, sample_air_quality_row):
        mock_db["cursor"].description = [
            ("timestamp",), ("location_id",), ("aqi",), ("aqi_category",),
            ("dominant_pollutant",), ("pm25",), ("pm10",), ("o3",),
            ("no2",), ("so2",), ("co",), ("source",),
        ]
        mock_db["cursor"].fetchone.return_value = (50,)
        mock_db["cursor"].fetchall.return_value = [sample_air_quality_row] * 5
        resp = client.get("/api/air-quality/historical?page=1&per_page=5")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "success"
        assert "pagination" in body
        assert body["pagination"]["page"] == 1
        assert body["pagination"]["per_page"] == 5
        assert body["pagination"]["total"] == 50

    def test_historical_date_filter(self, client, mock_db, sample_air_quality_row):
        mock_db["cursor"].description = [
            ("timestamp",), ("location_id",), ("aqi",), ("aqi_category",),
            ("dominant_pollutant",), ("pm25",), ("pm10",), ("o3",),
            ("no2",), ("so2",), ("co",), ("source",),
        ]
        mock_db["cursor"].fetchone.return_value = (1,)
        mock_db["cursor"].fetchall.return_value = [sample_air_quality_row]
        resp = client.get(
            "/api/air-quality/historical?start=2025-01-01&end=2025-01-31&location_id=LOC001"
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "success"


class TestAirQualityStats:
    def test_stats_daily(self, client, mock_db, sample_aggregated_aq_row):
        mock_db["cursor"].description = [
            ("bucket",), ("location_id",), ("period_type",),
            ("avg_aqi",), ("min_aqi",), ("max_aqi",),
            ("avg_pm25",), ("max_pm25",), ("avg_pm10",), ("max_pm10",),
            ("avg_o3",), ("avg_no2",), ("avg_so2",), ("avg_co",),
            ("dominant_pollutant",), ("sample_count",), ("processed_at",),
        ]
        mock_db["cursor"].fetchall.return_value = [sample_aggregated_aq_row]
        resp = client.get("/api/air-quality/stats?period=daily")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "success"
        assert len(body["data"]) == 1


class TestAirQualityTrends:
    def test_trends_default_7_days(self, client, mock_db):
        row = (
            datetime(2025, 1, 15, 0, 0, 0, tzinfo=timezone.utc),
            "LOC001", 42.0, 65, 8.5, 22.0,
        )
        mock_db["cursor"].description = [
            ("date",), ("location_id",),
            ("avg_aqi",), ("max_aqi",), ("avg_pm25",), ("avg_pm10",),
        ]
        mock_db["cursor"].fetchall.return_value = [row]
        resp = client.get("/api/air-quality/trends?days=7")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "success"
        assert len(body["data"]) == 1
