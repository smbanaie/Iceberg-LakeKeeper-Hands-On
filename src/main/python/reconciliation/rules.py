"""
Reconciliation rules for the banking reconciliation system.
"""

from typing import Dict, List, Any, Callable
from datetime import datetime, timedelta

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, abs, expr, when, lit


class ReconciliationRule:
    """
    Base class for reconciliation rules.
    """
    
    def __init__(self, name: str, description: str):
        """
        Initialize a reconciliation rule.
        
        Args:
            name: Rule name
            description: Rule description
        """
        self.name = name
        self.description = description
    
    def apply(self, df: DataFrame) -> DataFrame:
        """
        Apply the rule to a DataFrame.
        
        Args:
            df: DataFrame to apply the rule to
            
        Returns:
            DataFrame with the rule applied
        """
        raise NotImplementedError("Subclasses must implement this method")


class ExactMatchRule(ReconciliationRule):
    """
    Rule for exact matching of transactions.
    """
    
    def __init__(self):
        """Initialize the exact match rule."""
        super().__init__(
            name="exact_match",
            description="Match transactions with exactly the same account, amount, type, and status"
        )
    
    def apply(self, primary_df: DataFrame, secondary_df: DataFrame) -> DataFrame:
        """
        Apply the exact match rule.
        
        Args:
            primary_df: Primary transactions DataFrame
            secondary_df: Secondary transactions DataFrame
            
        Returns:
            DataFrame of matched transactions
        """
        return primary_df.join(
            secondary_df,
            [
                primary_df.account_id == secondary_df.account_id,
                primary_df.amount == secondary_df.amount,
                primary_df.transaction_type == secondary_df.transaction_type,
                primary_df.status == secondary_df.status
            ],
            "inner"
        )


class AmountToleranceRule(ReconciliationRule):
    """
    Rule for matching transactions with a tolerance for amount differences.
    """
    
    def __init__(self, tolerance_percentage: float = 0.01):
        """
        Initialize the amount tolerance rule.
        
        Args:
            tolerance_percentage: Tolerance for amount differences as a percentage
        """
        super().__init__(
            name="amount_tolerance",
            description=f"Match transactions with amount differences within {tolerance_percentage * 100}%"
        )
        self.tolerance_percentage = tolerance_percentage
    
    def apply(self, primary_df: DataFrame, secondary_df: DataFrame) -> DataFrame:
        """
        Apply the amount tolerance rule.
        
        Args:
            primary_df: Primary transactions DataFrame
            secondary_df: Secondary transactions DataFrame
            
        Returns:
            DataFrame of matched transactions
        """
        return primary_df.join(
            secondary_df,
            [
                primary_df.account_id == secondary_df.account_id,
                primary_df.transaction_type == secondary_df.transaction_type,
                abs(primary_df.amount - secondary_df.amount) <= (primary_df.amount * self.tolerance_percentage)
            ],
            "inner"
        ).withColumn(
            "discrepancy_type",
            when(
                primary_df.amount != secondary_df.amount,
                "AMOUNT"
            ).otherwise(None)
        ).withColumn(
            "discrepancy_amount",
            when(
                primary_df.amount != secondary_df.amount,
                abs(primary_df.amount - secondary_df.amount)
            ).otherwise(None)
        )


