# Apache Iceberg Banking Reconciliation Demo: Multi-Engine, Multi-Catalog Lakehouse

## 🚀 What is This Repo?

This repository demonstrates **practical adoption of Apache Iceberg** for a banking system, with hands-on, end-to-end samples for:
- **Hadoop Local Catalog** (file-based, no external services)
- **Hadoop Catalog with MinIO S3 Storage** (S3A-compatible, MinIO-backed)
- **Lakekeeper REST Catalog** (Iceberg REST catalog with **Postgres** for metadata and **MinIO** for storage)

It showcases **multi-engine access** to the same Iceberg tables using:
- **Spark**
- **DuckDB**
- **PyIceberg**
- **Trino**
- **StarRocks**

All scenarios are fully containerized with Docker Compose and feature interactive Jupyter notebooks for setup, data generation, and analytics.

---

## 🏦 Why Banking Reconciliation?

Banks operate multiple systems (core banking, card processors, payment gateways). Reconciliation ensures data consistency by matching transactions across these systems, identifying exceptions, and maintaining audit trails for compliance.

This repo provides:
- Realistic multi-system transaction data
- Advanced reconciliation logic
- Full auditability and time travel
- Schema evolution and ACID guarantees

---

## 🏗️ Architecture Overview

### Modes Supported

| Mode                        | Catalog Type         | Metadata Storage | Data Storage | Multi-Engine? | Compose File                        |
|-----------------------------|---------------------|------------------|--------------|--------------|-------------------------------------|
| Hadoop Local Catalog        | Hadoop (file-based) | Local FS         | Local FS     | Spark        | `docker/compose-hadoop-catalog.yml` |
| Hadoop Catalog + MinIO S3   | Hadoop (file-based) | Local FS         | MinIO (S3A)  | Spark        | `docker/compose-hadoop-catalog.yml` |
| Lakekeeper REST Catalog     | REST (Lakekeeper)   | **Postgres**     | MinIO (S3A)  | Spark, DuckDB, PyIceberg, Trino, StarRocks | `docker/compose-lakekeeper-minimal.yaml` |

### Key Points
- **Lakekeeper**: All schema creation, table changes, and lake operations are managed and tracked in **Postgres** (full auditability, multi-engine consistency).
- **MinIO**: S3-compatible object storage for all data and metadata in S3-backed modes.
- **Jupyter Notebooks**: All setup, data generation, and analytics are performed interactively.

---

## 🧑‍💻 How to Run Each Scenario

### 1. Hadoop Local Catalog (File-Based)
- Start services:
  ```bash
  docker compose -f docker/compose-hadoop-catalog.yml up
  ```
