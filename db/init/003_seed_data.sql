-- ============================================================================
-- Seed Data for Weather Data Pipeline
-- ============================================================================
-- Generates realistic weather data for 5 locations over the last 7 days.
-- All timestamps are relative to NOW() so the data is always recent.
--
-- Locations:
--   NYC - New York City  (temperate, moderate humidity)
--   LAX - Los Angeles    (warm, low humidity)
--   CHI - Chicago        (cold in winter, variable)
--   MIA - Miami          (hot, high humidity)
--   SEA - Seattle        (cool, high humidity)
-- ============================================================================

-- ============================================================================
-- Raw Weather Data (weather_data table)
-- ============================================================================
-- Generate 24 hourly readings per day for 7 days = 168 records per location
-- Total: 5 locations x 168 = 840 records

-- Use a DO block with generate_series to create the data programmatically
DO $$
DECLARE
    loc RECORD;
    h INTEGER;
    day_offset INTEGER;
    ts TIMESTAMPTZ;
    base_temp DOUBLE PRECISION;
    temp_val DOUBLE PRECISION;
    humidity_val DOUBLE PRECISION;
    pressure_val DOUBLE PRECISION;
    wind_val DOUBLE PRECISION;
    -- Diurnal temperature variation amplitude
    diurnal_amp DOUBLE PRECISION;
BEGIN
    -- Loop over each location with its baseline climate characteristics
    FOR loc IN
        SELECT * FROM (VALUES
            ('NYC', 5.0,   60.0, 1015.0, 5.5,  8.0),
            ('LAX', 18.0,  40.0, 1018.0, 3.5,  5.0),
            ('CHI', -2.0,  55.0, 1012.0, 7.0, 10.0),
            ('MIA', 25.0,  78.0, 1014.0, 4.0,  6.0),
            ('SEA', 7.0,   72.0, 1010.0, 4.5,  7.0)
        ) AS t(id, base_temp, base_humidity, base_pressure, base_wind, diurnal)
    LOOP
        FOR day_offset IN 0..6 LOOP
            FOR h IN 0..23 LOOP
                ts := date_trunc('hour', NOW()) - (day_offset || ' days')::INTERVAL + (h || ' hours')::INTERVAL;
                -- Only insert if timestamp is in the past
                IF ts <= NOW() THEN
                    -- Diurnal temperature cycle: coldest at 5 AM, warmest at 3 PM
                    diurnal_amp := loc.diurnal;
                    temp_val := loc.base_temp
                        + diurnal_amp * sin(PI() * (h - 5.0) / 12.0)
                        + (random() * 3.0 - 1.5);

                    -- Humidity inversely correlated with temperature deviation
                    humidity_val := loc.base_humidity
                        - 5.0 * sin(PI() * (h - 5.0) / 12.0)
                        + (random() * 8.0 - 4.0);
                    humidity_val := GREATEST(10.0, LEAST(100.0, humidity_val));

                    -- Pressure with slow daily drift
                    pressure_val := loc.base_pressure
                        + 3.0 * sin(PI() * day_offset / 3.5)
                        + (random() * 2.0 - 1.0);

                    -- Wind speed: higher in afternoon, random gusts
                    wind_val := loc.base_wind
                        + 2.0 * sin(PI() * (h - 6.0) / 12.0)
                        + (random() * 3.0 - 1.0);
                    wind_val := GREATEST(0.0, LEAST(30.0, wind_val));

                    INSERT INTO weather_data (timestamp, location_id, temperature, humidity, pressure, wind_speed)
                    VALUES (ts, loc.id, ROUND(temp_val::numeric, 2), ROUND(humidity_val::numeric, 2),
                            ROUND(pressure_val::numeric, 2), ROUND(wind_val::numeric, 2))
                    ON CONFLICT (timestamp, location_id) DO NOTHING;
                END IF;
            END LOOP;
        END LOOP;
    END LOOP;
END $$;

-- ============================================================================
-- Aggregated Weather Data (aggregated_weather table)
-- ============================================================================

-- Hourly aggregations: compute from the raw data we just inserted
INSERT INTO aggregated_weather (
    bucket, location_id, period_type,
    avg_temperature, min_temperature, max_temperature,
    avg_humidity, min_humidity, max_humidity,
    avg_pressure, avg_wind_speed, max_wind_speed,
    sample_count, processed_at
)
SELECT
    time_bucket('1 hour', timestamp) AS bucket,
    location_id,
    'hourly' AS period_type,
    ROUND(AVG(temperature)::numeric, 2),
    ROUND(MIN(temperature)::numeric, 2),
    ROUND(MAX(temperature)::numeric, 2),
    ROUND(AVG(humidity)::numeric, 2),
    ROUND(MIN(humidity)::numeric, 2),
    ROUND(MAX(humidity)::numeric, 2),
    ROUND(AVG(pressure)::numeric, 2),
    ROUND(AVG(wind_speed)::numeric, 2),
    ROUND(MAX(wind_speed)::numeric, 2),
    COUNT(*)::INTEGER,
    NOW()
FROM weather_data
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY bucket, location_id
ON CONFLICT (bucket, location_id, period_type) DO NOTHING;

-- Daily aggregations: compute from the raw data we just inserted
INSERT INTO aggregated_weather (
    bucket, location_id, period_type,
    avg_temperature, min_temperature, max_temperature,
    avg_humidity, min_humidity, max_humidity,
    avg_pressure, avg_wind_speed, max_wind_speed,
    sample_count, processed_at
)
SELECT
    time_bucket('1 day', timestamp) AS bucket,
    location_id,
    'daily' AS period_type,
    ROUND(AVG(temperature)::numeric, 2),
    ROUND(MIN(temperature)::numeric, 2),
    ROUND(MAX(temperature)::numeric, 2),
    ROUND(AVG(humidity)::numeric, 2),
    ROUND(MIN(humidity)::numeric, 2),
    ROUND(MAX(humidity)::numeric, 2),
    ROUND(AVG(pressure)::numeric, 2),
    ROUND(AVG(wind_speed)::numeric, 2),
    ROUND(MAX(wind_speed)::numeric, 2),
    COUNT(*)::INTEGER,
    NOW()
FROM weather_data
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY bucket, location_id
ON CONFLICT (bucket, location_id, period_type) DO NOTHING;

-- ============================================================================
-- Verification Queries (informational output)
-- ============================================================================
DO $$
DECLARE
    raw_count BIGINT;
    hourly_count BIGINT;
    daily_count BIGINT;
BEGIN
    SELECT COUNT(*) INTO raw_count FROM weather_data;
    SELECT COUNT(*) INTO hourly_count FROM aggregated_weather WHERE period_type = 'hourly';
    SELECT COUNT(*) INTO daily_count FROM aggregated_weather WHERE period_type = 'daily';
    RAISE NOTICE 'Seed complete: % raw records, % hourly aggregates, % daily aggregates',
        raw_count, hourly_count, daily_count;
END $$;
