#!/usr/bin/env python3
"""
Script to initialize MinIO buckets for the banking reconciliation system.
"""

import boto3
from botocore.client import Config
import time
import sys

def initialize_minio_buckets():
    """Initialize MinIO buckets for data storage."""
    print("Initializing MinIO buckets...")
    
    # Initialize MinIO client
    s3_client = boto3.client(
        's3',
        endpoint_url='http://minio:9000',
        aws_access_key_id='minio',
        aws_secret_access_key='minio123',
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'
    )
    
    # Create buckets if they don't exist
    buckets = ['warehouse', 'raw-data', 'stage-data', 'reconciled-data']
    
    # List existing buckets
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            existing_buckets = [bucket['Name'] for bucket in s3_client.list_buckets()['Buckets']]
            print(f"Existing buckets: {existing_buckets}")
            break
        except Exception as e:
            retry_count += 1
            print(f"Error listing buckets (attempt {retry_count}/{max_retries}): {str(e)}")
            if retry_count >= max_retries:
                print("Failed to connect to MinIO after multiple attempts. Exiting.")
                sys.exit(1)
            print("Waiting for MinIO to be ready...")
            time.sleep(5)  # Wait for MinIO to be ready
    
    # Create missing buckets
    for bucket in buckets:
        if bucket not in existing_buckets:
            try:
                s3_client.create_bucket(Bucket=bucket)
                print(f"Created bucket: {bucket}")
            except Exception as e:
                print(f"Error creating bucket {bucket}: {str(e)}")
        else:
            print(f"Bucket already exists: {bucket}")

def main():
    """Main function to initialize MinIO buckets."""
    print("Starting MinIO initialization...")
    initialize_minio_buckets()
    print("MinIO initialization completed successfully.")

if __name__ == "__main__":
    main()
