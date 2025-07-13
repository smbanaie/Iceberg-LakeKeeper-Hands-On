"""
Data transformers for the banking reconciliation system.
"""

from typing import Dict, List, Any

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, expr, when, lit, to_timestamp


class TransactionTransformer:
    """
    Transforms transaction data for reconciliation.
    """
    
    def __init__(self, spark: SparkSession):
        """
        Initialize the transformer with a Spark session.
        
        Args:
            spark: SparkSession instance
        """
        self.spark = spark
    
    def standardize_transaction_data(self, df: DataFrame) -> DataFrame:
        """
        Standardize transaction data by ensuring consistent formats and types.
        
        Args:
            df: DataFrame containing transaction data
            
        Returns:
            Standardized DataFrame
        """
        # Ensure all required columns exist
        required_columns = [
            'transaction_id', 'source_system', 'transaction_date', 
            'amount', 'account_id', 'transaction_type', 
            'reference_id', 'status', 'payload'
        ]
        
        for column in required_columns:
            if column not in df.columns:
                df = df.withColumn(column, lit(None))
        
        # Standardize data types
        df = df.withColumn("amount", col("amount").cast("decimal(18,2)"))
        df = df.withColumn("transaction_date", col("transaction_date").cast("timestamp"))
        
        # Add created_at and processing_timestamp if they don't exist
        if 'created_at' not in df.columns:
            df = df.withColumn("created_at", col("transaction_date"))
        else:
            df = df.withColumn("created_at", col("created_at").cast("timestamp"))
        
        if 'processing_timestamp' not in df.columns:
            df = df.withColumn("processing_timestamp", col("transaction_date"))
        else:
            df = df.withColumn("processing_timestamp", col("processing_timestamp").cast("timestamp"))
        
        # Standardize status values
        df = df.withColumn(
            "status",
            when(col("status").isin(["completed", "COMPLETED", "success", "SUCCESS"]), "completed")
            .when(col("status").isin(["pending", "PENDING", "in_progress", "IN_PROGRESS"]), "pending")
            .when(col("status").isin(["failed", "FAILED", "error", "ERROR"]), "failed")
            .when(col("status").isin(["reversed", "REVERSED", "cancelled", "CANCELLED"]), "reversed")
            .otherwise(col("status"))
        )
        
        return df
    
    def enrich_transaction_data(self, df: DataFrame) -> DataFrame:
        """
        Enrich transaction data with additional information.
        
        Args:
            df: DataFrame containing transaction data
            
        Returns:
            Enriched DataFrame
        """
        # Add a transaction_day column for easier querying
        df = df.withColumn("transaction_day", expr("date(transaction_date)"))
        
        # Add a transaction_month column for aggregation
        df = df.withColumn("transaction_month", expr("date_format(transaction_date, 'yyyy-MM')"))
        
        # Add a processing_lag column (difference between processing and transaction time)
        df = df.withColumn(
            "processing_lag_seconds", 
            expr("unix_timestamp(processing_timestamp) - unix_timestamp(transaction_date)")
        )
        
        return df
    
    def normalize_source_specific_data(self, df: DataFrame, source_system: str) -> DataFrame:
        """
        Apply source-specific normalization rules.
        
        Args:
            df: DataFrame containing transaction data
            source_system: Source system name
            
        Returns:
            Normalized DataFrame
        """
        if source_system == "core_banking":
            # Core banking specific transformations
            pass
        
        elif source_system == "card_processor":
            # Card processor specific transformations
            # For example, card processors might use different status terminology
            df = df.withColumn(
                "status",
                when(col("status") == "authorized", "pending")
                .when(col("status") == "settled", "completed")
                .when(col("status") == "declined", "failed")
                .when(col("status") == "chargeback", "reversed")
                .otherwise(col("status"))
            )
        
        elif source_system == "payment_gateway":
            # Payment gateway specific transformations
            # For example, payment gateways might have different transaction types
            df = df.withColumn(
                "transaction_type",
                when(col("transaction_type") == "charge", "payment")
                .when(col("transaction_type") == "credit", "refund")
                .otherwise(col("transaction_type"))
            )
        
        return df
    
    def prepare_for_reconciliation(
        self, 
        transactions_by_source: Dict[str, DataFrame]
    ) -> Dict[str, DataFrame]:
        """
        Prepare transaction data from multiple sources for reconciliation.
        
        Args:
            transactions_by_source: Dictionary mapping source systems to their transaction DataFrames
            
        Returns:
            Dictionary with prepared DataFrames
        """
        result = {}
        
        for source_system, df in transactions_by_source.items():
            # Apply standardization
            df = self.standardize_transaction_data(df)
            
            # Apply source-specific normalization
            df = self.normalize_source_specific_data(df, source_system)
            
            # Apply enrichment
            df = self.enrich_transaction_data(df)
            
            result[source_system] = df
        
        return result
