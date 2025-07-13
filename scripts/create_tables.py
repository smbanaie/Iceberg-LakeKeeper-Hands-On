#!/usr/bin/env python3
"""
Script to create Iceberg tables for the banking reconciliation system.
"""

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, DecimalType, LongType, ArrayType

def create_spark_session():
    """Create a Spark session with Iceberg configuration."""
    return SparkSession.builder \
        .appName("Banking Reconciliation - Create Tables") \
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

def create_namespace(spark):
    """Create the banking namespace if it doesn't exist."""
    spark.sql("CREATE NAMESPACE IF NOT EXISTS local.banking")
    print("Created namespace: local.banking")

def create_source_transactions_table(spark):
    """Create the source_transactions table."""
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

def create_reconciliation_results_table(spark):
    """Create the reconciliation_results table."""
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

def create_reconciliation_batches_table(spark):
    """Create the reconciliation_batches table."""
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

def initialize_minio_buckets():
    """Initialize MinIO buckets for data storage."""
    import boto3
    from botocore.client import Config
    
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
    existing_buckets = [bucket['Name'] for bucket in s3_client.list_buckets()['Buckets']]
    
    for bucket in buckets:
        if bucket not in existing_buckets:
            s3_client.create_bucket(Bucket=bucket)
            print(f"Created bucket: {bucket}")
        else:
            print(f"Bucket already exists: {bucket}")

def main():
    """Main function to create all tables."""
    print("Initializing Iceberg tables for banking reconciliation...")
    
    # Create Spark session
    spark = create_spark_session()
    
    try:
        # Initialize MinIO buckets
        initialize_minio_buckets()
        
        # Create namespace and tables
        create_namespace(spark)
        create_source_transactions_table(spark)
        create_reconciliation_results_table(spark)
        create_reconciliation_batches_table(spark)
        
        print("Successfully created all Iceberg tables.")
    except Exception as e:
        print(f"Error creating tables: {str(e)}")
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
