"""
Weather Data Aggregation Job.

Calculates hourly averages and daily summaries from the raw (or cleaned)
weather data and writes the results to the `aggregated_weather` table
in TimescaleDB.

Usage:
    spark-submit --packages org.postgresql:postgresql:42.7.1 \
        src/spark/aggregate_weather.py [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD]
"""

import argparse
import sys

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

sys.path.insert(0, ".")
from config.spark_config import JDBC_PROPERTIES, JDBC_URL, get_spark_session
from src.spark.process_weather import read_weather_data, clean_weather_data


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

def compute_hourly_averages(df: DataFrame) -> DataFrame:
    """Compute hourly aggregated statistics per location.

    Metrics per hour per location:
        - avg / min / max temperature
        - avg / min / max humidity
        - avg pressure
        - avg / max wind_speed
        - sample_count
    """
    hourly = (
        df.withColumn(
            "bucket", F.date_trunc("hour", F.col("timestamp"))
        )
        .groupBy("bucket", "location_id")
        .agg(
            F.avg("temperature").alias("avg_temperature"),
            F.min("temperature").alias("min_temperature"),
            F.max("temperature").alias("max_temperature"),
            F.avg("humidity").alias("avg_humidity"),
            F.min("humidity").alias("min_humidity"),
            F.max("humidity").alias("max_humidity"),
            F.avg("pressure").alias("avg_pressure"),
            F.avg("wind_speed").alias("avg_wind_speed"),
            F.max("wind_speed").alias("max_wind_speed"),
            F.count("*").alias("sample_count"),
        )
        .withColumn("period_type", F.lit("hourly"))
        .withColumn("processed_at", F.current_timestamp())
    )
    return hourly


def compute_daily_summaries(df: DataFrame) -> DataFrame:
    """Compute daily summary statistics per location.

    Same metric set as hourly but bucketed by calendar day.
    """
    daily = (
        df.withColumn(
            "bucket", F.date_trunc("day", F.col("timestamp"))
        )
        .groupBy("bucket", "location_id")
        .agg(
            F.avg("temperature").alias("avg_temperature"),
            F.min("temperature").alias("min_temperature"),
            F.max("temperature").alias("max_temperature"),
            F.avg("humidity").alias("avg_humidity"),
            F.min("humidity").alias("min_humidity"),
            F.max("humidity").alias("max_humidity"),
            F.avg("pressure").alias("avg_pressure"),
            F.avg("wind_speed").alias("avg_wind_speed"),
            F.max("wind_speed").alias("max_wind_speed"),
            F.count("*").alias("sample_count"),
        )
        .withColumn("period_type", F.lit("daily"))
        .withColumn("processed_at", F.current_timestamp())
    )
    return daily


def write_aggregated(df: DataFrame) -> None:
    """Write aggregated data to the aggregated_weather table in TimescaleDB."""
    # Select columns in the order matching the target table
    ordered = df.select(
        "bucket",
        "location_id",
        "period_type",
        "avg_temperature",
        "min_temperature",
        "max_temperature",
        "avg_humidity",
        "min_humidity",
        "max_humidity",
        "avg_pressure",
        "avg_wind_speed",
        "max_wind_speed",
        "sample_count",
        "processed_at",
    )
    (
        ordered.write.jdbc(
            url=JDBC_URL,
            table="aggregated_weather",
            mode="append",
            properties=JDBC_PROPERTIES,
        )
    )


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run(start_date: str | None = None, end_date: str | None = None) -> None:
    """Execute the full aggregation pipeline.

    1. Read raw weather data from TimescaleDB.
    2. Clean / validate measurements.
    3. Compute hourly averages.
    4. Compute daily summaries.
    5. Union both and write to aggregated_weather.
    """
    spark = get_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    print(f"[aggregate] Reading data  start={start_date}  end={end_date}")
    raw_df = read_weather_data(spark, start_date, end_date)
    raw_count = raw_df.count()
    print(f"[aggregate] Raw records: {raw_count}")

    if raw_count == 0:
        print("[aggregate] No data to aggregate.")
        return

    cleaned_df = clean_weather_data(raw_df)
    cleaned_df.cache()

    # Hourly
    hourly_df = compute_hourly_averages(cleaned_df)
    hourly_count = hourly_df.count()
    print(f"[aggregate] Hourly buckets: {hourly_count}")

    # Daily
    daily_df = compute_daily_summaries(cleaned_df)
    daily_count = daily_df.count()
    print(f"[aggregate] Daily buckets: {daily_count}")

    # Combine and write
    combined_df = hourly_df.unionByName(daily_df)
    write_aggregated(combined_df)
    total = hourly_count + daily_count
    print(f"[aggregate] Wrote {total} aggregated rows to aggregated_weather")

    cleaned_df.unpersist()


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aggregate weather data")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    run(args.start_date, args.end_date)
    get_spark_session().stop()
    print("[aggregate] Done.")
