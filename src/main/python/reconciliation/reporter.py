"""
Reporting functionality for the banking reconciliation system.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, count, sum, when, lit, current_timestamp


class ReconciliationReporter:
    """
    Generates reports for reconciliation results.
    """
    
    def __init__(self, spark: SparkSession):
        """
        Initialize the reporter with a Spark session.
        
        Args:
            spark: SparkSession instance
        """
        self.spark = spark
    
    def generate_summary_report(self, results_df: DataFrame) -> DataFrame:
        """
        Generate a summary report of reconciliation results.
        
        Args:
            results_df: DataFrame containing reconciliation results
            
        Returns:
            DataFrame containing the summary report
        """
        summary = results_df.groupBy("batch_id", "match_status").agg(
            count("*").alias("count"),
            sum(when(col("discrepancy_amount").isNotNull(), col("discrepancy_amount")).otherwise(0)).alias("total_discrepancy_amount")
        )
        
        return summary
    
    def generate_discrepancy_report(self, results_df: DataFrame) -> DataFrame:
        """
        Generate a report of discrepancies found during reconciliation.
        
        Args:
            results_df: DataFrame containing reconciliation results
            
        Returns:
            DataFrame containing the discrepancy report
        """
        discrepancies = results_df.filter(
            (col("match_status") == "PARTIAL") | (col("match_status") == "UNMATCHED")
        ).select(
            "reconciliation_id",
            "batch_id",
            "primary_transaction_id",
            "secondary_transaction_id",
            "match_status",
            "discrepancy_type",
            "discrepancy_amount",
            "reconciliation_timestamp",
            "notes"
        )
        
        return discrepancies
    
    def generate_batch_report(self, batch_df: DataFrame, results_df: DataFrame) -> DataFrame:
        """
        Generate a report for reconciliation batches.
        
        Args:
            batch_df: DataFrame containing reconciliation batches
            results_df: DataFrame containing reconciliation results
            
        Returns:
            DataFrame containing the batch report
        """
        # Calculate statistics for each batch
        batch_stats = results_df.groupBy("batch_id").agg(
            count("*").alias("total_transactions"),
            count(when(col("match_status") == "MATCHED", 1)).alias("matched_count"),
            count(when(col("match_status") == "PARTIAL", 1)).alias("partial_count"),
            count(when(col("match_status") == "UNMATCHED", 1)).alias("unmatched_count"),
            sum(when(col("discrepancy_amount").isNotNull(), col("discrepancy_amount")).otherwise(0)).alias("total_discrepancy_amount")
        )
        
        # Join with batch information
        batch_report = batch_df.join(
            batch_stats,
            "batch_id",
            "left"
        )
        
        return batch_report
    
    def generate_time_series_report(
        self, 
        results_df: DataFrame, 
        interval: str = "day"
    ) -> DataFrame:
        """
        Generate a time series report of reconciliation results.
        
        Args:
            results_df: DataFrame containing reconciliation results
            interval: Time interval for grouping ('day', 'week', 'month')
            
        Returns:
            DataFrame containing the time series report
        """
        # Create a date column based on the reconciliation timestamp
        if interval == "day":
            date_expr = "date(reconciliation_timestamp)"
        elif interval == "week":
            date_expr = "date_trunc('week', reconciliation_timestamp)"
        elif interval == "month":
            date_expr = "date_trunc('month', reconciliation_timestamp)"
        else:
            raise ValueError(f"Invalid interval: {interval}")
        
        time_series = results_df.withColumn("period", expr(date_expr)).groupBy(
            "period", "match_status"
        ).agg(
            count("*").alias("count"),
            sum(when(col("discrepancy_amount").isNotNull(), col("discrepancy_amount")).otherwise(0)).alias("total_discrepancy_amount")
        ).orderBy("period", "match_status")
        
        return time_series
    
    def generate_source_system_report(self, results_df: DataFrame, batch_df: DataFrame) -> DataFrame:
        """
        Generate a report comparing reconciliation results across source systems.
        
        Args:
            results_df: DataFrame containing reconciliation results
            batch_df: DataFrame containing reconciliation batches
            
        Returns:
            DataFrame containing the source system report
        """
        # Join results with batch information to get source systems
        joined_df = results_df.join(
            batch_df.select("batch_id", "source_systems"),
            "batch_id",
            "inner"
        )
        
        # Explode the source_systems array to get individual source systems
        exploded_df = joined_df.withColumn("source_system", explode("source_systems"))
        
        # Group by source system and match status
        source_report = exploded_df.groupBy("source_system", "match_status").agg(
            count("*").alias("count"),
            sum(when(col("discrepancy_amount").isNotNull(), col("discrepancy_amount")).otherwise(0)).alias("total_discrepancy_amount")
        ).orderBy("source_system", "match_status")
        
        return source_report
    
    def save_report_to_iceberg(
        self, 
        report_df: DataFrame, 
        table_name: str, 
        mode: str = "append"
    ) -> None:
        """
        Save a report to an Iceberg table.
        
        Args:
            report_df: DataFrame containing the report
            table_name: Name of the Iceberg table
            mode: Write mode ('append', 'overwrite')
        """
        # Add a report_id and timestamp
        report_with_id = report_df.withColumn(
            "report_id", 
            expr("uuid()")
        ).withColumn(
            "report_timestamp",
            current_timestamp()
        )
        
        # Write to Iceberg table
        report_with_id.writeTo(f"local.banking.{table_name}").using("iceberg").append()
        
        print(f"Saved report to {table_name}")
    
    def export_report_to_csv(self, report_df: DataFrame, file_path: str) -> None:
        """
        Export a report to a CSV file.
        
        Args:
            report_df: DataFrame containing the report
            file_path: Path to save the CSV file
        """
        report_df.write.option("header", "true").csv(file_path)
        print(f"Exported report to {file_path}")
    
    def query_historical_report(
        self, 
        table_name: str, 
        as_of_timestamp: Optional[datetime] = None
    ) -> DataFrame:
        """
        Query a historical report using Iceberg time travel.
        
        Args:
            table_name: Name of the Iceberg table
            as_of_timestamp: Optional timestamp for time travel
            
        Returns:
            DataFrame containing the historical report
        """
        if as_of_timestamp:
            timestamp_str = as_of_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            df = self.spark.sql(f"""
                SELECT *
                FROM local.banking.{table_name}
                FOR TIMESTAMP AS OF '{timestamp_str}'
            """)
        else:
            df = self.spark.sql(f"""
                SELECT *
                FROM local.banking.{table_name}
            """)
        
        return df
