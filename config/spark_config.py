"""
Spark Configuration for Weather Data Pipeline.

Provides Spark session factory and JDBC connection settings
for reading/writing weather data from/to TimescaleDB.
"""

import os

# ---------------------------------------------------------------------------
# TimescaleDB / PostgreSQL JDBC connection settings
# ---------------------------------------------------------------------------
DB_CONFIG = {
    "host": os.getenv("TIMESCALE_HOST", "localhost"),
    "port": os.getenv("TIMESCALE_PORT", "5432"),
    "database": os.getenv("TIMESCALE_DB", "weather_db"),
    "user": os.getenv("TIMESCALE_USER", "weather_user"),
    "password": os.getenv("TIMESCALE_PASSWORD", "weather_pass_2024"),
}

JDBC_URL = (
    f"jdbc:postgresql://{DB_CONFIG['host']}:{DB_CONFIG['port']}"
    f"/{DB_CONFIG['database']}"
)

JDBC_PROPERTIES = {
    "user": DB_CONFIG["user"],
    "password": DB_CONFIG["password"],
    "driver": "org.postgresql.Driver",
}

# ---------------------------------------------------------------------------
# Spark session settings
# ---------------------------------------------------------------------------
SPARK_CONFIG = {
    "spark.app.name": "WeatherDataPipeline",
    "spark.master": os.getenv("SPARK_MASTER", "local[*]"),
    # Memory
    "spark.driver.memory": os.getenv("SPARK_DRIVER_MEMORY", "2g"),
    "spark.executor.memory": os.getenv("SPARK_EXECUTOR_MEMORY", "2g"),
    # JDBC fetch/batch sizes tuned for time-series workloads
    "spark.jdbc.fetchsize": "10000",
    "spark.jdbc.batchsize": "5000",
    # Shuffle partitions – keep low for moderate data volumes
    "spark.sql.shuffle.partitions": os.getenv("SPARK_SHUFFLE_PARTITIONS", "8"),
    # PostgreSQL JDBC driver JAR
    "spark.jars.packages": "org.postgresql:postgresql:42.7.1",
}


def get_spark_session():
    """Create and return a configured SparkSession."""
    from pyspark.sql import SparkSession

    builder = SparkSession.builder
    for key, value in SPARK_CONFIG.items():
        builder = builder.config(key, value)

    return builder.getOrCreate()
