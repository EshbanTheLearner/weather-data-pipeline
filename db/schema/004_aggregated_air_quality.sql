-- ============================================================================
-- Aggregated Air Quality Table for Spark-Processed Data
-- ============================================================================
-- Purpose: Store hourly averages and daily summaries produced by Spark jobs.
--          This table is the write target for the PySpark aggregation pipeline
--          and the read source for the Flask/React dashboard.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- Hourly Aggregated Air Quality Data
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS aggregated_air_quality (
    bucket              TIMESTAMPTZ      NOT NULL,
    location_id         VARCHAR(50)      NOT NULL,
    period_type         VARCHAR(10)      NOT NULL DEFAULT 'hourly',
    avg_aqi             DOUBLE PRECISION,
    min_aqi             INTEGER,
    max_aqi             INTEGER,
    avg_pm25            DOUBLE PRECISION,
    max_pm25            DOUBLE PRECISION,
    avg_pm10            DOUBLE PRECISION,
    max_pm10            DOUBLE PRECISION,
    avg_o3              DOUBLE PRECISION,
    avg_no2             DOUBLE PRECISION,
    avg_so2             DOUBLE PRECISION,
    avg_co              DOUBLE PRECISION,
    dominant_pollutant  VARCHAR(10),
    sample_count        INTEGER,
    processed_at        TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
    PRIMARY KEY (bucket, location_id, period_type)
);

-- Convert to hypertable for efficient time-range queries
SELECT create_hypertable(
    'aggregated_air_quality',
    'bucket',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- ---------------------------------------------------------------------------
-- Indexes
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_agg_air_quality_location_bucket
    ON aggregated_air_quality (location_id, bucket DESC);

CREATE INDEX IF NOT EXISTS idx_agg_air_quality_period
    ON aggregated_air_quality (period_type, bucket DESC);

-- ---------------------------------------------------------------------------
-- Comments
-- ---------------------------------------------------------------------------
COMMENT ON TABLE aggregated_air_quality
    IS 'Spark-processed hourly and daily air quality aggregates per location';
COMMENT ON COLUMN aggregated_air_quality.period_type
    IS 'Aggregation period: hourly or daily';
COMMENT ON COLUMN aggregated_air_quality.avg_aqi
    IS 'Average Air Quality Index for the aggregation period';
COMMENT ON COLUMN aggregated_air_quality.dominant_pollutant
    IS 'Most frequently dominant pollutant during the aggregation period';
COMMENT ON COLUMN aggregated_air_quality.sample_count
    IS 'Number of raw measurements included in this aggregate';
