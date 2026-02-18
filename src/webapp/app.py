"""
Flask REST API for the Weather Data Pipeline.

Provides endpoints for current weather, historical data, aggregated statistics,
and temperature trends, powered by TimescaleDB.
"""

import math
import os
import time
from datetime import datetime, timedelta, timezone
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_restx import Api, Resource, reqparse

from config.database import check_connection, close_pool, get_db_connection, init_pool

load_dotenv()

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = Flask(__name__)
CORS(app, origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","))

api = Api(
    app,
    version="1.0",
    title="Weather & Air Quality Data API",
    description="REST API for weather and air quality data pipeline - current conditions, "
    "historical data, statistics, trends, and air quality metrics.",
    doc="/docs",
)

weather_ns = api.namespace("api/weather", description="Weather data operations")
locations_ns = api.namespace("api", description="Location operations")
air_quality_ns = api.namespace("api/air-quality", description="Air quality data operations")

# ---------------------------------------------------------------------------
# Simple TTL cache
# ---------------------------------------------------------------------------
_cache: dict = {}


def ttl_cache(seconds: int):
    """Decorator that caches JSON-serialisable return values for *seconds*."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = (fn.__name__, str(request.url))
            now = time.time()
            if key in _cache:
                value, ts = _cache[key]
                if now - ts < seconds:
                    return value
            result = fn(*args, **kwargs)
            _cache[key] = (result, now)
            return result

        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# Simple rate limiter (in-memory, per IP)
# ---------------------------------------------------------------------------
_rate_store: dict = {}
RATE_LIMIT = 100  # requests
RATE_WINDOW = 60  # seconds


@app.before_request
def rate_limit():
    ip = request.remote_addr
    now = time.time()
    window_start = now - RATE_WINDOW
    hits = _rate_store.get(ip, [])
    hits = [t for t in hits if t > window_start]
    if len(hits) >= RATE_LIMIT:
        return jsonify({"status": "error", "message": "Rate limit exceeded"}), 429
    hits.append(now)
    _rate_store[ip] = hits


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------
@app.before_request
def ensure_pool():
    """Lazily initialise the connection pool on first request."""
    if not hasattr(app, "_pool_ready"):
        try:
            init_pool()
            app._pool_ready = True
        except Exception as exc:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Database connection failed: {exc}",
                    }
                ),
                503,
            )


@app.teardown_appcontext
def shutdown_pool(exception=None):
    pass  # pool cleaned up at process exit


import atexit

atexit.register(close_pool)

# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.route("/health")
def health():
    db_ok = False
    try:
        db_ok = check_connection()
    except Exception:
        pass
    status_code = 200 if db_ok else 503
    return (
        jsonify(
            {
                "status": "healthy" if db_ok else "degraded",
                "database": "connected" if db_ok else "disconnected",
            }
        ),
        status_code,
    )


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------
location_parser = reqparse.RequestParser()
location_parser.add_argument("location_id", type=str, location="args")

historical_parser = reqparse.RequestParser()
historical_parser.add_argument("location_id", type=str, location="args")
historical_parser.add_argument("start", type=str, location="args")
historical_parser.add_argument("end", type=str, location="args")
historical_parser.add_argument("page", type=int, default=1, location="args")
historical_parser.add_argument("per_page", type=int, default=20, location="args")

stats_parser = reqparse.RequestParser()
stats_parser.add_argument("location_id", type=str, location="args")
stats_parser.add_argument(
    "period", type=str, default="daily", choices=("hourly", "daily"), location="args"
)

trends_parser = reqparse.RequestParser()
trends_parser.add_argument("location_id", type=str, location="args")
trends_parser.add_argument("days", type=int, default=7, location="args")

aq_location_parser = reqparse.RequestParser()
aq_location_parser.add_argument("location_id", type=str, location="args")

aq_historical_parser = reqparse.RequestParser()
aq_historical_parser.add_argument("location_id", type=str, location="args")
aq_historical_parser.add_argument("start", type=str, location="args")
aq_historical_parser.add_argument("end", type=str, location="args")
aq_historical_parser.add_argument("page", type=int, default=1, location="args")
aq_historical_parser.add_argument("per_page", type=int, default=20, location="args")

aq_stats_parser = reqparse.RequestParser()
aq_stats_parser.add_argument("location_id", type=str, location="args")
aq_stats_parser.add_argument(
    "period", type=str, default="daily", choices=("hourly", "daily"), location="args"
)

aq_trends_parser = reqparse.RequestParser()
aq_trends_parser.add_argument("location_id", type=str, location="args")
aq_trends_parser.add_argument("days", type=int, default=7, location="args")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _row_to_dict(cursor, row):
    """Convert a DB row to a dict using cursor column names."""
    return dict(zip([desc[0] for desc in cursor.description], row))


def _serialize(obj):
    """Make datetime objects JSON-friendly."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


