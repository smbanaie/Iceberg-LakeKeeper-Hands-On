#!/bin/bash
# Setup script for the banking reconciliation system

# Create directories
mkdir -p data/raw data/stage data/reconciled

# Build and start Docker containers
echo "Building and starting Docker containers..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 15

# No MinIO initialization needed

# Initialize the Iceberg environment
echo "Initializing Iceberg environment..."
docker exec jupyter python /opt/bitnami/spark/scripts/init_iceberg.py

# Run tests to verify configuration
echo "Running tests to verify configuration..."
docker exec jupyter python /opt/bitnami/spark/scripts/run_tests.py

# Generate sample data
echo "Generating sample data..."
docker exec jupyter python /opt/bitnami/spark/scripts/generate_sample_data.py

# Load sample data into Iceberg tables
echo "Loading sample data into Iceberg tables..."
docker exec jupyter python /opt/bitnami/spark/scripts/ingest_data.py

echo "Setup completed successfully!"
echo "You can now access:"
echo "- Spark Master UI: http://localhost:8082"
echo "- Spark Worker UI: http://localhost:8083"
echo "- Jupyter Notebook: http://localhost:8889"
echo "- PostgreSQL: localhost:5432 (user: iceberg, password: iceberg)"
