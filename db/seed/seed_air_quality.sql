-- ============================================================================
-- Seed Data for Air Quality Pipeline
-- ============================================================================
-- Generates realistic air quality data for 5 locations over the last 7 days.
-- All timestamps are relative to NOW() so the data is always recent.
--
-- Locations (same as weather data):
--   NYC - New York City  (moderate AQI, traffic-driven NO2)
--   LAX - Los Angeles    (higher AQI, ozone issues)
--   CHI - Chicago        (moderate, industrial SO2)
--   MIA - Miami          (good AQI, clean coastal air)
--   SEA - Seattle        (good-moderate, occasional PM2.5 from fires)
-- ============================================================================

-- ============================================================================
-- Raw Air Quality Data (air_quality_data table)
-- ============================================================================
-- Generate 24 hourly readings per day for 7 days = 168 records per location
-- Total: 5 locations x 168 = 840 records

DO $$
DECLARE
    loc RECORD;
    h INTEGER;
    day_offset INTEGER;
    ts TIMESTAMPTZ;
    pm25_val DOUBLE PRECISION;
    pm10_val DOUBLE PRECISION;
    o3_val DOUBLE PRECISION;
    no2_val DOUBLE PRECISION;
    so2_val DOUBLE PRECISION;
    co_val DOUBLE PRECISION;
    aqi_val INTEGER;
    aqi_cat VARCHAR(40);
    dom_poll VARCHAR(10);
    max_sub INTEGER;
    pm25_aqi INTEGER;
    o3_aqi INTEGER;
BEGIN
    FOR loc IN
        SELECT * FROM (VALUES
            ('NYC', 10.0, 25.0, 40.0, 30.0, 8.0,  0.4),
            ('LAX', 14.0, 30.0, 55.0, 25.0, 5.0,  0.5),
            ('CHI', 12.0, 28.0, 35.0, 22.0, 15.0, 0.3),
            ('MIA',  6.0, 15.0, 30.0, 12.0, 3.0,  0.2),
            ('SEA', 15.0, 22.0, 32.0, 18.0, 4.0,  0.3)
        ) AS t(id, base_pm25, base_pm10, base_o3, base_no2, base_so2, base_co)
    LOOP
        FOR day_offset IN 0..6 LOOP
            FOR h IN 0..23 LOOP
                ts := date_trunc('hour', NOW()) - (day_offset || ' days')::INTERVAL + (h || ' hours')::INTERVAL;

                IF ts <= NOW() THEN
                    -- PM2.5: peaks in morning rush (7-9) and evening (17-20)
                    pm25_val := loc.base_pm25
                        + 5.0 * CASE WHEN h BETWEEN 7 AND 9 THEN 1.5
                                     WHEN h BETWEEN 17 AND 20 THEN 1.2
                                     ELSE 0.3 END
                        + (random() * 6.0 - 3.0);
                    pm25_val := GREATEST(1.0, LEAST(80.0, pm25_val));

                    -- PM10: correlated with PM2.5 but higher
                    pm10_val := loc.base_pm10
                        + 8.0 * CASE WHEN h BETWEEN 7 AND 9 THEN 1.3
                                     WHEN h BETWEEN 17 AND 20 THEN 1.1
                                     ELSE 0.4 END
                        + (random() * 10.0 - 5.0);
                    pm10_val := GREATEST(2.0, LEAST(120.0, pm10_val));

                    -- O3: peaks in afternoon with sunlight (12-16)
                    o3_val := loc.base_o3
                        + 20.0 * CASE WHEN h BETWEEN 12 AND 16 THEN 1.5
                                      WHEN h BETWEEN 10 AND 18 THEN 0.8
                                      ELSE 0.2 END
                        + (random() * 10.0 - 5.0);
                    o3_val := GREATEST(5.0, LEAST(120.0, o3_val));

                    -- NO2: peaks during rush hours
                    no2_val := loc.base_no2
                        + 15.0 * CASE WHEN h BETWEEN 7 AND 9 THEN 1.5
                                      WHEN h BETWEEN 17 AND 19 THEN 1.3
                                      ELSE 0.3 END
                        + (random() * 8.0 - 4.0);
                    no2_val := GREATEST(2.0, LEAST(100.0, no2_val));

                    -- SO2: relatively steady with slight industrial peak
                    so2_val := loc.base_so2
                        + 3.0 * CASE WHEN h BETWEEN 8 AND 16 THEN 1.2
                                     ELSE 0.5 END
                        + (random() * 4.0 - 2.0);
                    so2_val := GREATEST(0.5, LEAST(50.0, so2_val));

                    -- CO: rush hour peaks
                    co_val := loc.base_co
                        + 0.3 * CASE WHEN h BETWEEN 7 AND 9 THEN 1.5
                                     WHEN h BETWEEN 17 AND 19 THEN 1.3
                                     ELSE 0.3 END
                        + (random() * 0.2 - 0.1);
                    co_val := GREATEST(0.1, LEAST(5.0, co_val));

                    -- Simplified AQI calculation (PM2.5 dominant)
                    -- PM2.5 AQI: 0-12=Good(0-50), 12.1-35.4=Moderate(51-100), 35.5-55.4=USG(101-150)
                    IF pm25_val <= 12.0 THEN
                        pm25_aqi := (pm25_val / 12.0 * 50)::INTEGER;
                    ELSIF pm25_val <= 35.4 THEN
                        pm25_aqi := (50 + (pm25_val - 12.1) / (35.4 - 12.1) * 49)::INTEGER;
                    ELSE
                        pm25_aqi := (100 + (pm25_val - 35.5) / (55.4 - 35.5) * 49)::INTEGER;
                    END IF;

                    -- O3 AQI: simplified
                    IF o3_val <= 54 THEN
                        o3_aqi := (o3_val / 54.0 * 50)::INTEGER;
                    ELSIF o3_val <= 70 THEN
                        o3_aqi := (50 + (o3_val - 55) / (70 - 55) * 49)::INTEGER;
                    ELSE
                        o3_aqi := (100 + (o3_val - 71) / (85 - 71) * 49)::INTEGER;
                    END IF;

                    -- Overall AQI = max of sub-indices
                    IF pm25_aqi >= o3_aqi THEN
                        aqi_val := pm25_aqi;
                        dom_poll := 'pm25';
                    ELSE
                        aqi_val := o3_aqi;
                        dom_poll := 'o3';
                    END IF;
                    aqi_val := GREATEST(0, LEAST(500, aqi_val));

                    -- Category
                    IF aqi_val <= 50 THEN aqi_cat := 'Good';
                    ELSIF aqi_val <= 100 THEN aqi_cat := 'Moderate';
                    ELSIF aqi_val <= 150 THEN aqi_cat := 'Unhealthy for Sensitive Groups';
                    ELSIF aqi_val <= 200 THEN aqi_cat := 'Unhealthy';
                    ELSIF aqi_val <= 300 THEN aqi_cat := 'Very Unhealthy';
                    ELSE aqi_cat := 'Hazardous';
                    END IF;

                    INSERT INTO air_quality_data (
                        timestamp, location_id, aqi, aqi_category, dominant_pollutant,
                        pm25, pm10, o3, no2, so2, co, source
                    ) VALUES (
                        ts, loc.id, aqi_val, aqi_cat, dom_poll,
                        ROUND(pm25_val::numeric, 2), ROUND(pm10_val::numeric, 2),
                        ROUND(o3_val::numeric, 2), ROUND(no2_val::numeric, 2),
                        ROUND(so2_val::numeric, 2), ROUND(co_val::numeric, 2),
                        'openaq'
                    )
                    ON CONFLICT (timestamp, location_id) DO NOTHING;
                END IF;
            END LOOP;
        END LOOP;
    END LOOP;