def _rows_to_list(cursor, rows):
    cols = [desc[0] for desc in cursor.description]
    result = []
    for row in rows:
        d = {}
        for col, val in zip(cols, row):
            d[col] = _serialize(val)
        result.append(d)
    return result


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@weather_ns.route("/current")
class CurrentWeather(Resource):
    @weather_ns.expect(location_parser)
    @ttl_cache(60)
    def get(self):
        """Get the latest weather reading for a location (or all locations)."""
        args = location_parser.parse_args()
        location_id = args.get("location_id")

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    if location_id:
                        cur.execute(
                            """SELECT * FROM weather_data
                               WHERE location_id = %s
                               ORDER BY timestamp DESC LIMIT 1""",
                            (location_id,),
                        )
                        row = cur.fetchone()
                        if not row:
                            return {
                                "status": "error",
                                "message": f"No data for location '{location_id}'",
                                "data": None,
                            }, 404
                        data = _row_to_dict(cur, row)
                        data["timestamp"] = _serialize(data["timestamp"])
                    else:
                        cur.execute(
                            """SELECT DISTINCT ON (location_id) *
                               FROM weather_data
                               ORDER BY location_id, timestamp DESC"""
                        )
                        rows = cur.fetchall()
                        data = _rows_to_list(cur, rows)

            return {"status": "success", "data": data}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "data": None}, 500


@weather_ns.route("/historical")
class HistoricalWeather(Resource):
    @weather_ns.expect(historical_parser)
    def get(self):
        """Get paginated historical weather data with optional date range filtering."""
        args = historical_parser.parse_args()
        location_id = args.get("location_id")
        start = args.get("start")
        end = args.get("end")
        page = max(1, args.get("page", 1))
        per_page = min(100, max(1, args.get("per_page", 20)))
        offset = (page - 1) * per_page

        conditions = []
        params = []

        if location_id:
            conditions.append("location_id = %s")
            params.append(location_id)
        if start:
            conditions.append("timestamp >= %s")
            params.append(start)
        if end:
            conditions.append("timestamp <= %s")
            params.append(end)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"SELECT COUNT(*) FROM weather_data {where}", params
                    )
                    total = cur.fetchone()[0]

                    cur.execute(
                        f"""SELECT * FROM weather_data {where}
                            ORDER BY timestamp DESC
                            LIMIT %s OFFSET %s""",
                        params + [per_page, offset],
                    )
                    rows = cur.fetchall()
                    data = _rows_to_list(cur, rows)

            return {
                "status": "success",
                "data": data,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "pages": math.ceil(total / per_page) if total else 0,
                },
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc), "data": []}, 500


@weather_ns.route("/stats")
class WeatherStats(Resource):
    @weather_ns.expect(stats_parser)
    @ttl_cache(300)
    def get(self):
        """Get aggregated weather statistics (hourly or daily) for the last 7 days."""
        args = stats_parser.parse_args()
        location_id = args.get("location_id")
        period = args.get("period", "daily")

        conditions = ["period_type = %s", "bucket >= NOW() - INTERVAL '7 days'"]
        params = [period]

        if location_id:
            conditions.append("location_id = %s")
            params.append(location_id)

        where = "WHERE " + " AND ".join(conditions)

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""SELECT * FROM aggregated_weather {where}
                            ORDER BY bucket DESC""",
                        params,
                    )
                    rows = cur.fetchall()
                    data = _rows_to_list(cur, rows)

            return {"status": "success", "data": data}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "data": []}, 500


@weather_ns.route("/trends")
class WeatherTrends(Resource):
    @weather_ns.expect(trends_parser)
    @ttl_cache(300)
    def get(self):
        """Get daily temperature trends for charting (default: 7 days)."""
        args = trends_parser.parse_args()
        location_id = args.get("location_id")
        days = min(90, max(1, args.get("days", 7)))

        conditions = [
            "period_type = 'daily'",
            "bucket >= NOW() - INTERVAL '%s days'",
        ]
        params: list = [days]

        if location_id:
            conditions.append("location_id = %s")
            params.append(location_id)

        where = "WHERE " + " AND ".join(conditions)

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""SELECT bucket AS date, location_id,
                                   avg_temperature, min_temperature, max_temperature
                            FROM aggregated_weather {where}
                            ORDER BY bucket ASC""",
                        params,
                    )
                    rows = cur.fetchall()
                    data = _rows_to_list(cur, rows)

            return {"status": "success", "data": data}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "data": []}, 500


