#!/usr/bin/env python3
"""
Script to run the banking reconciliation process.
"""

import os
import uuid
import argparse
from datetime import datetime, timedelta

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, current_timestamp

# Import project modules
from src.main.python.etl.extractors import TransactionExtractor
from src.main.python.etl.transformers import TransactionTransformer
from src.main.python.etl.loaders import IcebergLoader
from src.main.python.reconciliation.matcher import TransactionMatcher
from src.main.python.reconciliation.reporter import ReconciliationReporter


def create_spark_session():
    """Create a Spark session with Iceberg configuration."""
    return SparkSession.builder \
        .appName("Banking Reconciliation") \
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


def register_reconciliation_batch(spark, batch_id, source_systems, start_date, end_date):
    """Register a new reconciliation batch."""
    batch_df = spark.createDataFrame([{
        "batch_id": batch_id,
        "reconciliation_date": datetime.now(),
        "source_systems": source_systems,
        "start_date": start_date,
        "end_date": end_date,
        "status": "PENDING",
        "total_transactions": 0,
        "matched_count": 0,
        "unmatched_count": 0,
        "created_at": datetime.now(),
        "completed_at": None
    }])
    
    # Save to Iceberg table
    loader = IcebergLoader(spark)
    loader.load_reconciliation_batch(batch_df)
    
    print(f"Registered reconciliation batch: {batch_id}")
    return batch_df


def update_batch_status(spark, batch_id, status, matched_count=None, unmatched_count=None):
    """Update the status of a reconciliation batch."""
    # Get the current batch record
    batch_df = spark.sql(f"""
        SELECT *
        FROM local.banking.reconciliation_batches
        WHERE batch_id = '{batch_id}'
    """)
    
    # Create an updated record
    update_dict = {"status": status}
    
    if status == "COMPLETED":
        update_dict["completed_at"] = datetime.now()
    
    if matched_count is not None:
        update_dict["matched_count"] = matched_count
    
    if unmatched_count is not None:
        update_dict["unmatched_count"] = unmatched_count
    
    # Calculate total transactions
    if matched_count is not None and unmatched_count is not None:
        update_dict["total_transactions"] = matched_count + unmatched_count
    
    # Create a new DataFrame with the updates
    updated_batch = batch_df.select(
        *[
            lit(update_dict[col_name]) if col_name in update_dict else batch_df[col_name]
            for col_name in batch_df.columns
        ]
    )
    
    # Delete the old record and insert the new one
    spark.sql(f"""
        DELETE FROM local.banking.reconciliation_batches
        WHERE batch_id = '{batch_id}'
    """)
    
    # Save the updated record
    loader = IcebergLoader(spark)
    loader.load_reconciliation_batch(updated_batch)
    
    print(f"Updated batch status to {status}")


