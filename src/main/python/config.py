"""
Configuration settings for the banking reconciliation system.
"""

import os
from typing import Dict, Any


class Config:
    """Configuration class for the banking reconciliation system."""
    
    # Spark configuration
    SPARK_CONFIG = {
        "spark.sql.extensions": "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
        "spark.sql.catalog.spark_catalog": "org.apache.iceberg.spark.SparkSessionCatalog",
        "spark.sql.catalog.spark_catalog.type": "hive",
        "spark.sql.catalog.local": "org.apache.iceberg.spark.SparkCatalog",
        "spark.sql.catalog.local.type": "hadoop",
        "spark.sql.catalog.local.warehouse": "s3a://warehouse/",
        "spark.hadoop.fs.s3a.endpoint": "http://minio:9000",
        "spark.hadoop.fs.s3a.access.key": "minio",
        "spark.hadoop.fs.s3a.secret.key": "minio123",
        "spark.hadoop.fs.s3a.path.style.access": "true",
        "spark.hadoop.fs.s3a.impl": "org.apache.hadoop.fs.s3a.S3AFileSystem"
    }
    
    # MinIO configuration
    MINIO_CONFIG = {
        "endpoint": "http://minio:9000",
        "access_key": "minio",
        "secret_key": "minio123",
        "region": "us-east-1"
    }
    
    # PostgreSQL configuration
    POSTGRES_CONFIG = {
        "host": "postgres",
        "port": 5432,
        "database": "iceberg_catalog",
        "user": "iceberg",
        "password": "iceberg"
    }
    
    # Iceberg catalog configuration
    ICEBERG_CATALOG = "local"
    ICEBERG_NAMESPACE = "banking"
    
    # Table names
    SOURCE_TRANSACTIONS_TABLE = f"{ICEBERG_CATALOG}.{ICEBERG_NAMESPACE}.source_transactions"
    RECONCILIATION_RESULTS_TABLE = f"{ICEBERG_CATALOG}.{ICEBERG_NAMESPACE}.reconciliation_results"
    RECONCILIATION_BATCHES_TABLE = f"{ICEBERG_CATALOG}.{ICEBERG_NAMESPACE}.reconciliation_batches"
    
    # Source systems
    SOURCE_SYSTEMS = ["core_banking", "card_processor", "payment_gateway"]
    
    # Reconciliation settings
    DEFAULT_MATCH_STRATEGY = "hybrid"
    AMOUNT_TOLERANCE = 0.01  # 1% tolerance for amount differences
    DATE_TOLERANCE_HOURS = 24  # 24 hours tolerance for date differences
    
    # Data paths
    DATA_DIR = "/opt/spark/data"
    RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
    STAGE_DATA_DIR = os.path.join(DATA_DIR, "stage")
    RECONCILED_DATA_DIR = os.path.join(DATA_DIR, "reconciled")
    
    # S3 buckets
    WAREHOUSE_BUCKET = "warehouse"
    RAW_DATA_BUCKET = "raw-data"
    STAGE_DATA_BUCKET = "stage-data"
    RECONCILED_DATA_BUCKET = "reconciled-data"
    
    @classmethod
    def get_spark_config(cls) -> Dict[str, Any]:
        """Get the Spark configuration."""
        return cls.SPARK_CONFIG
    
    @classmethod
    def get_minio_config(cls) -> Dict[str, Any]:
        """Get the MinIO configuration."""
        return cls.MINIO_CONFIG
    
    @classmethod
    def get_postgres_config(cls) -> Dict[str, Any]:
        """Get the PostgreSQL configuration."""
        return cls.POSTGRES_CONFIG
    
    @classmethod
    def get_source_systems(cls) -> list:
        """Get the list of source systems."""
        return cls.SOURCE_SYSTEMS
    
    @classmethod
    def get_table_name(cls, table_type: str) -> str:
        """
        Get the full table name for a given table type.
        
        Args:
            table_type: Type of table ('source_transactions', 'reconciliation_results', 'reconciliation_batches')
            
        Returns:
            Full table name
        """
        if table_type == "source_transactions":
            return cls.SOURCE_TRANSACTIONS_TABLE
        elif table_type == "reconciliation_results":
            return cls.RECONCILIATION_RESULTS_TABLE
        elif table_type == "reconciliation_batches":
            return cls.RECONCILIATION_BATCHES_TABLE
        else:
            raise ValueError(f"Unknown table type: {table_type}")
    
    @classmethod
    def get_data_dir(cls, data_type: str) -> str:
        """
        Get the directory path for a given data type.
        
        Args:
            data_type: Type of data ('raw', 'stage', 'reconciled')
            
        Returns:
            Directory path
        """
        if data_type == "raw":
            return cls.RAW_DATA_DIR
        elif data_type == "stage":
            return cls.STAGE_DATA_DIR
        elif data_type == "reconciled":
            return cls.RECONCILED_DATA_DIR
        else:
            raise ValueError(f"Unknown data type: {data_type}")
    
    @classmethod
    def get_s3_bucket(cls, bucket_type: str) -> str:
        """
        Get the S3 bucket name for a given bucket type.
        
        Args:
            bucket_type: Type of bucket ('warehouse', 'raw', 'stage', 'reconciled')
            
        Returns:
            Bucket name
        """
        if bucket_type == "warehouse":
            return cls.WAREHOUSE_BUCKET
        elif bucket_type == "raw":
            return cls.RAW_DATA_BUCKET
        elif bucket_type == "stage":
            return cls.STAGE_DATA_BUCKET
        elif bucket_type == "reconciled":
            return cls.RECONCILED_DATA_BUCKET
        else:
            raise ValueError(f"Unknown bucket type: {bucket_type}")
