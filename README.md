# Apache Iceberg Banking Reconciliation System

## Overview
This project implements a scalable data platform using Apache Iceberg for banking transaction reconciliation. It demonstrates Iceberg's advanced features through a practical banking use case that matches transactions across multiple systems to identify discrepancies and ensure data consistency.

## Business Context
Banks operate multiple systems that process transactions (core banking, card processors, payment gateways). Reconciliation ensures data consistency by comparing transactions across these systems, identifying exceptions, and maintaining audit trails for compliance and regulatory requirements.

## Key Features
- **Scalable Data Platform**: Apache Iceberg with advanced table format features
- **Docker-based Environment**: Complete containerized setup for easy development
- **Multi-System Integration**: Process transactions from core banking, card processors, and payment gateways
- **Advanced Reconciliation Engine**: Sophisticated matching algorithms with configurable strategies
- **Iceberg Advanced Features**: Schema evolution, time travel, ACID transactions, and incremental processing
- **Real-time Monitoring**: Web UIs for Spark, MinIO, and PostgreSQL

## Technical Architecture

### Core Components
- **Apache Spark 3.3.1**: Distributed data processing engine
- **Apache Iceberg**: Advanced table format with ACID transactions
- **MinIO**: S3-compatible object storage for data lake
- **PostgreSQL 14**: Iceberg catalog service and metadata storage
- **Jupyter Notebooks**: Interactive data exploration and development
- **Docker & Docker Compose**: Containerized environment

### Data Flow
```
Raw Transactions → ETL Processing → Iceberg Tables → Reconciliation Engine → Results & Reports
```

## Project Structure
```
iceberg-bank-recon/
├── docker/                    # Docker configuration
│   ├── docker-compose.yml     # Multi-container setup
│   └── spark/                 # Spark Docker images
│       ├── Dockerfile.master  # Spark master container
│       ├── Dockerfile.worker  # Spark worker container
│       ├── Dockerfile.jupyter # Jupyter container
│       ├── conf/              # Spark configuration
│       └── requirements.txt   # Python dependencies
│
├── data/                      # Data directories
│   ├── raw/                   # Raw transaction files
│   ├── stage/                 # Staged data
│   └── reconciled/            # Reconciliation results
│
├── src/                       # Source code
│   ├── main/python/
│   │   ├── etl/              # ETL processes
│   │   │   └── loaders.py    # Iceberg data loaders
│   │   ├── models/           # Data models
│   │   ├── reconciliation/   # Reconciliation logic
│   │   └── config.py         # Configuration management
│   └── test/python/          # Unit tests
│
├── scripts/                   # Utility scripts
│   ├── setup.sh              # Complete environment setup
│   ├── init_minio.py         # MinIO bucket initialization
│   ├── init_iceberg.py       # Iceberg table creation
│   ├── generate_sample_data.py # Sample data generation
│   ├── ingest_data.py        # Data ingestion
│   ├── test_setup.py         # Setup verification
│   └── run_tests.py          # Test execution
│
├── notebooks/                 # Jupyter notebooks
├── requirements.txt           # Python dependencies
└── README.md                 # This documentation
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Git
- At least 4GB RAM available for containers

### One-Command Setup
```bash
# Clone the repository
git clone <repository-url>
cd iceberg-bank-recon

