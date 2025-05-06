#!/usr/bin/env python3
"""
Script to ingest sample data into Iceberg tables.
"""

import os
import glob
from pyspark.sql import SparkSession

# Import project modules
from src.main.python.etl.loaders import IcebergLoader


def create_spark_session():
    """Create a Spark session with Iceberg configuration."""
    return SparkSession.builder \
        .appName("Banking Reconciliation - Data Ingestion") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.iceberg.spark.SparkSessionCatalog") \
        .config("spark.sql.catalog.spark_catalog.type", "hive") \
        .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.local.type", "hadoop") \
        .config("spark.sql.catalog.local.warehouse", "s3a://warehouse/") \
        .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
        .config("spark.hadoop.fs.s3a.access.key", "minio") \
        .config("spark.hadoop.fs.s3a.secret.key", "minio123") \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .getOrCreate()


def ingest_csv_files(spark, data_dir):
    """
    Ingest CSV files into Iceberg tables.

    Args:
        spark: SparkSession instance
        data_dir: Directory containing CSV files
    """
    # Initialize loader
    loader = IcebergLoader(spark)

    # Find all CSV files in the data directory
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))

    for csv_file in csv_files:
        print(f"Ingesting {csv_file}...")
        loader.load_transactions_from_csv(csv_file)


def main():
    """Main function to ingest data."""
    print("Starting data ingestion process...")

    # Create Spark session
    spark = create_spark_session()

    try:
        # Ingest CSV files
        ingest_csv_files(spark, "/opt/bitnami/spark/data/raw")

        print("Data ingestion completed successfully.")
    except Exception as e:
        print(f"Error during data ingestion: {str(e)}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
