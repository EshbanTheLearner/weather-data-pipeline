-- ============================================================================
-- TimescaleDB Schema for Air Quality Data Pipeline
-- ============================================================================
-- Purpose: Define the time-series database schema for storing air quality
--          metrics including AQI, particulate matter, ozone, and other
--          pollutant concentrations from multiple locations with optimized
--          time-series partitioning.
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
-- Main Air Quality Data Table
-- ============================================================================
-- Stores raw air quality measurements with composite primary key to ensure
-- uniqueness per location and timestamp combination
CREATE TABLE IF NOT EXISTS air_quality_data (
    timestamp           TIMESTAMPTZ      NOT NULL,
    location_id         VARCHAR(50)      NOT NULL,
    aqi                 INTEGER,
    aqi_category        VARCHAR(40),
    dominant_pollutant  VARCHAR(10),
    pm25                DOUBLE PRECISION,
    pm10                DOUBLE PRECISION,
    o3                  DOUBLE PRECISION,
    no2                 DOUBLE PRECISION,
    so2                 DOUBLE PRECISION,
    co                  DOUBLE PRECISION,
    source              VARCHAR(30)      DEFAULT 'openaq',
    PRIMARY KEY (timestamp, location_id)
);

-- ============================================================================
-- Hypertable Configuration
-- ============================================================================
-- Convert the table to a TimescaleDB hypertable with 1-day chunk intervals
-- This optimizes storage and query performance for time-series data
SELECT create_hypertable(
    'air_quality_data',
    'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- ============================================================================
-- Indexes
-- ============================================================================
-- Composite index on (location_id, timestamp DESC) for efficient queries
-- that filter by location and order by time (most recent first)
CREATE INDEX IF NOT EXISTS idx_air_quality_data_location_time
    ON air_quality_data (location_id, timestamp DESC);

-- ============================================================================
-- Compression Policy (Optional)
-- ============================================================================
-- Enable compression to reduce storage footprint for older data
-- Segments are grouped by location_id for better compression ratios
-- Uncomment to enable:
--
-- ALTER TABLE air_quality_data SET (
--     timescaledb.compress,
--     timescaledb.compress_segmentby = 'location_id'
-- );
--
-- Automatically compress chunks older than 7 days
-- SELECT add_compression_policy('air_quality_data', INTERVAL '7 days');

-- ============================================================================
-- Continuous Aggregate - Hourly Air Quality Metrics
-- ============================================================================
-- Pre-compute hourly averages for faster dashboard and reporting queries
-- Automatically maintained as new data arrives
CREATE MATERIALIZED VIEW IF NOT EXISTS air_quality_data_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', timestamp) AS bucket,
    location_id,
    AVG(aqi) AS avg_aqi,
    MAX(aqi) AS max_aqi,
    AVG(pm25) AS avg_pm25,
    AVG(pm10) AS avg_pm10,
    AVG(o3) AS avg_o3,
    AVG(no2) AS avg_no2,
    AVG(so2) AS avg_so2,
    AVG(co) AS avg_co,
    COUNT(*) AS sample_count
FROM air_quality_data
GROUP BY bucket, location_id
WITH NO DATA;

-- Add refresh policy for continuous aggregate
-- Automatically refresh the last 2 days of data every hour
SELECT add_continuous_aggregate_policy('air_quality_data_hourly',
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
-- SELECT add_retention_policy('air_quality_data', INTERVAL '1 year');

-- ============================================================================
-- Indexes on Continuous Aggregate
-- ============================================================================
-- Index on location_id for the continuous aggregate view
CREATE INDEX IF NOT EXISTS idx_air_quality_hourly_location
    ON air_quality_data_hourly (location_id, bucket DESC);

-- ============================================================================
-- Comments for Documentation
-- ============================================================================
COMMENT ON TABLE air_quality_data IS 'Time-series air quality data from multiple locations with 1-day chunk intervals';
COMMENT ON COLUMN air_quality_data.timestamp IS 'Timestamp of air quality measurement (timezone-aware)';
COMMENT ON COLUMN air_quality_data.location_id IS 'Unique identifier for monitoring station location';
COMMENT ON COLUMN air_quality_data.aqi IS 'Air Quality Index value (0-500 scale)';
COMMENT ON COLUMN air_quality_data.aqi_category IS 'AQI category label (Good, Moderate, Unhealthy for Sensitive Groups, Unhealthy, Very Unhealthy, Hazardous)';
COMMENT ON COLUMN air_quality_data.dominant_pollutant IS 'Primary pollutant driving the AQI value';
COMMENT ON COLUMN air_quality_data.pm25 IS 'Fine particulate matter PM2.5 concentration (micrograms per cubic meter)';
COMMENT ON COLUMN air_quality_data.pm10 IS 'Coarse particulate matter PM10 concentration (micrograms per cubic meter)';
COMMENT ON COLUMN air_quality_data.o3 IS 'Ground-level ozone concentration (parts per billion)';
COMMENT ON COLUMN air_quality_data.no2 IS 'Nitrogen dioxide concentration (parts per billion)';
COMMENT ON COLUMN air_quality_data.so2 IS 'Sulfur dioxide concentration (parts per billion)';
COMMENT ON COLUMN air_quality_data.co IS 'Carbon monoxide concentration (parts per million)';
COMMENT ON COLUMN air_quality_data.source IS 'Data source identifier (default: openaq)';

COMMENT ON MATERIALIZED VIEW air_quality_data_hourly IS 'Continuous aggregate with hourly averaged air quality metrics per location';