# Run the complete setup
./scripts/setup.sh
```

The setup script will:
1. ✅ Start all Docker containers (Spark, MinIO, PostgreSQL, Jupyter)
2. ✅ Initialize MinIO buckets (warehouse, raw-data, stage-data, reconciled-data)
3. ✅ Create Iceberg tables (source_transactions, reconciliation_results, reconciliation_batches)
4. ✅ Generate sample transaction data (~15,000 transactions across 3 systems)
5. ✅ Load data into Iceberg tables
6. ✅ Run verification tests

### Access Points
After setup, access the system at:
- **Jupyter Notebooks**: http://localhost:8889
- **Spark Master UI**: http://localhost:8082
- **Spark Worker UI**: http://localhost:8083
- **MinIO Console**: http://localhost:9001 (login: minio/minio123)
- **PostgreSQL**: localhost:5432 (user: iceberg, password: iceberg)

## Data Model

### Transaction Schema
```sql
CREATE TABLE source_transactions (
  transaction_id STRING,
  source_system STRING,
  transaction_date TIMESTAMP,
  amount DECIMAL(18,2),
  account_id STRING,
  transaction_type STRING,
  reference_id STRING,
  status STRING,
  payload STRING,
  created_at TIMESTAMP,
  processing_timestamp TIMESTAMP
)
USING iceberg
PARTITIONED BY (days(transaction_date), source_system)
```

### Reconciliation Results Schema
```sql
CREATE TABLE reconciliation_results (
  reconciliation_id STRING,
  batch_id STRING,
  primary_transaction_id STRING,
  secondary_transaction_id STRING,
  match_status STRING,
  discrepancy_type STRING,
  discrepancy_amount DECIMAL(18,2),
  reconciliation_timestamp TIMESTAMP,
  notes STRING
)
USING iceberg
PARTITIONED BY (days(reconciliation_timestamp), match_status)
```

### Reconciliation Batches Schema
```sql
CREATE TABLE reconciliation_batches (
  batch_id STRING,
  reconciliation_date TIMESTAMP,
  source_systems ARRAY<STRING>,
  start_date TIMESTAMP,
  end_date TIMESTAMP,
  status STRING,
  total_transactions BIGINT,
  matched_count BIGINT,
  unmatched_count BIGINT,
  created_at TIMESTAMP,
  completed_at TIMESTAMP
)
USING iceberg
```

## Configuration

### Spark Configuration
The system uses the following critical Spark configurations:

```python
spark = SparkSession.builder \
    .appName("Banking Reconciliation") \
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.iceberg.spark.SparkSessionCatalog") \
    .config("spark.sql.catalog.spark_catalog.type", "hive") \
    .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.local.type", "hadoop") \
    .config("spark.sql.catalog.local.warehouse", "s3a://warehouse/iceberg-warehouse/") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "minio") \
    .config("spark.hadoop.fs.s3a.secret.key", "minio123") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
    .config("spark.sql.defaultCatalog", "local") \
    .getOrCreate()
```

### MinIO Configuration
- **Endpoint**: http://localhost:9000
- **Console**: http://localhost:9001
- **Access Key**: minio
- **Secret Key**: minio123
- **Buckets**: warehouse, raw-data, stage-data, reconciled-data

## Usage Examples

### 1. Data Ingestion
```python
from src.main.python.etl.loaders import IcebergLoader

# Initialize loader
loader = IcebergLoader(spark)

# Load transactions from CSV
loader.load_transactions_from_csv("/path/to/transactions.csv")

# Load incrementally (avoiding duplicates)
loader.load_transactions_incrementally(df, "core_banking")
```

### 2. Reconciliation Process
```python
# Create reconciliation batch
batch_id = "RECON-2025-01-01"
source_systems = ["core_banking", "card_processor"]

# Run reconciliation
reconciler = ReconciliationEngine(spark)
results = reconciler.reconcile_transactions(
    batch_id=batch_id,
    source_systems=source_systems,
    start_date="2025-01-01",
    end_date="2025-01-01"
)
```

### 3. Time Travel Queries
```python
# Query historical data
historical_data = spark.sql("""
    SELECT * FROM local.banking.source_transactions
    FOR TIMESTAMP AS OF '2025-01-01 10:00:00'
    WHERE source_system = 'core_banking'
""")
```

### 4. Schema Evolution
```python
# Add new column to existing table
spark.sql("""
    ALTER TABLE local.banking.source_transactions
    ADD COLUMN new_field STRING
""")
```

## Advanced Iceberg Features

### 1. Schema Evolution
- Add, drop, or rename columns without rebuilding tables
- Maintain backward compatibility
- Automatic schema versioning

### 2. Time Travel
- Query data at any point in time
- Audit trail for compliance
- Rollback capabilities

### 3. ACID Transactions
- Atomic operations across multiple tables
- Consistency guarantees
- Isolation between concurrent operations

### 4. Partition Evolution
- Change partitioning strategy without data migration
- Optimize query performance
- Automatic partition pruning

### 5. Incremental Processing
- Process only new data since last run
- Efficient updates and deletes
- Change data capture capabilities

## Troubleshooting

### Common Issues

#### 1. MinIO Connection Issues
```bash
# Check if MinIO is running
docker ps | grep minio

# Check MinIO logs
docker logs minio

# Reinitialize buckets
docker exec jupyter python /opt/bitnami/spark/scripts/init_minio.py
```

#### 2. Spark Configuration Issues
```bash
# Check Spark logs
docker logs spark-master

