# Apache Iceberg Banking Reconciliation System

## Overview
This project implements a scalable data platform using Apache Iceberg for banking transaction reconciliation. It demonstrates Iceberg's advanced features through a practical banking use case that matches transactions across systems to identify discrepancies.

## Business Context
Banks operate multiple systems that process transactions (core banking, card processors, payment gateways). Reconciliation ensures data consistency by comparing transactions across these systems, identifying exceptions, and maintaining audit trails for compliance.

## Key Features
- Scalable data platform using Apache Iceberg
- Docker-based environment for easy development and testing
- Transaction processing from multiple banking sources
- Advanced reconciliation engine with matching algorithms
- Demonstration of Iceberg's schema evolution, time travel, and ACID transactions

## Technical Architecture
- **Apache Spark**: For distributed data processing
- **Apache Iceberg**: For table format with advanced features
- **MinIO**: S3-compatible object storage
- **PostgreSQL**: For Iceberg catalog service
- **Docker**: For containerized development environment

## Project Structure
```
banking-reconciliation-iceberg/
│
├── docker/                    # Docker configuration
│   ├── docker-compose.yml     # Multi-container setup
│   ├── spark/                 # Spark with Iceberg configuration
│   │   ├── Dockerfile
│   │   └── conf/
│   ├── minio/                 # S3-compatible storage
│   └── postgres/              # Catalog service
│
├── data/                      # Sample datasets
│   ├── raw/                   # Raw transaction files
│   ├── stage/                 # Staged data
│   └── reconciled/            # Reconciliation results
│
├── notebooks/                 # Jupyter notebooks for exploration
│
├── src/                       # Source code
│   ├── main/
│   │   └── python/
│   │       ├── models/        # Data models
│   │       ├── etl/           # ETL processes
│   │       ├── reconciliation/ # Reconciliation logic
│   │       └── api/           # Optional REST API
│   └── test/                  # Unit and integration tests
│
├── scripts/                   # Utility scripts
│
├── README.md                  # Project documentation
└── requirements.txt           # Python dependencies
```

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Git

### Setup
1. Clone the repository
2. Run `./scripts/setup.sh` to initialize the environment
3. Access Jupyter notebooks at http://localhost:8889
4. Follow the example notebooks to understand the system

### Manual Setup
If you prefer to set up the system manually:

1. Create the necessary directories:
   ```bash
   mkdir -p data/raw data/stage data/reconciled
   ```

2. Start the Docker containers:
   ```bash
   docker-compose up -d
   ```

3. Initialize MinIO buckets:
   ```bash
   docker exec -it jupyter python /opt/bitnami/spark/scripts/init_minio.py
   ```

4. Initialize Iceberg tables:
   ```bash
   docker exec -it jupyter python /opt/bitnami/spark/scripts/init_iceberg.py
   ```

5. Generate and ingest sample data:
   ```bash
   docker exec -it jupyter python /opt/bitnami/spark/scripts/generate_sample_data.py
   docker exec -it jupyter python /opt/bitnami/spark/scripts/ingest_data.py
   ```

### Troubleshooting

#### MinIO Connection Issues
- Ensure MinIO container is running: `docker ps | grep minio`
- Check MinIO logs: `docker logs minio`
- Verify MinIO credentials in configuration match those in docker-compose.yml
- Ensure the warehouse bucket exists: `docker exec -it jupyter python /opt/bitnami/spark/scripts/init_minio.py`

#### Spark Configuration Issues
- Verify Spark configuration is properly mounted: `docker exec -it jupyter ls -la /opt/bitnami/spark/conf`
- Check Spark logs: `docker logs spark-master`
- Run the configuration test: `docker exec -it jupyter python /opt/bitnami/spark/scripts/run_tests.py`

