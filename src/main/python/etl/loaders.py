"""
Data loaders for the banking reconciliation system.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from pyspark.sql import DataFrame, SparkSession


class IcebergLoader:
    """
    Loads data into Iceberg tables.
    """
    
    def __init__(self, spark: SparkSession):
        """
        Initialize the loader with a Spark session.
        
        Args:
            spark: SparkSession instance
        """
        self.spark = spark
    
    def load_transactions(self, df: DataFrame, mode: str = "append") -> None:
        """
        Load transactions into the source_transactions Iceberg table.
        
        Args:
            df: DataFrame containing transaction data
            mode: Write mode ('append', 'overwrite', 'error', 'ignore')
        """
        # Write to Iceberg table
        df.writeTo("local.banking.source_transactions").using("iceberg").append()
        
        print(f"Loaded {df.count()} transactions into source_transactions table")
    
    def load_reconciliation_results(self, df: DataFrame, mode: str = "append") -> None:
        """
        Load reconciliation results into the reconciliation_results Iceberg table.
        
        Args:
            df: DataFrame containing reconciliation results
            mode: Write mode ('append', 'overwrite', 'error', 'ignore')
        """
        # Write to Iceberg table
        df.writeTo("local.banking.reconciliation_results").using("iceberg").append()
        
        print(f"Loaded {df.count()} results into reconciliation_results table")
    
    def load_reconciliation_batch(self, df: DataFrame, mode: str = "append") -> None:
        """
        Load reconciliation batch into the reconciliation_batches Iceberg table.
        
        Args:
            df: DataFrame containing reconciliation batch data
            mode: Write mode ('append', 'overwrite', 'error', 'ignore')
        """
        # Write to Iceberg table
        df.writeTo("local.banking.reconciliation_batches").using("iceberg").append()
        
        print(f"Loaded {df.count()} batches into reconciliation_batches table")
    
    def load_transactions_from_csv(self, file_path: str, mode: str = "append") -> None:
        """
        Load transactions from a CSV file into the source_transactions Iceberg table.
        
        Args:
            file_path: Path to the CSV file
            mode: Write mode ('append', 'overwrite', 'error', 'ignore')
        """
        # Read CSV file
        df = self.spark.read.option("header", "true").csv(file_path)
        
        # Convert string columns to appropriate types
        df = df.withColumn("amount", df["amount"].cast("decimal(18,2)"))
        df = df.withColumn("transaction_date", df["transaction_date"].cast("timestamp"))
        df = df.withColumn("created_at", df["created_at"].cast("timestamp"))
        df = df.withColumn("processing_timestamp", df["processing_timestamp"].cast("timestamp"))
        
        # Load into Iceberg table
        self.load_transactions(df, mode)
    
    def load_transactions_incrementally(
        self, 
        df: DataFrame, 
        source_system: str,
        snapshot_time: Optional[datetime] = None
    ) -> None:
        """
        Load transactions incrementally, handling duplicates.
        
        Args:
            df: DataFrame containing transaction data
            source_system: Source system name
            snapshot_time: Optional snapshot time for time travel
        """
        # Register the DataFrame as a temporary view
        df.createOrReplaceTempView("new_transactions")
        
        # Find existing transaction IDs to avoid duplicates
        if snapshot_time:
            snapshot_time_str = snapshot_time.strftime("%Y-%m-%d %H:%M:%S")
            existing_ids = self.spark.sql(f"""
                SELECT transaction_id
                FROM local.banking.source_transactions
                FOR TIMESTAMP AS OF '{snapshot_time_str}'
                WHERE source_system = '{source_system}'
            """)
        else:
            existing_ids = self.spark.sql(f"""
                SELECT transaction_id
                FROM local.banking.source_transactions
                WHERE source_system = '{source_system}'
            """)
        
        existing_ids.createOrReplaceTempView("existing_transaction_ids")
        
        # Filter out existing transactions
        new_transactions = self.spark.sql("""
            SELECT n.*
            FROM new_transactions n
            LEFT JOIN existing_transaction_ids e
              ON n.transaction_id = e.transaction_id
            WHERE e.transaction_id IS NULL
        """)
        
        # Load new transactions
        if new_transactions.count() > 0:
            self.load_transactions(new_transactions, "append")
            print(f"Loaded {new_transactions.count()} new transactions incrementally")
        else:
            print("No new transactions to load")
    
    def update_schema(self, table_name: str, new_columns: Dict[str, str]) -> None:
        """
        Update the schema of an Iceberg table by adding new columns.
        
        Args:
            table_name: Name of the Iceberg table
            new_columns: Dictionary mapping column names to their data types
        """
        for column_name, data_type in new_columns.items():
            # Add column if it doesn't exist
            self.spark.sql(f"""
                ALTER TABLE local.banking.{table_name}
                ADD COLUMN IF NOT EXISTS {column_name} {data_type}
            """)
            
            print(f"Added column {column_name} ({data_type}) to {table_name}")
    
    def update_partition_spec(self, table_name: str, partition_spec: str) -> None:
        """
        Update the partition specification of an Iceberg table.
        
        Args:
            table_name: Name of the Iceberg table
            partition_spec: Partition specification (e.g., "days(transaction_date)")
        """
        self.spark.sql(f"""
            ALTER TABLE local.banking.{table_name}
            REPLACE PARTITION FIELD {partition_spec}
        """)
        
        print(f"Updated partition spec for {table_name} to {partition_spec}")
    
    def compact_data_files(self, table_name: str) -> None:
        """
        Compact small data files in an Iceberg table.
        
        Args:
            table_name: Name of the Iceberg table
        """
        self.spark.sql(f"""
            CALL local.system.rewrite_data_files(
                table => 'local.banking.{table_name}',
                options => map('min-input-files','5', 'target-file-size-bytes', '104857600')
            )
        """)
        
        print(f"Compacted data files for {table_name}")
    
    def expire_snapshots(self, table_name: str, older_than: str) -> None:
        """
        Expire old snapshots to reclaim storage space.
        
        Args:
            table_name: Name of the Iceberg table
            older_than: Timestamp for expiring snapshots (e.g., '7d' for 7 days)
        """
        self.spark.sql(f"""
            CALL local.system.expire_snapshots(
                table => 'local.banking.{table_name}',
                older_than => '{older_than}'
            )
        """)
        
        print(f"Expired snapshots older than {older_than} for {table_name}")
