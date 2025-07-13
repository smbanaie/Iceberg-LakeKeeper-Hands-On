#!/bin/bash
# Setup script for the banking reconciliation system

# Create directories
mkdir -p data/raw data/stage data/reconciled

# Build and start Docker containers
echo "Building and starting Docker containers..."
docker-compose -f docker/docker-compose.yml up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 20

# Wait for MinIO to be ready
echo "Waiting for MinIO to be ready..."
max_attempts=30
attempt=1
while [ $attempt -le $max_attempts ]; do
    if curl -s http://localhost:9000/minio/health/live >/dev/null 2>&1; then
        echo "MinIO is ready!"
        break
    fi
    echo "Waiting for MinIO... (attempt $attempt/$max_attempts)"
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    echo "MinIO failed to start within the expected time. Continuing anyway..."
fi

# Initialize MinIO buckets
echo "Initializing MinIO buckets..."
docker exec jupyter python /opt/bitnami/spark/scripts/init_minio.py

# Wait a bit more for buckets to be fully created
sleep 5

# Initialize the Iceberg environment
echo "Initializing Iceberg environment..."
docker exec jupyter python /opt/bitnami/spark/scripts/init_iceberg.py

# Test the setup
echo "Testing the setup..."
docker exec jupyter python /opt/bitnami/spark/scripts/test_setup.py

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
echo "- MinIO Console: http://localhost:9001 (login: minio / minio123)"
echo "- PostgreSQL: localhost:5432 (user: iceberg, password: iceberg)"
