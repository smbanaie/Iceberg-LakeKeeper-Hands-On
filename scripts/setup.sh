#!/bin/bash
# Setup script for the banking reconciliation system

# Create directories
mkdir -p data/raw data/stage data/reconciled

# Build and start Docker containers
echo "Building and starting Docker containers..."
cd docker && docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 15

# Initialize the Iceberg environment
echo "Initializing Iceberg environment..."
docker exec -it jupyter python /opt/bitnami/spark/scripts/init_iceberg.py

# Generate sample data
echo "Generating sample data..."
docker exec -it jupyter python /opt/bitnami/spark/scripts/generate_sample_data.py

# Load sample data into Iceberg tables
echo "Loading sample data into Iceberg tables..."
docker exec -it jupyter python /opt/bitnami/spark/scripts/ingest_data.py

echo "Setup completed successfully!"
echo "You can now access:"
echo "- Spark Master UI: http://localhost:8082"
echo "- Spark Worker UI: http://localhost:8083"
echo "- Jupyter Notebook: http://localhost:8889"
echo "- MinIO Console: http://localhost:9001 (login: minio / minio123)"
