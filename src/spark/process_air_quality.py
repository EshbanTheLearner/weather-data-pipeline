"""
Air Quality Data Processing Job.

Reads raw air quality data from the TimescaleDB `air_quality_data` table,
performs cleaning and validation, and writes the processed data back.

Usage:
    spark-submit --packages org.postgresql:postgresql:42.7.1 \
        src/spark/process_air_quality.py [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD]
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, IntegerType

# Allow running from project root
sys.path.insert(0, ".")
from config.spark_config import JDBC_PROPERTIES, JDBC_URL, get_spark_session

# ---------------------------------------------------------------------------
# Physical-range bounds used for data validation
# ---------------------------------------------------------------------------
VALID_RANGES = {
    "pm25": (0.0, 1000.0),
    "pm10": (0.0, 1000.0),
    "o3": (0.0, 600.0),
    "no2": (0.0, 2000.0),
    "so2": (0.0, 1000.0),
    "co": (0.0, 50.0),
    "aqi": (0, 500),
}


def read_air_quality_data(
    spark: SparkSession,
    start_date: str | None = None,
    end_date: str | None = None,
) -> DataFrame:
    """Read raw air quality data from TimescaleDB.

    Args:
        spark: Active SparkSession.
        start_date: Optional lower bound (inclusive) ISO date string.
        end_date: Optional upper bound (exclusive) ISO date string.

    Returns:
        DataFrame with raw air quality records.
    """
    query_parts = ["SELECT * FROM air_quality_data WHERE 1=1"]

    if start_date:
        query_parts.append(f"AND timestamp >= '{start_date}'")
    if end_date:
        query_parts.append(f"AND timestamp < '{end_date}'")

    query = f"({' '.join(query_parts)}) AS air_quality_raw"

    df = (
        spark.read.jdbc(
            url=JDBC_URL,
            table=query,
            properties=JDBC_PROPERTIES,
        )
    )
    return df


def clean_air_quality_data(df: DataFrame) -> DataFrame:
    """Clean and validate air quality measurements.

    Steps:
        1. Drop exact duplicate rows.
        2. Clamp metric columns to physically valid ranges.
        3. Forward-fill nulls within each location partition (ordered by time).
    """
    # 1. De-duplicate
    df = df.dropDuplicates(["timestamp", "location_id"])

    # 2. Clamp values to valid physical ranges (set out-of-range to null)
    for col_name, (lo, hi) in VALID_RANGES.items():
        cast_type = IntegerType() if col_name == "aqi" else DoubleType()
        df = df.withColumn(
            col_name,
            F.when(
                F.col(col_name).between(lo, hi),
                F.col(col_name),
            ).otherwise(F.lit(None).cast(cast_type)),
        )

    # 3. Forward-fill nulls per location (last known observation carried forward)
    from pyspark.sql import Window

    window = Window.partitionBy("location_id").orderBy("timestamp")
    for col_name in VALID_RANGES:
        df = df.withColumn(
            col_name,
            F.coalesce(
                F.col(col_name),
                F.last(F.col(col_name), ignorenulls=True).over(window),
            ),
        )

    return df


def write_processed_data(df: DataFrame) -> None:
    """Overwrite-append processed air quality data back to TimescaleDB."""
    (
        df.write.jdbc(
            url=JDBC_URL,
            table="air_quality_data",
            mode="append",
            properties=JDBC_PROPERTIES,
        )
    )


def run(start_date: str | None = None, end_date: str | None = None) -> DataFrame:
    """Execute the processing pipeline and return the cleaned DataFrame."""
    spark = get_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    print(f"[process_air_quality] Reading data  start={start_date}  end={end_date}")
    raw_df = read_air_quality_data(spark, start_date, end_date)
    raw_count = raw_df.count()
    print(f"[process_air_quality] Raw records: {raw_count}")

    if raw_count == 0:
        print("[process_air_quality] No data to process.")
        return raw_df

    cleaned_df = clean_air_quality_data(raw_df)
    cleaned_count = cleaned_df.count()
    print(f"[process_air_quality] Cleaned records: {cleaned_count}")

    return cleaned_df


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process raw air quality data")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    result = run(args.start_date, args.end_date)
    print(f"[process_air_quality] Done. Final row count: {result.count()}")
    result.unpersist()
    get_spark_session().stop()
