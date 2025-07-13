#!/usr/bin/env python3
"""
Script to initialize Iceberg tables for the banking reconciliation system.
"""

import os
from pyspark.sql import SparkSession

def create_spark_session():
    """Create a Spark session with Iceberg configuration."""
    return SparkSession.builder \
        .appName("Iceberg Initialization") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.iceberg.spark.SparkSessionCatalog") \
        .config("spark.sql.catalog.spark_catalog.type", "hive") \
        .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.local.type", "hadoop") \
        .config("spark.sql.catalog.local.warehouse", "s3a://warehouse/iceberg-warehouse/") \
        .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
        .config("spark.hadoop.fs.s3a.access.key", "minio") \
        .config("spark.hadoop.fs.s3a.secret.key", "minio123") \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
        .config("spark.sql.defaultCatalog", "local") \
        .getOrCreate()

def create_banking_namespace(spark):
    """Create the banking namespace."""
    print("Creating banking namespace...")
    spark.sql("CREATE NAMESPACE IF NOT EXISTS local.banking")
    print("Banking namespace created successfully.")

def create_source_transactions_table(spark):
    """Create the source_transactions table."""
    print("Creating source_transactions table...")
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
    print("source_transactions table created successfully.")

def create_reconciliation_results_table(spark):
    """Create the reconciliation_results table."""
    print("Creating reconciliation_results table...")
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
    print("reconciliation_results table created successfully.")

def create_reconciliation_batches_table(spark):
    """Create the reconciliation_batches table."""
    print("Creating reconciliation_batches table...")
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
    print("reconciliation_batches table created successfully.")

def main():
    """Main function to initialize Iceberg tables."""
    print("Initializing Iceberg tables...")
    
    # Create Spark session
    spark = create_spark_session()
    
    try:
        # Create banking namespace
        create_banking_namespace(spark)
        
        # Create tables
        create_source_transactions_table(spark)
        create_reconciliation_results_table(spark)
        create_reconciliation_batches_table(spark)
        
        print("Iceberg tables initialized successfully.")
    except Exception as e:
        print(f"Error initializing Iceberg tables: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