#### Iceberg Table Issues
- Ensure Iceberg tables are created: `docker exec -it jupyter python /opt/bitnami/spark/scripts/init_iceberg.py`
- Check for errors in the Spark UI: http://localhost:8082
- Verify the warehouse path is correctly set to `s3a://warehouse/`

## Advanced Iceberg Features Demonstrated
- **Schema Evolution**: Add new fields to transaction tables without rebuilding
- **Time Travel**: Query historical reconciliation states for audit
- **Partition Evolution**: Optimize partitioning based on query patterns
- **Optimized Reads**: Leverage predicate pushdown and file pruning
- **ACID Transactions**: Ensure consistency during reconciliation
- **Incremental Processing**: Process only new transactions since last run

## Implementation Guide

### Data Storage

#### MinIO Buckets

The system uses the following MinIO buckets:

- **warehouse**: Main storage for Iceberg tables
- **raw-data**: Storage for raw transaction data
- **stage-data**: Storage for intermediate data
- **reconciled-data**: Storage for reconciliation results

#### Iceberg Tables

The system uses the following Iceberg tables:

- **source_transactions**: Stores transaction data from all source systems
- **reconciliation_results**: Stores the results of reconciliation processes
- **reconciliation_batches**: Stores metadata about reconciliation batches

### Configuration

#### Spark Configuration

Critical Spark configuration parameters:

```
spark.sql.extensions = org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions
spark.sql.catalog.spark_catalog = org.apache.iceberg.spark.SparkSessionCatalog
spark.sql.catalog.spark_catalog.type = hive
spark.sql.catalog.local = org.apache.iceberg.spark.SparkCatalog
spark.sql.catalog.local.type = hadoop
spark.sql.catalog.local.warehouse = s3a://warehouse/iceberg-warehouse/
spark.hadoop.fs.s3a.endpoint = http://minio:9000
spark.hadoop.fs.s3a.access.key = minio
spark.hadoop.fs.s3a.secret.key = minio123
spark.hadoop.fs.s3a.path.style.access = true
spark.hadoop.fs.s3a.impl = org.apache.hadoop.fs.s3a.S3AFileSystem
spark.hadoop.fs.s3a.connection.ssl.enabled = false
spark.sql.defaultCatalog = local
```

#### Important Configuration Notes

1. The warehouse path must include a subdirectory: `s3a://warehouse/iceberg-warehouse/`
2. SSL should be disabled for local MinIO: `spark.hadoop.fs.s3a.connection.ssl.enabled = false`
3. Set the default catalog: `spark.sql.defaultCatalog = local`

### Data Model

#### Transaction Model

The Transaction model includes the following fields:

- **transaction_id**: Unique identifier for the transaction
- **source_system**: System where the transaction originated
- **transaction_date**: Date and time of the transaction
- **amount**: Transaction amount
- **account_id**: Account identifier
- **transaction_type**: Type of transaction (deposit, withdrawal, etc.)
- **reference_id**: Reference identifier
- **status**: Transaction status (completed, pending, failed, etc.)
- **payload**: Additional transaction data
- **created_at**: Creation timestamp
- **processing_timestamp**: Processing timestamp

#### Reconciliation Results Model

The reconciliation results include:

- **reconciliation_id**: Unique identifier for the reconciliation record
- **batch_id**: Identifier for the reconciliation batch
- **primary_transaction_id**: Transaction ID from the primary system
- **secondary_transaction_id**: Transaction ID from the secondary system
- **match_status**: Status of the match (MATCHED, PARTIAL, UNMATCHED)
- **discrepancy_type**: Type of discrepancy if any
- **discrepancy_amount**: Amount of discrepancy if any
- **reconciliation_timestamp**: Timestamp of reconciliation
- **notes**: Additional notes

#### Reconciliation Batch Model

The reconciliation batch includes:

