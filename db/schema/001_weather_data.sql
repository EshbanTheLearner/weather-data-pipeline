-- ============================================================================
-- TimescaleDB Schema for Weather Data Pipeline
-- ============================================================================
-- Purpose: Define the time-series database schema for storing weather metrics
--          including temperature, humidity, pressure, and wind speed data
--          from multiple locations with optimized time-series partitioning.
--
-- Features:
--   - Hypertable with 1-day chunk intervals for efficient time-based queries
--   - Composite primary key for unique location-timestamp pairs
--   - Compression policies for storage optimization
--   - Continuous aggregates for hourly metrics
--   - Retention policies for data lifecycle management
--
-- Best Practices:
--   - Use TIMESTAMPTZ for timezone-aware timestamps
--   - Segment compression by location_id for better compression ratios
--   - Index on (location_id, timestamp DESC) for common query patterns
-- ============================================================================

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ============================================================================
-- Main Weather Data Table
-- ============================================================================
-- Stores raw weather measurements with composite primary key to ensure
-- uniqueness per location and timestamp combination
CREATE TABLE IF NOT EXISTS weather_data (
    timestamp       TIMESTAMPTZ     NOT NULL,
    location_id     VARCHAR(50)     NOT NULL,
    temperature     DOUBLE PRECISION,
    humidity        DOUBLE PRECISION,
    pressure        DOUBLE PRECISION,
    wind_speed      DOUBLE PRECISION,
    PRIMARY KEY (timestamp, location_id)
);

-- ============================================================================
-- Hypertable Configuration
-- ============================================================================
-- Convert the table to a TimescaleDB hypertable with 1-day chunk intervals
-- This optimizes storage and query performance for time-series data
SELECT create_hypertable(
    'weather_data',
    'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- ============================================================================
-- Indexes
-- ============================================================================
-- Composite index on (location_id, timestamp DESC) for efficient queries
-- that filter by location and order by time (most recent first)
CREATE INDEX IF NOT EXISTS idx_weather_data_location_time
    ON weather_data (location_id, timestamp DESC);

-- ============================================================================
-- Compression Policy (Optional)
-- ============================================================================
-- Enable compression to reduce storage footprint for older data
-- Segments are grouped by location_id for better compression ratios
-- Uncomment to enable:
--
-- ALTER TABLE weather_data SET (
--     timescaledb.compress,
--     timescaledb.compress_segmentby = 'location_id'
-- );
--
-- Automatically compress chunks older than 7 days
-- SELECT add_compression_policy('weather_data', INTERVAL '7 days');

-- ============================================================================
-- Continuous Aggregate - Hourly Weather Metrics
-- ============================================================================
-- Pre-compute hourly averages for faster dashboard and reporting queries
-- Automatically maintained as new data arrives
CREATE MATERIALIZED VIEW IF NOT EXISTS weather_data_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', timestamp) AS bucket,
    location_id,
    AVG(temperature) AS avg_temperature,
    AVG(humidity) AS avg_humidity,
    AVG(pressure) AS avg_pressure,
    AVG(wind_speed) AS avg_wind_speed,
    COUNT(*) AS sample_count
FROM weather_data
GROUP BY bucket, location_id
WITH NO DATA;

-- Add refresh policy for continuous aggregate
-- Automatically refresh the last 2 days of data every hour
SELECT add_continuous_aggregate_policy('weather_data_hourly',
    start_offset => INTERVAL '2 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- ============================================================================
-- Retention Policy (Optional)
-- ============================================================================
-- Automatically drop chunks older than 1 year to manage storage
-- Uncomment to enable:
--
-- SELECT add_retention_policy('weather_data', INTERVAL '1 year');

-- ============================================================================
-- Indexes on Continuous Aggregate
-- ============================================================================
-- Index on location_id for the continuous aggregate view
CREATE INDEX IF NOT EXISTS idx_weather_hourly_location
    ON weather_data_hourly (location_id, bucket DESC);

-- ============================================================================
-- Comments for Documentation
-- ============================================================================
COMMENT ON TABLE weather_data IS 'Time-series weather data from multiple locations with 1-day chunk intervals';
COMMENT ON COLUMN weather_data.timestamp IS 'Timestamp of weather measurement (timezone-aware)';
COMMENT ON COLUMN weather_data.location_id IS 'Unique identifier for weather station location';
COMMENT ON COLUMN weather_data.temperature IS 'Temperature measurement (degrees Celsius)';
COMMENT ON COLUMN weather_data.humidity IS 'Relative humidity percentage (0-100)';
COMMENT ON COLUMN weather_data.pressure IS 'Atmospheric pressure (hPa or mbar)';
COMMENT ON COLUMN weather_data.wind_speed IS 'Wind speed (meters per second)';

COMMENT ON MATERIALIZED VIEW weather_data_hourly IS 'Continuous aggregate with hourly averaged weather metrics per location';