class DateToleranceRule(ReconciliationRule):
    """
    Rule for matching transactions with a tolerance for date differences.
    """
    
    def __init__(self, tolerance_hours: int = 24):
        """
        Initialize the date tolerance rule.
        
        Args:
            tolerance_hours: Tolerance for date differences in hours
        """
        super().__init__(
            name="date_tolerance",
            description=f"Match transactions with date differences within {tolerance_hours} hours"
        )
        self.tolerance_seconds = tolerance_hours * 3600
    
    def apply(self, primary_df: DataFrame, secondary_df: DataFrame) -> DataFrame:
        """
        Apply the date tolerance rule.
        
        Args:
            primary_df: Primary transactions DataFrame
            secondary_df: Secondary transactions DataFrame
            
        Returns:
            DataFrame of matched transactions
        """
        return primary_df.join(
            secondary_df,
            [
                primary_df.account_id == secondary_df.account_id,
                primary_df.amount == secondary_df.amount,
                primary_df.transaction_type == secondary_df.transaction_type,
                abs(
                    expr("unix_timestamp(primary_df.transaction_date)") - 
                    expr("unix_timestamp(secondary_df.transaction_date)")
                ) <= self.tolerance_seconds
            ],
            "inner"
        ).withColumn(
            "discrepancy_type",
            when(
                primary_df.transaction_date != secondary_df.transaction_date,
                "DATE"
            ).otherwise(None)
        ).withColumn(
            "date_diff_seconds",
            when(
                primary_df.transaction_date != secondary_df.transaction_date,
                abs(
                    expr("unix_timestamp(primary_df.transaction_date)") - 
                    expr("unix_timestamp(secondary_df.transaction_date)")
                )
            ).otherwise(None)
        )


class StatusIgnoreRule(ReconciliationRule):
    """
    Rule for matching transactions while ignoring status differences.
    """
    
    def __init__(self):
        """Initialize the status ignore rule."""
        super().__init__(
            name="status_ignore",
            description="Match transactions ignoring status differences"
        )
    
    def apply(self, primary_df: DataFrame, secondary_df: DataFrame) -> DataFrame:
        """
        Apply the status ignore rule.
        
        Args:
            primary_df: Primary transactions DataFrame
            secondary_df: Secondary transactions DataFrame
            
        Returns:
            DataFrame of matched transactions
        """
        return primary_df.join(
            secondary_df,
            [
                primary_df.account_id == secondary_df.account_id,
                primary_df.amount == secondary_df.amount,
                primary_df.transaction_type == secondary_df.transaction_type
            ],
            "inner"
        ).withColumn(
            "discrepancy_type",
            when(
                primary_df.status != secondary_df.status,
                "STATUS"
            ).otherwise(None)
        ).withColumn(
            "notes",
            when(
                primary_df.status != secondary_df.status,
                concat(
                    lit("Status discrepancy: Primary="),
                    primary_df.status,
                    lit(", Secondary="),
                    secondary_df.status
                )
            ).otherwise(None)
        )


class ReferenceIdMatchRule(ReconciliationRule):
    """
    Rule for matching transactions based on reference ID.
    """
    
    def __init__(self):
        """Initialize the reference ID match rule."""
        super().__init__(
            name="reference_id_match",
            description="Match transactions with the same reference ID"
        )
    
    def apply(self, primary_df: DataFrame, secondary_df: DataFrame) -> DataFrame:
        """
        Apply the reference ID match rule.
        
        Args:
            primary_df: Primary transactions DataFrame
            secondary_df: Secondary transactions DataFrame
            
        Returns:
            DataFrame of matched transactions
        """
        return primary_df.join(
            secondary_df,
            primary_df.reference_id == secondary_df.reference_id,
            "inner"
        )


class RuleEngine:
    """
    Engine for applying reconciliation rules.
    """
    
    def __init__(self, spark: SparkSession):
        """
        Initialize the rule engine.
        
        Args:
            spark: SparkSession instance
        """
        self.spark = spark
        self.rules = []
    
    def add_rule(self, rule: ReconciliationRule) -> None:
        """
        Add a rule to the engine.
        
        Args:
            rule: ReconciliationRule instance
        """
        self.rules.append(rule)
    
    def apply_rules(
        self, 
        primary_df: DataFrame, 
        secondary_df: DataFrame,
        rule_names: List[str] = None
    ) -> Dict[str, DataFrame]:
        """
        Apply rules to match transactions.
        
        Args:
            primary_df: Primary transactions DataFrame
            secondary_df: Secondary transactions DataFrame
            rule_names: Optional list of rule names to apply (if None, apply all rules)
            
        Returns:
            Dictionary mapping rule names to matched DataFrames
        """
        results = {}
        
        for rule in self.rules:
            if rule_names is None or rule.name in rule_names:
                matched_df = rule.apply(primary_df, secondary_df)
                results[rule.name] = matched_df
        
        return results
