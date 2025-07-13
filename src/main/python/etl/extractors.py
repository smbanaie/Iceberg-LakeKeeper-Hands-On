"""
Data extractors for the banking reconciliation system.
"""

import os
from datetime import datetime
from typing import List, Dict, Any, Optional

import pandas as pd
from pyspark.sql import SparkSession, DataFrame


class TransactionExtractor:
    """
    Extracts transaction data from various source systems.
    """
    
    def __init__(self, spark: SparkSession):
        """
        Initialize the extractor with a Spark session.
        
        Args:
            spark: SparkSession instance
        """
        self.spark = spark
    
    def extract_from_csv(self, file_path: str) -> DataFrame:
        """
        Extract transactions from a CSV file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            DataFrame containing the transactions
        """
        # Read CSV file into a DataFrame
        df = self.spark.read.option("header", "true").csv(file_path)
        
        # Convert string columns to appropriate types
        df = df.withColumn("amount", df["amount"].cast("decimal(18,2)"))
        df = df.withColumn("transaction_date", df["transaction_date"].cast("timestamp"))
        df = df.withColumn("created_at", df["created_at"].cast("timestamp"))
        df = df.withColumn("processing_timestamp", df["processing_timestamp"].cast("timestamp"))
        
        return df
    
    def extract_from_iceberg(
        self, 
        source_system: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> DataFrame:
        """
        Extract transactions from an Iceberg table.
        
        Args:
            source_system: Source system to extract from
            start_date: Start date for filtering transactions
            end_date: End date for filtering transactions
            
        Returns:
            DataFrame containing the transactions
        """
        # Convert dates to strings for SQL query
        start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
        end_date_str = end_date.strftime("%Y-%m-%d %H:%M:%S")
        
        # Query the Iceberg table
        df = self.spark.sql(f"""
            SELECT *
            FROM local.banking.source_transactions
            WHERE source_system = '{source_system}'
              AND transaction_date >= '{start_date_str}'
              AND transaction_date <= '{end_date_str}'
        """)
        
        return df
    
    def extract_from_s3(self, bucket: str, prefix: str, source_system: Optional[str] = None) -> DataFrame:
        """
        Extract transactions from files in an S3 bucket.
        
        Args:
            bucket: S3 bucket name
            prefix: Prefix for S3 objects
            source_system: Optional filter for source system
            
        Returns:
            DataFrame containing the transactions
        """
        # Read data from S3
        path = f"s3a://{bucket}/{prefix}"
        df = self.spark.read.option("header", "true").csv(path)
        
        # Convert string columns to appropriate types
        df = df.withColumn("amount", df["amount"].cast("decimal(18,2)"))
        df = df.withColumn("transaction_date", df["transaction_date"].cast("timestamp"))
        df = df.withColumn("created_at", df["created_at"].cast("timestamp"))
        df = df.withColumn("processing_timestamp", df["processing_timestamp"].cast("timestamp"))
        
        # Filter by source system if provided
        if source_system:
            df = df.filter(df.source_system == source_system)
        
        return df
    
    def extract_transactions_for_reconciliation(
        self, 
        source_systems: List[str], 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, DataFrame]:
        """
        Extract transactions from multiple source systems for reconciliation.
        
        Args:
            source_systems: List of source systems to extract from
            start_date: Start date for filtering transactions
            end_date: End date for filtering transactions
            
        Returns:
            Dictionary mapping source systems to their transaction DataFrames
        """
        result = {}
        
        for source_system in source_systems:
            df = self.extract_from_iceberg(source_system, start_date, end_date)
            result[source_system] = df
        
        return result