- **batch_id**: Unique identifier for the batch
- **reconciliation_date**: Date of reconciliation
- **source_systems**: Array of source systems included in the batch
- **start_date**: Start date for transaction filtering
- **end_date**: End date for transaction filtering
- **status**: Batch status (PENDING, IN_PROGRESS, COMPLETED, FAILED)
- **total_transactions**: Total number of transactions processed
- **matched_count**: Number of matched transactions
- **unmatched_count**: Number of unmatched transactions
- **created_at**: Creation timestamp
- **completed_at**: Completion timestamp

### Implementation Components

#### ETL Components

1. **Extractors**: Extract transaction data from various sources
2. **Transformers**: Transform and normalize transaction data
3. **Loaders**: Load data into Iceberg tables

#### Reconciliation Components

1. **Matcher**: Match transactions across systems using exact, fuzzy, or hybrid matching
2. **Reporter**: Generate reconciliation reports

### Reconciliation Process

The reconciliation process follows these steps:

1. Create a reconciliation batch with a unique ID
2. Extract transactions from source systems for the specified date range
3. Transform and normalize transactions for comparison
4. Match transactions using the specified strategy (exact, fuzzy, or hybrid)
5. Generate reconciliation results
6. Create summary and discrepancy reports
7. Update the batch status with match statistics

### Testing

#### Unit Tests

The system includes unit tests for:

- **Spark Configuration**: Verifies Spark is properly configured
- **Transaction Model**: Tests the Transaction class functionality
- **Matcher**: Tests the transaction matching logic
- **Reconciliation Batch**: Tests batch creation and updates

#### Running Tests

Run tests using the provided script:

```bash
docker exec jupyter python /opt/bitnami/spark/scripts/run_tests.py
```

### Schema Issues

When working with complex data types like arrays:
- Always define explicit schemas for DataFrames
- Use appropriate data types (StringType, TimestampType, ArrayType, etc.)
- Ensure schema consistency when updating records

### Access Points

- **Spark Master UI**: http://localhost:8082
- **Spark Worker UI**: http://localhost:8083
- **Jupyter Notebook**: http://localhost:8889
- **MinIO Console**: http://localhost:9001 (login: minio / minio123)

### Best Practices

1. **Schema Management**: Always define explicit schemas for complex data types
2. **Error Handling**: Implement comprehensive error handling and logging
3. **Idempotent Operations**: Design operations to be safely repeatable
4. **Testing**: Write tests for all critical components
5. **Documentation**: Document configuration, data models, and processes

## Implementation Guide

### Data Storage

#### MinIO Buckets

The system uses the following MinIO buckets:

- **warehouse**: Main storage for Iceberg tables
- **raw-data**: Storage for raw transaction data
- **stage-data**: Storage for intermediate data
- **reconciled-data**: Storage for reconciliation results

#### Iceberg Tables

The system uses the following Iceberg tables:

- **source_transactions**: Stores transaction data from all source systems
- **reconciliation_results**: Stores the results of reconciliation processes
- **reconciliation_batches**: Stores metadata about reconciliation batches

### Configuration

#### Spark Configuration

Critical Spark configuration parameters:

```
spark.sql.extensions = org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions
spark.sql.catalog.spark_catalog = org.apache.iceberg.spark.SparkSessionCatalog
spark.sql.catalog.spark_catalog.type = hive
spark.sql.catalog.local = org.apache.iceberg.spark.SparkCatalog
spark.sql.catalog.local.type = hadoop
spark.sql.catalog.local.warehouse = s3a://warehouse/iceberg-warehouse/
spark.hadoop.fs.s3a.endpoint = http://minio:9000
spark.hadoop.fs.s3a.access.key = minio
spark.hadoop.fs.s3a.secret.key = minio123
spark.hadoop.fs.s3a.path.style.access = true
spark.hadoop.fs.s3a.impl = org.apache.hadoop.fs.s3a.S3AFileSystem
spark.hadoop.fs.s3a.connection.ssl.enabled = false
spark.sql.defaultCatalog = local
```

#### Important Configuration Notes

