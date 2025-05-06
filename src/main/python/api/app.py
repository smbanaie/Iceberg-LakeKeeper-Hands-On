"""
Simple API for the banking reconciliation system.
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from pyspark.sql import SparkSession

# Import project modules
from src.main.python.config import Config


# Initialize FastAPI app
app = FastAPI(
    title="Banking Reconciliation API",
    description="API for the Apache Iceberg Banking Reconciliation System",
    version="1.0.0"
)

# Create Spark session
def get_spark_session():
    """Create or get the Spark session."""
    return SparkSession.builder \
        .appName("Banking Reconciliation API") \
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


# Pydantic models for API
class ReconciliationBatch(BaseModel):
    """Model for reconciliation batch."""
    batch_id: str
    reconciliation_date: datetime
    source_systems: List[str]
    start_date: datetime
    end_date: datetime
    status: str
    total_transactions: int
    matched_count: int
    unmatched_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None


class ReconciliationResult(BaseModel):
    """Model for reconciliation result."""
    reconciliation_id: str
    batch_id: str
    primary_transaction_id: Optional[str]
    secondary_transaction_id: Optional[str]
    match_status: str
    discrepancy_type: Optional[str] = None
    discrepancy_amount: Optional[float] = None
    reconciliation_timestamp: datetime
    notes: Optional[str] = None


class ReconciliationSummary(BaseModel):
    """Model for reconciliation summary."""
    batch_id: str
    status: str
    source_systems: List[str]
    start_date: datetime
    end_date: datetime
    total_transactions: int
    matched_count: int
    unmatched_count: int
    match_rate: float
    created_at: datetime
    completed_at: Optional[datetime] = None


# API routes
@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Banking Reconciliation API"}


@app.get("/batches", response_model=List[ReconciliationBatch])
def get_batches(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None
):
    """
    Get reconciliation batches.
    
    Args:
        limit: Maximum number of batches to return
        offset: Offset for pagination
        status: Filter by status
        
    Returns:
        List of reconciliation batches
    """
    spark = get_spark_session()
    
    # Build query
    query = f"""
        SELECT *
        FROM {Config.RECONCILIATION_BATCHES_TABLE}
    """
    
    if status:
        query += f" WHERE status = '{status}'"
    
    query += f" ORDER BY reconciliation_date DESC LIMIT {limit} OFFSET {offset}"
    
    # Execute query
    result = spark.sql(query)
    
    # Convert to list of dictionaries
    batches = [row.asDict() for row in result.collect()]
    
    return batches


@app.get("/batches/{batch_id}", response_model=ReconciliationSummary)
def get_batch(batch_id: str):
    """
    Get a specific reconciliation batch.
    
    Args:
        batch_id: Batch ID
        
    Returns:
        Reconciliation batch summary
    """
    spark = get_spark_session()
    
    # Get batch
    batch_query = f"""
        SELECT *
        FROM {Config.RECONCILIATION_BATCHES_TABLE}
        WHERE batch_id = '{batch_id}'
    """
    
    batch_result = spark.sql(batch_query)
    
    if batch_result.count() == 0:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")
    
    batch = batch_result.first().asDict()
    
    # Get summary statistics
    stats_query = f"""
        SELECT
            match_status,
            COUNT(*) as count
        FROM {Config.RECONCILIATION_RESULTS_TABLE}
        WHERE batch_id = '{batch_id}'
        GROUP BY match_status
    """
    
    stats_result = spark.sql(stats_query)
    stats = {row["match_status"]: row["count"] for row in stats_result.collect()}
    
    # Calculate match rate
    matched_count = stats.get("MATCHED", 0)
    total_count = sum(stats.values())
    match_rate = matched_count / total_count if total_count > 0 else 0
    
    # Create summary
    summary = {
        **batch,
        "match_rate": match_rate
    }
    
    return summary


@app.get("/batches/{batch_id}/results", response_model=List[ReconciliationResult])
def get_batch_results(
    batch_id: str,
    match_status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Get reconciliation results for a specific batch.
    
    Args:
        batch_id: Batch ID
        match_status: Filter by match status
        limit: Maximum number of results to return
        offset: Offset for pagination
        
    Returns:
        List of reconciliation results
    """
    spark = get_spark_session()
    
    # Build query
    query = f"""
        SELECT *
        FROM {Config.RECONCILIATION_RESULTS_TABLE}
        WHERE batch_id = '{batch_id}'
    """
    
    if match_status:
        query += f" AND match_status = '{match_status}'"
    
    query += f" ORDER BY reconciliation_timestamp DESC LIMIT {limit} OFFSET {offset}"
    
    # Execute query
    result = spark.sql(query)
    
    # Convert to list of dictionaries
    results = [row.asDict() for row in result.collect()]
    
    return results


@app.get("/transactions", response_model=List[Dict[str, Any]])
def get_transactions(
    source_system: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Get transactions.
    
    Args:
        source_system: Filter by source system
        start_date: Filter by start date (ISO format)
        end_date: Filter by end date (ISO format)
        limit: Maximum number of transactions to return
        offset: Offset for pagination
        
    Returns:
        List of transactions
    """
    spark = get_spark_session()
    
    # Build query
    query = f"""
        SELECT *
        FROM {Config.SOURCE_TRANSACTIONS_TABLE}
        WHERE 1=1
    """
    
    if source_system:
        query += f" AND source_system = '{source_system}'"
    
    if start_date:
        query += f" AND transaction_date >= '{start_date}'"
    
    if end_date:
        query += f" AND transaction_date <= '{end_date}'"
    
    query += f" ORDER BY transaction_date DESC LIMIT {limit} OFFSET {offset}"
    
    # Execute query
    result = spark.sql(query)
    
    # Convert to list of dictionaries
    transactions = [row.asDict() for row in result.collect()]
    
    return transactions


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
