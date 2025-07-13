"""
Script to fix the Spark session configuration and initialize the Iceberg environment.
"""

from pyspark.sql import SparkSession
import boto3
from botocore.client import Config
import time

def create_spark_session():
    """Create a Spark session with corrected Iceberg configuration."""
    print("Creating Spark session with corrected configuration...")

    # Stop any existing Spark session
    try:
        SparkSession.builder.getOrCreate().stop()
        print("Stopped existing Spark session")
    except:
        pass

    # Create a new Spark session with the correct configuration
    import os

    # Create warehouse directory if it doesn't exist
    warehouse_dir = "/opt/bitnami/spark/warehouse"
    os.makedirs(warehouse_dir, exist_ok=True)

    spark = SparkSession.builder \
        .appName("Banking Reconciliation Demo") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.iceberg.spark.SparkSessionCatalog") \
        .config("spark.sql.catalog.spark_catalog.type", "hive") \
        .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.local.type", "hadoop") \
        .config("spark.sql.catalog.local.warehouse", f"file://{warehouse_dir}") \
        .config("spark.sql.defaultCatalog", "local") \
        .getOrCreate()

    print("Spark session created successfully")
    return spark

def initialize_minio_buckets():
    """Initialize MinIO buckets for data storage."""
    print("Initializing MinIO buckets...")

    # Initialize MinIO client
    s3_client = boto3.client(
        's3',
        endpoint_url='http://minio:9000',
        aws_access_key_id='minio',
        aws_secret_access_key='minio123',
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'
    )

    # Create buckets if they don't exist
    buckets = ['warehouse', 'raw-data', 'stage-data', 'reconciled-data']

    # List existing buckets
    try:
        existing_buckets = [bucket['Name'] for bucket in s3_client.list_buckets()['Buckets']]
        print(f"Existing buckets: {existing_buckets}")
    except Exception as e:
        print(f"Error listing buckets: {str(e)}")
        print("Waiting for MinIO to be ready...")
        time.sleep(10)  # Wait for MinIO to be ready
        existing_buckets = [bucket['Name'] for bucket in s3_client.list_buckets()['Buckets']]

    # Create missing buckets
    for bucket in buckets:
        if bucket not in existing_buckets:
            try:
                s3_client.create_bucket(Bucket=bucket)
                print(f"Created bucket: {bucket}")
            except Exception as e:
                print(f"Error creating bucket {bucket}: {str(e)}")
        else:
            print(f"Bucket already exists: {bucket}")

def create_iceberg_tables(spark):
    """Create Iceberg tables for the banking reconciliation system."""
    print("Creating Iceberg tables...")

    # Create the banking namespace
    spark.sql("CREATE NAMESPACE IF NOT EXISTS local.banking")
    print("Created namespace: local.banking")

    # Create source_transactions table
    spark.sql("""
    CREATE TABLE IF NOT EXISTS local.banking.source_transactions (
      transaction_id STRING,
      source_system STRING,
      transaction_date TIMESTAMP,
      amount DECIMAL(18,2),
      account_id STRING,
      transaction_type STRING,
      reference_id STRING,
      status STRING,
      payload STRING,
      created_at TIMESTAMP,
      processing_timestamp TIMESTAMP
    )
    USING iceberg
    PARTITIONED BY (days(transaction_date), source_system)
    """)
    print("Created table: local.banking.source_transactions")

    # Create reconciliation_results table
    spark.sql("""
    CREATE TABLE IF NOT EXISTS local.banking.reconciliation_results (
      reconciliation_id STRING,
      batch_id STRING,
      primary_transaction_id STRING,
      secondary_transaction_id STRING,
      match_status STRING,
      discrepancy_type STRING,
      discrepancy_amount DECIMAL(18,2),
      reconciliation_timestamp TIMESTAMP,
      notes STRING
    )
    USING iceberg
    PARTITIONED BY (days(reconciliation_timestamp), match_status)
    """)
    print("Created table: local.banking.reconciliation_results")

    # Create reconciliation_batches table
    spark.sql("""
    CREATE TABLE IF NOT EXISTS local.banking.reconciliation_batches (
      batch_id STRING,
      reconciliation_date TIMESTAMP,
      source_systems ARRAY<STRING>,
      start_date TIMESTAMP,
      end_date TIMESTAMP,
      status STRING,
      total_transactions BIGINT,
      matched_count BIGINT,
      unmatched_count BIGINT,
      created_at TIMESTAMP,
      completed_at TIMESTAMP
    )
    USING iceberg
    """)
    print("Created table: local.banking.reconciliation_batches")

def main():
    """Main function to fix the Spark session and initialize the environment."""
    print("Starting Spark session fix and environment initialization...")

    # Initialize MinIO buckets
    initialize_minio_buckets()

    # Create Spark session with corrected configuration
    spark = create_spark_session()

    try:
        # Create Iceberg tables
        create_iceberg_tables(spark)

        # List tables to verify
        print("\nVerifying tables...")
        tables = spark.sql("SHOW TABLES IN local.banking").collect()
        if tables:
            print("Tables in local.banking namespace:")
            for table in tables:
                print(f"  - {table.tableName}")
        else:
            print("No tables found in local.banking namespace.")

        print("\nSpark session fix and environment initialization completed successfully.")
    except Exception as e:
        print(f"Error during initialization: {str(e)}")
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