1. The warehouse path must include a subdirectory: `s3a://warehouse/iceberg-warehouse/`
2. SSL should be disabled for local MinIO: `spark.hadoop.fs.s3a.connection.ssl.enabled = false`
3. Set the default catalog: `spark.sql.defaultCatalog = local`

### Data Model

#### Transaction Model

The Transaction model includes the following fields:

- **transaction_id**: Unique identifier for the transaction
- **source_system**: System where the transaction originated
- **transaction_date**: Date and time of the transaction
- **amount**: Transaction amount
- **account_id**: Account identifier
- **transaction_type**: Type of transaction (deposit, withdrawal, etc.)
- **reference_id**: Reference identifier
- **status**: Transaction status (completed, pending, failed, etc.)
- **payload**: Additional transaction data
- **created_at**: Creation timestamp
- **processing_timestamp**: Processing timestamp

#### Reconciliation Results Model

The reconciliation results include:

- **reconciliation_id**: Unique identifier for the reconciliation record
- **batch_id**: Identifier for the reconciliation batch
- **primary_transaction_id**: Transaction ID from the primary system
- **secondary_transaction_id**: Transaction ID from the secondary system
- **match_status**: Status of the match (MATCHED, PARTIAL, UNMATCHED)
- **discrepancy_type**: Type of discrepancy if any
- **discrepancy_amount**: Amount of discrepancy if any
- **reconciliation_timestamp**: Timestamp of reconciliation
- **notes**: Additional notes

#### Reconciliation Batch Model

The reconciliation batch includes:

- **batch_id**: Unique identifier for the batch
- **reconciliation_date**: Date of reconciliation
- **source_systems**: Array of source systems included in the batch
- **start_date**: Start date for transaction filtering
- **end_date**: End date for transaction filtering
- **status**: Batch status (PENDING, IN_PROGRESS, COMPLETED, FAILED)
- **total_transactions**: Total number of transactions processed
- **matched_count**: Number of matched transactions
- **unmatched_count**: Number of unmatched transactions
- **created_at**: Creation timestamp
- **completed_at**: Completion timestamp

### Implementation Components

#### ETL Components

1. **Extractors**: Extract transaction data from various sources
2. **Transformers**: Transform and normalize transaction data
3. **Loaders**: Load data into Iceberg tables

#### Reconciliation Components

1. **Matcher**: Match transactions across systems using exact, fuzzy, or hybrid matching
2. **Reporter**: Generate reconciliation reports

### Reconciliation Process

The reconciliation process follows these steps:

1. Create a reconciliation batch with a unique ID
2. Extract transactions from source systems for the specified date range
3. Transform and normalize transactions for comparison
4. Match transactions using the specified strategy (exact, fuzzy, or hybrid)
5. Generate reconciliation results
6. Create summary and discrepancy reports
7. Update the batch status with match statistics

### Testing

#### Unit Tests

The system includes unit tests for:

- **Spark Configuration**: Verifies Spark is properly configured
- **Transaction Model**: Tests the Transaction class functionality
- **Matcher**: Tests the transaction matching logic
- **Reconciliation Batch**: Tests batch creation and updates

#### Running Tests

Run tests using the provided script:

```bash
docker exec jupyter python /opt/bitnami/spark/scripts/run_tests.py
```

### Schema Issues

When working with complex data types like arrays:
- Always define explicit schemas for DataFrames
- Use appropriate data types (StringType, TimestampType, ArrayType, etc.)
- Ensure schema consistency when updating records

### Access Points

- **Spark Master UI**: http://localhost:8082
- **Spark Worker UI**: http://localhost:8083
- **Jupyter Notebook**: http://localhost:8889
- **MinIO Console**: http://localhost:9001 (login: minio / minio123)

### Best Practices

1. **Schema Management**: Always define explicit schemas for complex data types
2. **Error Handling**: Implement comprehensive error handling and logging
3. **Idempotent Operations**: Design operations to be safely repeatable
4. **Testing**: Write tests for all critical components
5. **Documentation**: Document configuration, data models, and processes

