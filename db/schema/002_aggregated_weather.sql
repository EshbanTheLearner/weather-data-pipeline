-- ============================================================================
-- Aggregated Weather Table for Spark-Processed Data
-- ============================================================================
-- Purpose: Store hourly averages and daily summaries produced by Spark jobs.
--          This table is the write target for the PySpark aggregation pipeline
--          and the read source for the Flask/React dashboard.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- Hourly Aggregated Weather Data
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS aggregated_weather (
    bucket          TIMESTAMPTZ      NOT NULL,
    location_id     VARCHAR(50)      NOT NULL,
    period_type     VARCHAR(10)      NOT NULL DEFAULT 'hourly',
    avg_temperature DOUBLE PRECISION,
    min_temperature DOUBLE PRECISION,
    max_temperature DOUBLE PRECISION,
    avg_humidity    DOUBLE PRECISION,
    min_humidity    DOUBLE PRECISION,
    max_humidity    DOUBLE PRECISION,
    avg_pressure    DOUBLE PRECISION,
    avg_wind_speed  DOUBLE PRECISION,
    max_wind_speed  DOUBLE PRECISION,
    sample_count    INTEGER,
    processed_at    TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
    PRIMARY KEY (bucket, location_id, period_type)
);

-- Convert to hypertable for efficient time-range queries
SELECT create_hypertable(
    'aggregated_weather',
    'bucket',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- ---------------------------------------------------------------------------
-- Indexes
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_agg_weather_location_bucket
    ON aggregated_weather (location_id, bucket DESC);

CREATE INDEX IF NOT EXISTS idx_agg_weather_period
    ON aggregated_weather (period_type, bucket DESC);

-- ---------------------------------------------------------------------------
-- Comments
-- ---------------------------------------------------------------------------
COMMENT ON TABLE aggregated_weather
    IS 'Spark-processed hourly and daily weather aggregates per location';
COMMENT ON COLUMN aggregated_weather.period_type
    IS 'Aggregation period: hourly or daily';
COMMENT ON COLUMN aggregated_weather.sample_count
    IS 'Number of raw measurements included in this aggregate';
