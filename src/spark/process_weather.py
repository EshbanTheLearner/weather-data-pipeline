"""
Weather Data Processing Job.

Reads raw weather data from the TimescaleDB `weather_data` table,
performs cleaning and validation, and writes the processed data back.

Usage:
    spark-submit --packages org.postgresql:postgresql:42.7.1 \
        src/spark/process_weather.py [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD]
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType

# Allow running from project root
sys.path.insert(0, ".")
from config.spark_config import JDBC_PROPERTIES, JDBC_URL, get_spark_session

# ---------------------------------------------------------------------------
# Physical-range bounds used for data validation
# ---------------------------------------------------------------------------
VALID_RANGES = {
    "temperature": (-90.0, 60.0),      # Celsius
    "humidity": (0.0, 100.0),           # Percent
    "pressure": (870.0, 1085.0),       # hPa
    "wind_speed": (0.0, 120.0),        # m/s
}


def read_weather_data(
    spark: SparkSession,
    start_date: str | None = None,
    end_date: str | None = None,
) -> DataFrame:
    """Read raw weather data from TimescaleDB.

    Args:
        spark: Active SparkSession.
        start_date: Optional lower bound (inclusive) ISO date string.
        end_date: Optional upper bound (exclusive) ISO date string.

    Returns:
        DataFrame with raw weather records.
    """
    query_parts = ["SELECT * FROM weather_data WHERE 1=1"]

    if start_date:
        query_parts.append(f"AND timestamp >= '{start_date}'")
    if end_date:
        query_parts.append(f"AND timestamp < '{end_date}'")

    query = f"({' '.join(query_parts)}) AS weather_raw"

    df = (
        spark.read.jdbc(
            url=JDBC_URL,
            table=query,
            properties=JDBC_PROPERTIES,
        )
    )
    return df


def clean_weather_data(df: DataFrame) -> DataFrame:
    """Clean and validate weather measurements.

    Steps:
        1. Drop exact duplicate rows.
        2. Clamp metric columns to physically valid ranges.
        3. Forward-fill nulls within each location partition (ordered by time).
    """
    # 1. De-duplicate
    df = df.dropDuplicates(["timestamp", "location_id"])

    # 2. Clamp values to valid physical ranges (set out-of-range to null)
    for col_name, (lo, hi) in VALID_RANGES.items():
        df = df.withColumn(
            col_name,
            F.when(
                F.col(col_name).between(lo, hi),
                F.col(col_name),
            ).otherwise(F.lit(None).cast(DoubleType())),
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
    """Overwrite-append processed weather data back to TimescaleDB."""
    (
        df.write.jdbc(
            url=JDBC_URL,
            table="weather_data",
            mode="append",
            properties=JDBC_PROPERTIES,
        )
    )


def run(start_date: str | None = None, end_date: str | None = None) -> DataFrame:
    """Execute the processing pipeline and return the cleaned DataFrame."""
    spark = get_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    print(f"[process_weather] Reading data  start={start_date}  end={end_date}")
    raw_df = read_weather_data(spark, start_date, end_date)
    raw_count = raw_df.count()
    print(f"[process_weather] Raw records: {raw_count}")

    if raw_count == 0:
        print("[process_weather] No data to process.")
        return raw_df

    cleaned_df = clean_weather_data(raw_df)
    cleaned_count = cleaned_df.count()
    print(f"[process_weather] Cleaned records: {cleaned_count}")

    return cleaned_df


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process raw weather data")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    result = run(args.start_date, args.end_date)
    print(f"[process_weather] Done. Final row count: {result.count()}")
    result.unpersist()
    get_spark_session().stop()