### Example Output

#### Iceberg Table Schema

```
Schema for source_transactions:
+--------------------+----------------------+-------+
|col_name            |data_type             |comment|
+--------------------+----------------------+-------+
|transaction_id      |string                |       |
|source_system       |string                |       |
|transaction_date    |timestamp             |       |
|amount              |decimal(18,2)         |       |
|account_id          |string                |       |
|transaction_type    |string                |       |
|reference_id        |string                |       |
|status              |string                |       |
|payload             |string                |       |
|created_at          |timestamp             |       |
|processing_timestamp|timestamp             |       |
|                    |                      |       |
|# Partitioning      |                      |       |
|Part 0              |days(transaction_date)|       |
|Part 1              |source_system         |       |
+--------------------+----------------------+-------+

Schema for reconciliation_results:
+------------------------+------------------------------+-------+
|col_name                |data_type                     |comment|
+------------------------+------------------------------+-------+
|reconciliation_id       |string                        |       |
|batch_id                |string                        |       |
|primary_transaction_id  |string                        |       |
|secondary_transaction_id|string                        |       |
|match_status            |string                        |       |
|discrepancy_type        |string                        |       |
|discrepancy_amount      |decimal(18,2)                 |       |
|reconciliation_timestamp|timestamp                     |       |
|notes                   |string                        |       |
|                        |                              |       |
|# Partitioning          |                              |       |
|Part 0                  |days(reconciliation_timestamp)|       |
|Part 1                  |match_status                  |       |
+------------------------+------------------------------+-------+

Schema for reconciliation_batches:
+-------------------+-------------+-------+
|col_name           |data_type    |comment|
+-------------------+-------------+-------+
|batch_id           |string       |       |
|reconciliation_date|timestamp    |       |
|source_systems     |array<string>|       |
|start_date         |timestamp    |       |
|end_date           |timestamp    |       |
|status             |string       |       |
|total_transactions |bigint       |       |
|matched_count      |bigint       |       |
|unmatched_count    |bigint       |       |
|created_at         |timestamp    |       |
|completed_at       |timestamp    |       |
|                   |             |       |
|# Partitioning     |             |       |
|Not partitioned    |             |       |
+-------------------+-------------+-------+
```

#### Sample Reconciliation Batch

```
+-------------+--------------------------+------------------------------+--------------------------+--------------------------+---------+----------
---------+-------------+---------------+--------------------------+--------------------------+
|batch_id     |reconciliation_date       |source_systems                |start_date                |end_date                  |status   |total_tran
nsactions|matched_count|unmatched_count|created_at                |completed_at              |
+-------------+--------------------------+------------------------------+--------------------------+--------------------------+---------+----------
---------+-------------+---------------+--------------------------+--------------------------+
|TEST-caf44569|2025-05-09 19:50:58.894405|[core_banking, card_processor]|2025-05-09 19:50:58.894411|2025-05-09 19:50:58.894411|COMPLETED|100
         |80           |20             |2025-05-09 19:50:58.894412|2025-05-09 19:50:58.894412|
+-------------+--------------------------+------------------------------+--------------------------+--------------------------+---------+----------
---------+-------------+---------------+--------------------------+--------------------------+
```

#### Data Ingestion Output

```
Starting data ingestion process...
Ingesting /opt/bitnami/spark/data/raw/card_processor_transactions.csv...
Loaded 5042 transactions into source_transactions table
Ingesting /opt/bitnami/spark/data/raw/core_banking_transactions.csv...
Loaded 5000 transactions into source_transactions table
Ingesting /opt/bitnami/spark/data/raw/payment_gateway_transactions.csv...
Loaded 5032 transactions into source_transactions table
Data ingestion completed successfully.
```

## License
[MIT License](LICENSE)