# Verify configuration
docker exec jupyter python /opt/bitnami/spark/scripts/test_setup.py
```

#### 3. Iceberg Table Issues
```bash
# Recreate tables
docker exec jupyter python /opt/bitnami/spark/scripts/init_iceberg.py

# Check table schemas
docker exec jupyter spark-sql -e "DESCRIBE local.banking.source_transactions"
```

#### 4. Permission Issues
```bash
# Fix script permissions
chmod +x scripts/setup.sh

# Fix line endings (if on Windows/WSL)
dos2unix scripts/setup.sh
```

### Performance Optimization

#### 1. Spark Configuration
```bash
# Increase memory for large datasets
SPARK_WORKER_MEMORY=4G
SPARK_WORKER_CORES=4
```

#### 2. Iceberg Optimization
```python
# Compact small files
spark.sql("""
    CALL local.system.rewrite_data_files(
        table => 'local.banking.source_transactions',
        options => map('min-input-files','5', 'target-file-size-bytes', '104857600')
    )
""")

# Expire old snapshots
spark.sql("""
    CALL local.system.expire_snapshots(
        table => 'local.banking.source_transactions',
        older_than => '7d'
    )
""")
```

## Development

### Running Tests
```bash
# Run all tests
docker exec jupyter python /opt/bitnami/spark/scripts/run_tests.py

# Run specific test
docker exec jupyter python -m pytest src/test/python/test_iceberg_loader.py -v
```

### Adding New Features
1. Create feature branch
2. Add tests in `src/test/python/`
3. Update documentation
4. Run full test suite
5. Submit pull request

### Code Style
- Follow PEP 8 for Python code
- Use type hints where appropriate
- Add docstrings to all functions
- Write unit tests for new features

## Monitoring and Logging

### Spark UI
- Monitor job progress and performance
- Debug failed applications
- Analyze query plans

### MinIO Console
- Monitor storage usage
- Manage buckets and objects
- Set up access policies

### Application Logs
```bash
# View container logs
docker logs jupyter
docker logs spark-master
docker logs minio
```

## Production Considerations

### Security
- Use proper authentication for MinIO
- Implement SSL/TLS for all connections
- Set up proper network isolation
- Use secrets management for credentials

### Scalability
- Scale Spark workers based on workload
- Use external MinIO cluster for production
- Implement proper monitoring and alerting
- Set up automated backups

### Performance
- Tune Spark configuration for your workload
- Optimize Iceberg table partitioning
- Use appropriate file formats and compression
- Monitor and optimize query performance

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License
[MIT License](LICENSE)

## Support
For issues and questions:
1. Check the troubleshooting section
2. Review the logs and error messages
3. Open an issue with detailed information
4. Include system information and error logs

## Lakehouse Setup with Jupyter Notebooks

> **Note:** The initial setup scripts for the Lakehouse (Iceberg tables, catalog, and storage configuration) have been moved from `scripts/setup.sh` to dedicated Jupyter notebooks in the `notebooks/` directory. This allows for interactive, step-by-step setup and experimentation.

### Notebooks Overview

There are two main setup flows, each with two phases:

#### 1. Local Storage (Hadoop Catalog)
- **01_Phase1_complete_setup_local_catalog_local_storage.ipynb**
  - Sets up the Iceberg catalog using local file-based (Hadoop) storage.
  - Configures Spark and Iceberg for local warehouse, creates the initial catalog and tables.
- **01_Phase2_complete_setup_local_catalog_local_storage.ipynb**
  - Generates and populates sample banking data into the local Iceberg tables.
  - Demonstrates data ingestion, partitioning, and validation.

#### 2. MinIO S3 Storage (Hadoop Catalog)
- **02_Phase1_complete_setup_local_catalog_minio_storage.ipynb**
  - Sets up the Iceberg catalog using MinIO as S3-compatible object storage.
  - Configures Spark and Iceberg for S3A, creates the initial catalog and tables in MinIO.
- **02_Phase2_complete_setup_local_catalog_minio_storage.ipynb**
  - Generates and populates sample banking data into the MinIO-backed Iceberg tables.
  - Demonstrates S3-based data ingestion, partitioning, and validation.

> **How to use:**
> 1. Launch Jupyter from Docker (`http://localhost:8889`).
> 2. Open the desired notebook for your storage backend (local or MinIO).
> 3. Run the cells step by step to set up the environment, create tables, and load data.

This modular approach makes it easy to experiment with both local and S3-based Lakehouse setups, and to understand the configuration and data flow interactively.
