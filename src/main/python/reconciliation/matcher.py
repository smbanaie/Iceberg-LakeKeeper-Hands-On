"""
Transaction matching logic for the banking reconciliation system.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Tuple, Optional

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, abs, lit, expr, when


class TransactionMatcher:
    """
    Matches transactions across different source systems.
    """
    
    def __init__(self, spark: SparkSession):
        """
        Initialize the matcher with a Spark session.
        
        Args:
            spark: SparkSession instance
        """
        self.spark = spark
    
    def exact_match(
        self, 
        primary_df: DataFrame, 
        secondary_df: DataFrame
    ) -> Tuple[DataFrame, DataFrame, DataFrame]:
        """
        Perform exact matching between primary and secondary transactions.
        
        Args:
            primary_df: DataFrame containing primary transactions
            secondary_df: DataFrame containing secondary transactions
            
        Returns:
            Tuple of (matched_df, unmatched_primary_df, unmatched_secondary_df)
        """
        # Join on account_id, amount, and transaction_type
        matched_df = primary_df.join(
            secondary_df,
            [
                primary_df.account_id == secondary_df.account_id,
                primary_df.amount == secondary_df.amount,
                primary_df.transaction_type == secondary_df.transaction_type,
                primary_df.status == secondary_df.status
            ],
            "inner"
        ).select(
            primary_df.transaction_id.alias("primary_transaction_id"),
            secondary_df.transaction_id.alias("secondary_transaction_id"),
            primary_df.account_id,
            primary_df.amount,
            primary_df.transaction_type,
            primary_df.transaction_date.alias("primary_transaction_date"),
            secondary_df.transaction_date.alias("secondary_transaction_date"),
            primary_df.status,
            lit("MATCHED").alias("match_status"),
            lit(None).alias("discrepancy_type"),
            lit(None).cast("decimal(18,2)").alias("discrepancy_amount")
        )
        
        # Find unmatched primary transactions
        matched_primary_ids = matched_df.select("primary_transaction_id").distinct()
        unmatched_primary_df = primary_df.join(
            matched_primary_ids,
            primary_df.transaction_id == matched_primary_ids.primary_transaction_id,
            "left_anti"
        )
        
        # Find unmatched secondary transactions
        matched_secondary_ids = matched_df.select("secondary_transaction_id").distinct()
        unmatched_secondary_df = secondary_df.join(
            matched_secondary_ids,
            secondary_df.transaction_id == matched_secondary_ids.secondary_transaction_id,
            "left_anti"
        )
        
        return matched_df, unmatched_primary_df, unmatched_secondary_df
    
    def fuzzy_match(
        self, 
        primary_df: DataFrame, 
        secondary_df: DataFrame,
        amount_tolerance: float = 0.01,
        date_tolerance_seconds: int = 86400  # 24 hours
    ) -> Tuple[DataFrame, DataFrame, DataFrame]:
        """
        Perform fuzzy matching between primary and secondary transactions.
        
        Args:
            primary_df: DataFrame containing primary transactions
            secondary_df: DataFrame containing secondary transactions
            amount_tolerance: Tolerance for amount differences (as a percentage)
            date_tolerance_seconds: Tolerance for date differences (in seconds)
            
        Returns:
            Tuple of (matched_df, unmatched_primary_df, unmatched_secondary_df)
        """
        # Join on account_id and transaction_type, with fuzzy matching for amount and date
        joined_df = primary_df.crossJoin(secondary_df).where(
            (primary_df.account_id == secondary_df.account_id) &
            (primary_df.transaction_type == secondary_df.transaction_type) &
            (abs(primary_df.amount - secondary_df.amount) <= primary_df.amount * amount_tolerance) &
            (abs(
                expr("unix_timestamp(primary_df.transaction_date)") - 
                expr("unix_timestamp(secondary_df.transaction_date)")
            ) <= date_tolerance_seconds)
        )
        
        # Calculate match score based on closeness of amount and date
        scored_df = joined_df.withColumn(
            "amount_diff", 
            abs(primary_df.amount - secondary_df.amount)
        ).withColumn(
            "date_diff_seconds",
            abs(
                expr("unix_timestamp(primary_df.transaction_date)") - 
                expr("unix_timestamp(secondary_df.transaction_date)")
            )
        ).withColumn(
            "match_score",
            expr("1.0 - (amount_diff / primary_df.amount) * 0.5 - (date_diff_seconds / 86400.0) * 0.5")
        )
        
        # Find the best match for each primary transaction
        window_spec = Window.partitionBy("primary_df.transaction_id").orderBy(col("match_score").desc())
        best_matches = scored_df.withColumn(
            "rank", 
            row_number().over(window_spec)
        ).filter(col("rank") == 1).drop("rank")
        
        # Create the matched DataFrame
        matched_df = best_matches.select(
            primary_df.transaction_id.alias("primary_transaction_id"),
            secondary_df.transaction_id.alias("secondary_transaction_id"),
            primary_df.account_id,
            primary_df.amount.alias("primary_amount"),
            secondary_df.amount.alias("secondary_amount"),
            primary_df.transaction_type,
            primary_df.transaction_date.alias("primary_transaction_date"),
            secondary_df.transaction_date.alias("secondary_transaction_date"),
            primary_df.status.alias("primary_status"),
            secondary_df.status.alias("secondary_status"),
            when(
                (primary_df.amount == secondary_df.amount) &
                (primary_df.status == secondary_df.status),
                "MATCHED"
            ).when(
                (primary_df.status != secondary_df.status),
                "PARTIAL"
            ).otherwise("PARTIAL").alias("match_status"),
            when(
                primary_df.amount != secondary_df.amount,
                "AMOUNT"
            ).when(
                primary_df.status != secondary_df.status,
                "STATUS"
            ).otherwise(None).alias("discrepancy_type"),
            when(
                primary_df.amount != secondary_df.amount,
                abs(primary_df.amount - secondary_df.amount)
            ).otherwise(None).alias("discrepancy_amount")
        )
        
        # Find unmatched primary transactions
        matched_primary_ids = matched_df.select("primary_transaction_id").distinct()
        unmatched_primary_df = primary_df.join(
            matched_primary_ids,
            primary_df.transaction_id == matched_primary_ids.primary_transaction_id,
            "left_anti"
        )
        
        # Find unmatched secondary transactions
        matched_secondary_ids = matched_df.select("secondary_transaction_id").distinct()
        unmatched_secondary_df = secondary_df.join(
            matched_secondary_ids,
            secondary_df.transaction_id == matched_secondary_ids.secondary_transaction_id,
            "left_anti"
        )
        
        return matched_df, unmatched_primary_df, unmatched_secondary_df
    
    def match_transactions(
        self, 
        primary_df: DataFrame, 
        secondary_df: DataFrame,
        match_strategy: str = "hybrid"
    ) -> Tuple[DataFrame, DataFrame, DataFrame]:
        """
        Match transactions using the specified strategy.
        
        Args:
            primary_df: DataFrame containing primary transactions
            secondary_df: DataFrame containing secondary transactions
            match_strategy: Matching strategy ('exact', 'fuzzy', or 'hybrid')
            
        Returns:
            Tuple of (matched_df, unmatched_primary_df, unmatched_secondary_df)
        """
        if match_strategy == "exact":
            return self.exact_match(primary_df, secondary_df)
        
        elif match_strategy == "fuzzy":
            return self.fuzzy_match(primary_df, secondary_df)
        
        elif match_strategy == "hybrid":
            # First try exact matching
            matched_exact, unmatched_primary_exact, unmatched_secondary_exact = self.exact_match(
                primary_df, secondary_df
            )
            
            # Then try fuzzy matching on the remaining unmatched transactions
            matched_fuzzy, unmatched_primary_fuzzy, unmatched_secondary_fuzzy = self.fuzzy_match(
                unmatched_primary_exact, unmatched_secondary_exact
            )
            
            # Combine the results
            matched_combined = matched_exact.union(matched_fuzzy)
            
            return matched_combined, unmatched_primary_fuzzy, unmatched_secondary_fuzzy
        
        else:
            raise ValueError(f"Unknown match strategy: {match_strategy}")
    
    def create_reconciliation_results(
        self, 
        batch_id: str,
        matched_df: DataFrame, 
        unmatched_primary_df: DataFrame, 
        unmatched_secondary_df: DataFrame,
        primary_source: str,
        secondary_source: str
    ) -> DataFrame:
        """
        Create reconciliation results from matching results.
        
        Args:
            batch_id: Reconciliation batch ID
            matched_df: DataFrame containing matched transactions
            unmatched_primary_df: DataFrame containing unmatched primary transactions
            unmatched_secondary_df: DataFrame containing unmatched secondary transactions
            primary_source: Name of the primary source system
            secondary_source: Name of the secondary source system
            
        Returns:
            DataFrame containing reconciliation results
        """
        # Create results for matched transactions
        matched_results = matched_df.select(
            expr("uuid()").alias("reconciliation_id"),
            lit(batch_id).alias("batch_id"),
            col("primary_transaction_id"),
            col("secondary_transaction_id"),
            col("match_status"),
            col("discrepancy_type"),
            col("discrepancy_amount"),
            current_timestamp().alias("reconciliation_timestamp"),
            when(
                col("match_status") == "PARTIAL",
                concat(
                    lit(f"Partial match between {primary_source} and {secondary_source}. "),
                    when(
                        col("discrepancy_type") == "AMOUNT",
                        concat(
                            lit("Amount discrepancy: "),
                            col("discrepancy_amount")
                        )
                    ).when(
                        col("discrepancy_type") == "STATUS",
                        concat(
                            lit("Status discrepancy: Primary="),
                            col("primary_status"),
                            lit(", Secondary="),
                            col("secondary_status")
                        )
                    ).otherwise(lit(""))
                )
            ).otherwise(
                lit(f"Exact match between {primary_source} and {secondary_source}")
            ).alias("notes")
        )
        
        # Create results for unmatched primary transactions
        unmatched_primary_results = unmatched_primary_df.select(
            expr("uuid()").alias("reconciliation_id"),
            lit(batch_id).alias("batch_id"),
            col("transaction_id").alias("primary_transaction_id"),
            lit(None).alias("secondary_transaction_id"),
            lit("UNMATCHED").alias("match_status"),
            lit("MISSING_SECONDARY").alias("discrepancy_type"),
            col("amount").alias("discrepancy_amount"),
            current_timestamp().alias("reconciliation_timestamp"),
            lit(f"Transaction in {primary_source} not found in {secondary_source}").alias("notes")
        )
        
        # Create results for unmatched secondary transactions
        unmatched_secondary_results = unmatched_secondary_df.select(
            expr("uuid()").alias("reconciliation_id"),
            lit(batch_id).alias("batch_id"),
            lit(None).alias("primary_transaction_id"),
            col("transaction_id").alias("secondary_transaction_id"),
            lit("UNMATCHED").alias("match_status"),
            lit("MISSING_PRIMARY").alias("discrepancy_type"),
            col("amount").alias("discrepancy_amount"),
            current_timestamp().alias("reconciliation_timestamp"),
            lit(f"Transaction in {secondary_source} not found in {primary_source}").alias("notes")
        )
        
        # Combine all results
        all_results = matched_results.union(unmatched_primary_results).union(unmatched_secondary_results)
        
        return all_results