def run_reconciliation(args):
    """Run the reconciliation process."""
    print("Starting banking reconciliation process...")
    
    # Parse date arguments
    if args.start_date:
        start_date = datetime.fromisoformat(args.start_date)
    else:
        start_date = datetime.now() - timedelta(days=7)
    
    if args.end_date:
        end_date = datetime.fromisoformat(args.end_date)
    else:
        end_date = datetime.now()
    
    # Parse source systems
    source_systems = args.source_systems.split(",")
    if len(source_systems) < 2:
        raise ValueError("At least two source systems are required for reconciliation")
    
    # Create Spark session
    spark = create_spark_session()
    
    try:
        # Generate batch ID
        batch_id = f"RECON-{uuid.uuid4().hex[:8]}"
        
        # Register reconciliation batch
        register_reconciliation_batch(spark, batch_id, source_systems, start_date, end_date)
        update_batch_status(spark, batch_id, "IN_PROGRESS")
        
        # Initialize components
        extractor = TransactionExtractor(spark)
        transformer = TransactionTransformer(spark)
        matcher = TransactionMatcher(spark)
        reporter = ReconciliationReporter(spark)
        loader = IcebergLoader(spark)
        
        # Extract transactions from source systems
        print(f"Extracting transactions from {source_systems} between {start_date} and {end_date}...")
        transactions_by_source = extractor.extract_transactions_for_reconciliation(
            source_systems, start_date, end_date
        )
        
        # Transform transactions for reconciliation
        print("Transforming transactions...")
        prepared_transactions = transformer.prepare_for_reconciliation(transactions_by_source)
        
        # Define primary and secondary sources
        primary_source = source_systems[0]
        primary_df = prepared_transactions[primary_source]
        
        # Initialize counters
        total_matched = 0
        total_unmatched = 0
        
        # For each secondary source, reconcile with primary
        for secondary_source in source_systems[1:]:
            secondary_df = prepared_transactions[secondary_source]
            
            print(f"Reconciling {primary_source} with {secondary_source}...")
            
            # Match transactions
            matched_df, unmatched_primary_df, unmatched_secondary_df = matcher.match_transactions(
                primary_df, secondary_df, match_strategy=args.match_strategy
            )
            
            # Create reconciliation results
            results_df = matcher.create_reconciliation_results(
                batch_id,
                matched_df,
                unmatched_primary_df,
                unmatched_secondary_df,
                primary_source,
                secondary_source
            )
            
            # Save reconciliation results
            loader.load_reconciliation_results(results_df)
            
            # Update counters
            matched_count = matched_df.count()
            unmatched_primary_count = unmatched_primary_df.count()
            unmatched_secondary_count = unmatched_secondary_df.count()
            
            total_matched += matched_count
            total_unmatched += (unmatched_primary_count + unmatched_secondary_count)
            
            print(f"Reconciliation results: {matched_count} matched, "
                  f"{unmatched_primary_count} unmatched in {primary_source}, "
                  f"{unmatched_secondary_count} unmatched in {secondary_source}")
        
        # Generate summary report
        print("Generating reconciliation reports...")
        results_df = spark.sql(f"""
            SELECT *
            FROM local.banking.reconciliation_results
            WHERE batch_id = '{batch_id}'
        """)
        
        summary_report = reporter.generate_summary_report(results_df)
        discrepancy_report = reporter.generate_discrepancy_report(results_df)
        
        # Export reports to CSV
        os.makedirs("data/reconciled", exist_ok=True)
        reporter.export_report_to_csv(summary_report, f"data/reconciled/{batch_id}_summary.csv")
        reporter.export_report_to_csv(discrepancy_report, f"data/reconciled/{batch_id}_discrepancies.csv")
        
        # Update batch status
        update_batch_status(
            spark, batch_id, "COMPLETED", 
            matched_count=total_matched, 
            unmatched_count=total_unmatched
        )
        
        print(f"Reconciliation completed successfully. Batch ID: {batch_id}")
        print(f"Total matched: {total_matched}, Total unmatched: {total_unmatched}")
        
    except Exception as e:
        print(f"Error during reconciliation: {str(e)}")
        if 'batch_id' in locals():
            update_batch_status(spark, batch_id, "FAILED")
        raise
    finally:
        spark.stop()


def main():
    """Main function to parse arguments and run reconciliation."""
    parser = argparse.ArgumentParser(description="Run banking reconciliation")
    parser.add_argument(
        "--source-systems",
        default="core_banking,card_processor,payment_gateway",
        help="Comma-separated list of source systems to reconcile"
    )
    parser.add_argument(
        "--start-date",
        help="Start date for reconciliation (ISO format, e.g., 2023-01-01)"
    )
    parser.add_argument(
        "--end-date",
        help="End date for reconciliation (ISO format, e.g., 2023-01-31)"
    )
    parser.add_argument(
        "--match-strategy",
        default="hybrid",
        choices=["exact", "fuzzy", "hybrid"],
        help="Strategy for matching transactions"
    )
    
    args = parser.parse_args()
    run_reconciliation(args)


if __name__ == "__main__":
    main()
