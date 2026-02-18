"""
Air Quality Data Aggregation Job.

Calculates hourly averages and daily summaries from the raw (or cleaned)
air quality data and writes the results to the `aggregated_air_quality` table
in TimescaleDB.

Usage:
    spark-submit --packages org.postgresql:postgresql:42.7.1 \
        src/spark/aggregate_air_quality.py [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD]
"""

import argparse
import sys

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

sys.path.insert(0, ".")
from config.spark_config import JDBC_PROPERTIES, JDBC_URL, get_spark_session
from src.spark.process_air_quality import read_air_quality_data, clean_air_quality_data


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

def compute_hourly_averages(df: DataFrame) -> DataFrame:
    """Compute hourly aggregated statistics per location.

    Metrics per hour per location:
        - avg / min / max AQI
        - avg / max PM2.5
        - avg / max PM10
        - avg O3, NO2, SO2, CO
        - dominant_pollutant (first observed)
        - sample_count
    """
    hourly = (
        df.withColumn(
            "bucket", F.date_trunc("hour", F.col("timestamp"))
        )
        .groupBy("bucket", "location_id")
        .agg(
            F.avg("aqi").alias("avg_aqi"),
            F.min("aqi").alias("min_aqi"),
            F.max("aqi").alias("max_aqi"),
            F.avg("pm25").alias("avg_pm25"),
            F.max("pm25").alias("max_pm25"),
            F.avg("pm10").alias("avg_pm10"),
            F.max("pm10").alias("max_pm10"),
            F.avg("o3").alias("avg_o3"),
            F.avg("no2").alias("avg_no2"),
            F.avg("so2").alias("avg_so2"),
            F.avg("co").alias("avg_co"),
            F.count("*").alias("sample_count"),
            F.first("dominant_pollutant").alias("dominant_pollutant"),
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
            F.avg("aqi").alias("avg_aqi"),
            F.min("aqi").alias("min_aqi"),
            F.max("aqi").alias("max_aqi"),
            F.avg("pm25").alias("avg_pm25"),
            F.max("pm25").alias("max_pm25"),
            F.avg("pm10").alias("avg_pm10"),
            F.max("pm10").alias("max_pm10"),
            F.avg("o3").alias("avg_o3"),
            F.avg("no2").alias("avg_no2"),
            F.avg("so2").alias("avg_so2"),
            F.avg("co").alias("avg_co"),
            F.count("*").alias("sample_count"),
            F.first("dominant_pollutant").alias("dominant_pollutant"),
        )
        .withColumn("period_type", F.lit("daily"))
        .withColumn("processed_at", F.current_timestamp())
    )
    return daily


def write_aggregated(df: DataFrame) -> None:
    """Write aggregated data to the aggregated_air_quality table in TimescaleDB."""
    # Select columns in the order matching the target table
    ordered = df.select(
        "bucket",
        "location_id",
        "period_type",
        "avg_aqi",
        "min_aqi",
        "max_aqi",
        "avg_pm25",
        "max_pm25",
        "avg_pm10",
        "max_pm10",
        "avg_o3",
        "avg_no2",
        "avg_so2",
        "avg_co",
        "dominant_pollutant",
        "sample_count",
        "processed_at",
    )
    (
        ordered.write.jdbc(
            url=JDBC_URL,
            table="aggregated_air_quality",
            mode="append",
            properties=JDBC_PROPERTIES,
        )
    )


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run(start_date: str | None = None, end_date: str | None = None) -> None:
    """Execute the full aggregation pipeline.

    1. Read raw air quality data from TimescaleDB.
    2. Clean / validate measurements.
    3. Compute hourly averages.
    4. Compute daily summaries.
    5. Union both and write to aggregated_air_quality.
    """
    spark = get_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    print(f"[aggregate_air_quality] Reading data  start={start_date}  end={end_date}")
    raw_df = read_air_quality_data(spark, start_date, end_date)
    raw_count = raw_df.count()
    print(f"[aggregate_air_quality] Raw records: {raw_count}")

    if raw_count == 0:
        print("[aggregate_air_quality] No data to aggregate.")
        return

    cleaned_df = clean_air_quality_data(raw_df)
    cleaned_df.cache()

    # Hourly
    hourly_df = compute_hourly_averages(cleaned_df)
    hourly_count = hourly_df.count()
    print(f"[aggregate_air_quality] Hourly buckets: {hourly_count}")

    # Daily
    daily_df = compute_daily_summaries(cleaned_df)
    daily_count = daily_df.count()
    print(f"[aggregate_air_quality] Daily buckets: {daily_count}")

    # Combine and write
    combined_df = hourly_df.unionByName(daily_df)
    write_aggregated(combined_df)
    total = hourly_count + daily_count
    print(f"[aggregate_air_quality] Wrote {total} aggregated rows to aggregated_air_quality")

    cleaned_df.unpersist()


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aggregate air quality data")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    run(args.start_date, args.end_date)
    get_spark_session().stop()
    print("[aggregate_air_quality] Done.")
