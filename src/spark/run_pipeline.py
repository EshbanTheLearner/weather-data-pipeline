"""
Weather Data Pipeline Runner.

CLI entry point to run the full Spark pipeline or individual jobs:
    - process   : Clean and validate raw weather data
    - aggregate : Compute hourly averages and daily summaries
    - all       : Run process then aggregate (default)

Usage:
    spark-submit --packages org.postgresql:postgresql:42.7.1 \
        src/spark/run_pipeline.py [all|process|aggregate] \
        [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD]
"""

import argparse
import sys
import time

sys.path.insert(0, ".")
from config.spark_config import get_spark_session


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Weather Data Spark Pipeline Runner"
    )
    parser.add_argument(
        "job",
        nargs="?",
        default="all",
        choices=["all", "process", "aggregate"],
        help="Which job to run (default: all)",
    )
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    start = time.time()
    print(f"{'=' * 60}")
    print(f"  Weather Data Pipeline  –  job={args.job}")
    print(f"  date range: {args.start_date or 'all'} → {args.end_date or 'all'}")
    print(f"{'=' * 60}")

    if args.job in ("all", "process"):
        from src.spark.process_weather import run as run_process

        print("\n>>> Stage 1: Processing raw data")
        run_process(args.start_date, args.end_date)

    if args.job in ("all", "aggregate"):
        from src.spark.aggregate_weather import run as run_aggregate

        print("\n>>> Stage 2: Aggregating data")
        run_aggregate(args.start_date, args.end_date)

    elapsed = time.time() - start
    print(f"\n{'=' * 60}")
    print(f"  Pipeline finished in {elapsed:.1f}s")
    print(f"{'=' * 60}")

    get_spark_session().stop()


if __name__ == "__main__":
    main()