@locations_ns.route("/locations")
class Locations(Resource):
    @ttl_cache(300)
    def get(self):
        """Get a list of all distinct location IDs."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT DISTINCT location_id FROM weather_data ORDER BY location_id"
                    )
                    rows = cur.fetchall()
                    data = [{"location_id": row[0]} for row in rows]

            return {"status": "success", "data": data}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "data": []}, 500


# ---------------------------------------------------------------------------
# Air Quality Endpoints
# ---------------------------------------------------------------------------
@air_quality_ns.route("/current")
class CurrentAirQuality(Resource):
    @air_quality_ns.expect(aq_location_parser)
    @ttl_cache(60)
    def get(self):
        """Get the latest air quality reading for a location (or all locations)."""
        args = aq_location_parser.parse_args()
        location_id = args.get("location_id")

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    if location_id:
                        cur.execute(
                            """SELECT * FROM air_quality_data
                               WHERE location_id = %s
                               ORDER BY timestamp DESC LIMIT 1""",
                            (location_id,),
                        )
                        row = cur.fetchone()
                        if not row:
                            return {
                                "status": "error",
                                "message": f"No data for location '{location_id}'",
                                "data": None,
                            }, 404
                        data = _row_to_dict(cur, row)
                        data["timestamp"] = _serialize(data["timestamp"])
                    else:
                        cur.execute(
                            """SELECT DISTINCT ON (location_id) *
                               FROM air_quality_data
                               ORDER BY location_id, timestamp DESC"""
                        )
                        rows = cur.fetchall()
                        data = _rows_to_list(cur, rows)

            return {"status": "success", "data": data}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "data": None}, 500


@air_quality_ns.route("/historical")
class HistoricalAirQuality(Resource):
    @air_quality_ns.expect(aq_historical_parser)
    def get(self):
        """Get paginated historical air quality data with optional date range filtering."""
        args = aq_historical_parser.parse_args()
        location_id = args.get("location_id")
        start = args.get("start")
        end = args.get("end")
        page = max(1, args.get("page", 1))
        per_page = min(100, max(1, args.get("per_page", 20)))
        offset = (page - 1) * per_page

        conditions = []
        params = []

        if location_id:
            conditions.append("location_id = %s")
            params.append(location_id)
        if start:
            conditions.append("timestamp >= %s")
            params.append(start)
        if end:
            conditions.append("timestamp <= %s")
            params.append(end)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"SELECT COUNT(*) FROM air_quality_data {where}", params
                    )
                    total = cur.fetchone()[0]

                    cur.execute(
                        f"""SELECT * FROM air_quality_data {where}
                            ORDER BY timestamp DESC
                            LIMIT %s OFFSET %s""",
                        params + [per_page, offset],
                    )
                    rows = cur.fetchall()
                    data = _rows_to_list(cur, rows)

            return {
                "status": "success",
                "data": data,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "pages": math.ceil(total / per_page) if total else 0,
                },
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc), "data": []}, 500


@air_quality_ns.route("/stats")
class AirQualityStats(Resource):
    @air_quality_ns.expect(aq_stats_parser)
    @ttl_cache(300)
    def get(self):
        """Get aggregated air quality statistics (hourly or daily) for the last 7 days."""
        args = aq_stats_parser.parse_args()
        location_id = args.get("location_id")
        period = args.get("period", "daily")

        conditions = ["period_type = %s", "bucket >= NOW() - INTERVAL '7 days'"]
        params = [period]

        if location_id:
            conditions.append("location_id = %s")
            params.append(location_id)

        where = "WHERE " + " AND ".join(conditions)

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""SELECT * FROM aggregated_air_quality {where}
                            ORDER BY bucket DESC""",
                        params,
                    )
                    rows = cur.fetchall()
                    data = _rows_to_list(cur, rows)

            return {"status": "success", "data": data}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "data": []}, 500


@air_quality_ns.route("/trends")
class AirQualityTrends(Resource):
    @air_quality_ns.expect(aq_trends_parser)
    @ttl_cache(300)
    def get(self):
        """Get daily AQI trends for charting (default: 7 days)."""
        args = aq_trends_parser.parse_args()
        location_id = args.get("location_id")
        days = min(90, max(1, args.get("days", 7)))

        conditions = [
            "period_type = 'daily'",
            "bucket >= NOW() - INTERVAL '%s days'",
        ]
        params: list = [days]

        if location_id:
            conditions.append("location_id = %s")
            params.append(location_id)

        where = "WHERE " + " AND ".join(conditions)

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""SELECT bucket AS date, location_id,
                                   avg_aqi, max_aqi, avg_pm25, avg_pm10
                            FROM aggregated_air_quality {where}
                            ORDER BY bucket ASC""",
                        params,
                    )
                    rows = cur.fetchall()
                    data = _rows_to_list(cur, rows)

            return {"status": "success", "data": data}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "data": []}, 500


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return jsonify({"status": "error", "message": "Resource not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"status": "error", "message": "Internal server error"}), 500


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_ENV", "production") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
