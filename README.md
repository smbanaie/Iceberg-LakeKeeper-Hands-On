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
2. Run `docker-compose up -d` to start the environment
3. Access Jupyter notebooks at http://localhost:8888
4. Follow the example notebooks to understand the system

## Advanced Iceberg Features Demonstrated
- **Schema Evolution**: Add new fields to transaction tables without rebuilding
- **Time Travel**: Query historical reconciliation states for audit
- **Partition Evolution**: Optimize partitioning based on query patterns
- **Optimized Reads**: Leverage predicate pushdown and file pruning
- **ACID Transactions**: Ensure consistency during reconciliation
- **Incremental Processing**: Process only new transactions since last run

## License
[MIT License](LICENSE)
