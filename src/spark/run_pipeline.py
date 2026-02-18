"""
Weather & Air Quality Data Pipeline Runner.

CLI entry point to run the full Spark pipeline or individual jobs:
    - process       : Clean and validate raw weather data
    - aggregate     : Compute hourly averages and daily summaries for weather
    - air-process   : Clean and validate raw air quality data
    - air-aggregate : Compute hourly averages and daily summaries for air quality
    - air-all       : Run air-process then air-aggregate
    - all           : Run all jobs (weather + air quality)

Usage:
    spark-submit --packages org.postgresql:postgresql:42.7.1 \
        src/spark/run_pipeline.py [all|process|aggregate|air-process|air-aggregate|air-all] \
        [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD]
"""

import argparse
import sys
import time

sys.path.insert(0, ".")
from config.spark_config import get_spark_session


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Weather & Air Quality Data Spark Pipeline Runner"
    )
    parser.add_argument(
        "job",
        nargs="?",
        default="all",
        choices=["all", "process", "aggregate", "air-process", "air-aggregate", "air-all"],
        help="Which job to run (default: all)",
    )
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    start = time.time()
    print(f"{'=' * 60}")
    print(f"  Weather & Air Quality Data Pipeline  –  job={args.job}")
    print(f"  date range: {args.start_date or 'all'} → {args.end_date or 'all'}")
    print(f"{'=' * 60}")

    if args.job in ("all", "process"):
        from src.spark.process_weather import run as run_process

        print("\n>>> Stage 1: Processing raw weather data")
        run_process(args.start_date, args.end_date)

    if args.job in ("all", "aggregate"):
        from src.spark.aggregate_weather import run as run_aggregate

        print("\n>>> Stage 2: Aggregating weather data")
        run_aggregate(args.start_date, args.end_date)

    if args.job in ("all", "air-all", "air-process"):
        from src.spark.process_air_quality import run as run_air_process

        print("\n>>> Stage 3: Processing raw air quality data")
        run_air_process(args.start_date, args.end_date)

    if args.job in ("all", "air-all", "air-aggregate"):
        from src.spark.aggregate_air_quality import run as run_air_aggregate

        print("\n>>> Stage 4: Aggregating air quality data")
        run_air_aggregate(args.start_date, args.end_date)

    elapsed = time.time() - start
    print(f"\n{'=' * 60}")
    print(f"  Pipeline finished in {elapsed:.1f}s")
    print(f"{'=' * 60}")

    get_spark_session().stop()


if __name__ == "__main__":
    main()