- Open Jupyter: [http://localhost:8889](http://localhost:8889)
- Run:
  - `notebooks/01_Phase1_complete_setup_hadoop_catalog_local_storage.ipynb`
  - `notebooks/01_Phase2_complete_setup_hadoop_catalog_local_storage.ipynb`
  - `notebooks/01_Phase3_iceberg_banking_reconciliation_demo.ipynb`

### 2. Hadoop Catalog with MinIO S3 Storage
- Start services (same as above):
  ```bash
  docker compose -f docker/compose-hadoop-catalog.yml up
  ```
- Open Jupyter: [http://localhost:8889](http://localhost:8889)
- Run:
  - `notebooks/02_Phase1_complete_setup_hadoop_catalog_minio_storage.ipynb`
  - `notebooks/02_Phase2_complete_setup_hadoop_catalog_minio_storage.ipynb`

### 3. Lakekeeper REST Catalog (Multi-Engine, Multi-User)
- Start core services:
  ```bash
  docker compose -f docker/compose-lakekeeper-minimal.yaml up
  ```
- **To enable Trino or StarRocks, use Docker Compose profiles:**
  - Trino:
    ```bash
    docker compose -f docker/compose-lakekeeper-minimal.yaml --profile trino up
    ```
  - StarRocks:
    ```bash
    docker compose -f docker/compose-lakekeeper-minimal.yaml --profile starrocks up
    ```
- Open Jupyter: [http://localhost:8889](http://localhost:8889)
- Run Lakekeeper notebooks:
  - `notebooks/lakekeeper-notebooks/01_Phase1_complete_setup_lakekeeper_catalog_minio_storage.ipynb`
  - `notebooks/lakekeeper-notebooks/02_Phase2_complete_setup_lakekeeper_catalog_minio_storage.ipynb`
  - `notebooks/lakekeeper-notebooks/03_Phase3_iceberg_banking_reconciliation_demo.ipynb`
  - Multi-engine demos:
    - `notebooks/lakekeeper-notebooks/DuckDB.ipynb`
    - `notebooks/lakekeeper-notebooks/Pyiceberg.ipynb`
    - `notebooks/lakekeeper-notebooks/Spark.ipynb`
    - `notebooks/lakekeeper-notebooks/Trino.ipynb`
    - `notebooks/lakekeeper-notebooks/Starrocks.ipynb`
    - `notebooks/lakekeeper-notebooks/Multiple Warehouses.ipynb`

---

## 🛠️ Customizing Warehouse Names and Configs

- **Lakekeeper**: Edit `docker/create-default-warehouse.json` or the relevant notebook cell to change the initial warehouse name, S3 bucket, or endpoint.
- **Hadoop/MinIO**: Edit the warehouse path in the Spark config cell in the notebook.
- **Lakekeeper UI**: Access [http://localhost:8181/ui/warehouse](http://localhost:8181/ui/warehouse) to view and manage warehouses and namespaces.

---

## 🧩 Lakekeeper: Multi-Engine Access

Lakekeeper enables seamless access to the same Iceberg tables from multiple engines:

- **Spark**: Use the REST catalog config in your Spark session (see `Spark.ipynb`).
- **DuckDB**: Install the ICEBERG extension and attach the Lakekeeper warehouse (see `DuckDB.ipynb`).
- **PyIceberg**: Use the REST catalog to read/write tables (see `Pyiceberg.ipynb`).
- **Trino**: Create a Trino catalog using the REST catalog and connect (see `Trino.ipynb`).
- **StarRocks**: Create an external catalog in StarRocks using the REST catalog (see `Starrocks.ipynb`).

**Note:** For Trino and StarRocks, you must specify the Docker Compose profile to start the service.

---

## 🗄️ Postgres Role in Lakekeeper

- **All schema creation, table changes, and lake operations are managed and tracked in Postgres** (the Lakekeeper metadata database).
- This enables strong auditability, time travel, and multi-engine consistency.
- You can inspect the Postgres database to see all namespaces, tables, and changes.

---

## 📒 Notebooks Overview

| Scenario                | Notebook(s)                                                                                 |
|-------------------------|--------------------------------------------------------------------------------------------|
| Hadoop Local Catalog    | 01_Phase1_complete_setup_hadoop_catalog_local_storage, 01_Phase2..., 01_Phase3...          |
| Hadoop + MinIO S3       | 02_Phase1_complete_setup_hadoop_catalog_minio_storage, 02_Phase2...                        |
| Lakekeeper REST Catalog | 01_Phase1_complete_setup_lakekeeper_catalog_minio_storage, 02_Phase2..., 03_Phase3...      |
| Lakekeeper Multi-Engine | DuckDB, Pyiceberg, Spark, Trino, Starrocks, Multiple Warehouses                            |

All notebooks are in `notebooks/` or `notebooks/lakekeeper-notebooks/`.

---

## 🧑‍🔬 How to Customize and Extend
- **Change warehouse names, S3 buckets, or endpoints** by editing the relevant notebook cell or `create-default-warehouse.json`.
- **Add new tables or schemas** by modifying the notebook SQL cells.
- **Experiment with multi-engine access** by running the corresponding engine notebook.

---

## 🛡️ Troubleshooting & Tips
- **Trino/StarRocks not available?** Make sure to use the correct Docker Compose profile (`--profile trino` or `--profile starrocks`).
- **MinIO/Trino/StarRocks health checks**: Wait for all containers to be healthy before running notebooks.
- **Permissions**: If you see permission errors, ensure your data and scripts folders are accessible to Docker.
- **Lakekeeper UI**: Use [http://localhost:8181/ui/warehouse](http://localhost:8181/ui/warehouse) to inspect and manage your lake.
- **Postgres**: All metadata and changes are tracked in the Lakekeeper Postgres database for full auditability.

---

## 🗂️ Quick Reference Table

| Scenario                | Compose File                              | Notebooks Directory                | Key Notebooks / Notes                                 |
|-------------------------|-------------------------------------------|------------------------------------|------------------------------------------------------|
| Hadoop Local Catalog    | docker/compose-hadoop-catalog.yml         | notebooks/                         | 01_Phase1..., 01_Phase2..., 01_Phase3...             |
| Hadoop + MinIO S3       | docker/compose-hadoop-catalog.yml         | notebooks/                         | 02_Phase1..., 02_Phase2...                            |
| Lakekeeper REST Catalog | docker/compose-lakekeeper-minimal.yaml    | notebooks/lakekeeper-notebooks/    | 01_Phase1..., 02_Phase2..., 03_Phase3...              |
| Lakekeeper + Trino      | docker/compose-lakekeeper-minimal.yaml    | notebooks/lakekeeper-notebooks/    | Trino.ipynb (use `--profile trino`)                   |
| Lakekeeper + StarRocks  | docker/compose-lakekeeper-minimal.yaml    | notebooks/lakekeeper-notebooks/    | Starrocks.ipynb (use `--profile starrocks`)           |
| Lakekeeper Multi-Engine | docker/compose-lakekeeper-minimal.yaml    | notebooks/lakekeeper-notebooks/    | DuckDB, Pyiceberg, Spark, Trino, Starrocks, Multiple Warehouses |

---

## 📚 Advanced Features
- **Schema Evolution**: Add/drop/rename columns without rebuilding tables
- **Time Travel**: Query data at any point in time
- **ACID Transactions**: Atomic operations across multiple tables
- **Partition Evolution**: Change partitioning strategy without data migration
- **Incremental Processing**: Process only new data since last run

---

## 🏁 Contributing & Support
- Fork, branch, and PR as usual
- See the troubleshooting section for common issues
- For questions, open an issue with logs and system info

---

## 📝 License
MIT