END $$;

-- ============================================================================
-- Aggregated Air Quality Data (aggregated_air_quality table)
-- ============================================================================

-- Hourly aggregations
INSERT INTO aggregated_air_quality (
    bucket, location_id, period_type,
    avg_aqi, min_aqi, max_aqi,
    avg_pm25, max_pm25, avg_pm10, max_pm10,
    avg_o3, avg_no2, avg_so2, avg_co,
    dominant_pollutant, sample_count, processed_at
)
SELECT
    time_bucket('1 hour', timestamp) AS bucket,
    location_id,
    'hourly' AS period_type,
    ROUND(AVG(aqi)::numeric, 2),
    MIN(aqi),
    MAX(aqi),
    ROUND(AVG(pm25)::numeric, 2),
    ROUND(MAX(pm25)::numeric, 2),
    ROUND(AVG(pm10)::numeric, 2),
    ROUND(MAX(pm10)::numeric, 2),
    ROUND(AVG(o3)::numeric, 2),
    ROUND(AVG(no2)::numeric, 2),
    ROUND(AVG(so2)::numeric, 2),
    ROUND(AVG(co)::numeric, 2),
    MODE() WITHIN GROUP (ORDER BY dominant_pollutant),
    COUNT(*)::INTEGER,
    NOW()
FROM air_quality_data
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY bucket, location_id
ON CONFLICT (bucket, location_id, period_type) DO NOTHING;

-- Daily aggregations
INSERT INTO aggregated_air_quality (
    bucket, location_id, period_type,
    avg_aqi, min_aqi, max_aqi,
    avg_pm25, max_pm25, avg_pm10, max_pm10,
    avg_o3, avg_no2, avg_so2, avg_co,
    dominant_pollutant, sample_count, processed_at
)
SELECT
    time_bucket('1 day', timestamp) AS bucket,
    location_id,
    'daily' AS period_type,
    ROUND(AVG(aqi)::numeric, 2),
    MIN(aqi),
    MAX(aqi),
    ROUND(AVG(pm25)::numeric, 2),
    ROUND(MAX(pm25)::numeric, 2),
    ROUND(AVG(pm10)::numeric, 2),
    ROUND(MAX(pm10)::numeric, 2),
    ROUND(AVG(o3)::numeric, 2),
    ROUND(AVG(no2)::numeric, 2),
    ROUND(AVG(so2)::numeric, 2),
    ROUND(AVG(co)::numeric, 2),
    MODE() WITHIN GROUP (ORDER BY dominant_pollutant),
    COUNT(*)::INTEGER,
    NOW()
FROM air_quality_data
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY bucket, location_id
ON CONFLICT (bucket, location_id, period_type) DO NOTHING;

-- ============================================================================
-- Verification
-- ============================================================================
DO $$
DECLARE
    raw_count BIGINT;
    hourly_count BIGINT;
    daily_count BIGINT;
BEGIN
    SELECT COUNT(*) INTO raw_count FROM air_quality_data;
    SELECT COUNT(*) INTO hourly_count FROM aggregated_air_quality WHERE period_type = 'hourly';
    SELECT COUNT(*) INTO daily_count FROM aggregated_air_quality WHERE period_type = 'daily';
    RAISE NOTICE 'Air quality seed complete: % raw records, % hourly aggregates, % daily aggregates',
        raw_count, hourly_count, daily_count;
END $$;
