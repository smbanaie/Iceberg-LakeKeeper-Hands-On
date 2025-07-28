#!/usr/bin/env python3
"""
Debezium Kafka Consumer for Iceberg Ingestion
============================================

This script reads Debezium messages from a Kafka topic and ingests them into
an Apache Iceberg table using the Lakekeeper catalog and MinIO storage.

Features:
- Reads Debezium CDC messages from Kafka
- Transforms data to match Iceberg table schema
- Handles timestamp conversion from string to datetime
- Batches writes for better performance
- Error handling and logging
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import time

# Kafka imports
from kafka import KafkaConsumer
from kafka.errors import KafkaError

# Iceberg imports
from pyiceberg.catalog.rest import RestCatalog
import pyarrow as pa
import pandas as pd

# Data processing
from datetime import datetime, timedelta
import pytz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DebeziumIcebergConsumer:
    """
    Consumer for Debezium messages that ingests data into Iceberg tables.
    """
    
    def __init__(self, 
                 kafka_bootstrap_servers: str,
                 kafka_topic: str,
                 kafka_group_id: str,
                 catalog_url: str,
                 warehouse: str,
                 namespace: str,
                 table_name: str,
                 batch_size: int = 100,
                 batch_timeout_seconds: int = 30):
        """
        Initialize the Debezium Iceberg consumer.
        
        Args:
            kafka_bootstrap_servers: Kafka bootstrap servers
            kafka_topic: Kafka topic to consume from
            kafka_group_id: Kafka consumer group ID
            catalog_url: Iceberg catalog URL
            warehouse: Iceberg warehouse name
            namespace: Iceberg namespace
            table_name: Iceberg table name
            batch_size: Number of records to batch before writing
            batch_timeout_seconds: Maximum time to wait before writing a batch
        """
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.kafka_topic = kafka_topic
        self.kafka_group_id = kafka_group_id
        self.catalog_url = catalog_url
        self.warehouse = warehouse
        self.namespace = namespace
        self.table_name = table_name
        self.batch_size = batch_size
        self.batch_timeout_seconds = batch_timeout_seconds
        
        # Initialize Kafka consumer
        self.consumer = None
        self._init_kafka_consumer()
        
        # Initialize Iceberg catalog and table
        self.catalog = None
        self.table = None
        self._init_iceberg_catalog()
        
        # Batch processing
        self.batch_records = []
        self.last_batch_time = time.time()
        
        logger.info("✅ DebeziumIcebergConsumer initialized successfully")
    
    def _init_kafka_consumer(self):
        """Initialize Kafka consumer."""
        try:
            self.consumer = KafkaConsumer(
                self.kafka_topic,
                bootstrap_servers=self.kafka_bootstrap_servers,
                group_id=self.kafka_group_id,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda m: m.decode('utf-8') if m else None,
                consumer_timeout_ms=1000,  # 1 second timeout
            )
            logger.info(f"✅ Kafka consumer initialized for topic: {self.kafka_topic}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Kafka consumer: {e}")
            raise
    
    def _init_iceberg_catalog(self):
        """Initialize Iceberg catalog and load table."""
        try:
            # Initialize catalog
            self.catalog = RestCatalog(
                name="irisa_catalog",
                warehouse=self.warehouse,
                uri=self.catalog_url,
                token="dummy",
            )
            logger.info("✅ Iceberg catalog initialized")
            
            # Load the table
            table_identifier = (self.namespace, self.table_name)
            self.table = self.catalog.load_table(table_identifier)
            logger.info(f"✅ Iceberg table loaded: {self.namespace}.{self.table_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Iceberg catalog: {e}")
            raise
    
    def _parse_debezium_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """
        Parse Debezium timestamp string to datetime object.
        
        Args:
            timestamp_str: Timestamp string from Debezium message
            
        Returns:
            datetime object or None if parsing fails
        """
        if not timestamp_str:
            return None
            
        try:
            # Try different timestamp formats
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S.%fZ',
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue
            
            # If none of the formats work, try parsing as ISO format
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to parse timestamp '{timestamp_str}': {e}")
            return None
    
    def _transform_debezium_record(self, debezium_msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Transform a Debezium message to Iceberg table format.
        
        Args:
            debezium_msg: Debezium message dictionary
            
        Returns:
            Transformed record or None if transformation fails
        """
        try:
            # Extract the 'after' data from the Debezium message
            if 'after' not in debezium_msg:
                logger.warning("⚠️ No 'after' data found in Debezium message")
                return None
            
            after_data = debezium_msg['after']
            
            # Transform the record
            transformed_record = {
                'Id': after_data.get('Id'),
                'TelegramCode': after_data.get('TelegramCode'),
                'Source': after_data.get('Source'),
                'Destination': after_data.get('Destination'),
                'Body': after_data.get('Body'),
            }
            
            # Parse timestamps
            date_in_str = after_data.get('DateIn')
            date_out_str = after_data.get('DateOut')
            
            transformed_record['DateIn'] = self._parse_debezium_timestamp(date_in_str)
            transformed_record['DateOut'] = self._parse_debezium_timestamp(date_out_str)
            
            # Validate required fields
            if transformed_record['Id'] is None:
                logger.warning("⚠️ Record missing required 'Id' field")
                return None
            
            logger.debug(f"✅ Transformed record: ID={transformed_record['Id']}")
            return transformed_record
            
        except Exception as e:
            logger.error(f"❌ Failed to transform Debezium record: {e}")
            return None
    
    def _write_batch_to_iceberg(self, records: List[Dict[str, Any]]):
        """
        Write a batch of records to the Iceberg table.
        
        Args:
            records: List of transformed records
        """
        if not records:
            return
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(records)
            
            # Convert timestamps to microsecond precision
            if 'DateIn' in df.columns:
                df['DateIn'] = pd.to_datetime(df['DateIn']).dt.floor('us')
            if 'DateOut' in df.columns:
                df['DateOut'] = pd.to_datetime(df['DateOut']).dt.floor('us')
            
            # Convert to PyArrow table with explicit schema
            arrow_table = pa.Table.from_pandas(df, schema=pa.schema([
                pa.field("Id", pa.int32(), nullable=False),
                pa.field("TelegramCode", pa.int32(), nullable=True),
                pa.field("Source", pa.int32(), nullable=True),
                pa.field("Destination", pa.int32(), nullable=True),
                pa.field("DateIn", pa.timestamp('us'), nullable=True),
                pa.field("DateOut", pa.timestamp('us'), nullable=True),
                pa.field("Body", pa.string(), nullable=True),
            ]))
            
            # Append to Iceberg table
            self.table.append(arrow_table)
            
            logger.info(f"✅ Successfully wrote {len(records)} records to Iceberg table")
            
        except Exception as e:
            logger.error(f"❌ Failed to write batch to Iceberg: {e}")
            raise
    
    def _should_flush_batch(self) -> bool:
        """Check if the current batch should be flushed."""
        current_time = time.time()
        return (len(self.batch_records) >= self.batch_size or 
                (self.batch_records and 
                 current_time - self.last_batch_time >= self.batch_timeout_seconds))
    
    def _flush_batch(self):
        """Flush the current batch to Iceberg."""
        if self.batch_records:
            self._write_batch_to_iceberg(self.batch_records)
            self.batch_records = []
            self.last_batch_time = time.time()
    
    def process_message(self, message):
        """
        Process a single Debezium message.
        
        Args:
            message: Kafka message object
        """
        try:
            # Parse the Debezium message
            debezium_data = message.value
            
            # Check if this is a data change event (not schema change)
            if 'payload' in debezium_data:
                payload = debezium_data['payload']
                
                # Transform the record
                transformed_record = self._transform_debezium_record(payload)
                
                if transformed_record:
                    # Add to batch
                    self.batch_records.append(transformed_record)
                    
                    # Check if we should flush the batch
                    if self._should_flush_batch():
                        self._flush_batch()
                        
            else:
                logger.debug("ℹ️ Skipping non-data message")
                
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
    
    def consume_messages(self, max_messages: Optional[int] = None):
        """
        Start consuming messages from Kafka.
        
        Args:
            max_messages: Maximum number of messages to consume (None for unlimited)
        """
        logger.info(f"🚀 Starting to consume messages from topic: {self.kafka_topic}")
        
        message_count = 0
        
        try:
            for message in self.consumer:
                message_count += 1
                
                logger.debug(f"📨 Processing message {message_count}")
                self.process_message(message)
                
                # Check if we've reached the maximum messages
                if max_messages and message_count >= max_messages:
                    logger.info(f"✅ Reached maximum messages ({max_messages})")
                    break
                    
        except KeyboardInterrupt:
            logger.info("⏹️ Received interrupt signal, stopping consumer")
        except Exception as e:
            logger.error(f"❌ Error in message consumption: {e}")
        finally:
            # Flush any remaining records
            self._flush_batch()
            
            # Close consumer
            if self.consumer:
                self.consumer.close()
            
            logger.info("✅ Consumer stopped")


def main():
    """Main function to run the Debezium Kafka consumer."""
    
    # Configuration (matching the notebook settings)
    KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"  # Adjust as needed
    KAFKA_TOPIC = "fake_sl.dbo.fake_seclink"    # Debezium topic name
    KAFKA_GROUP_ID = "iceberg-consumer-group"
    
    # Iceberg configuration (from notebook)
    CATALOG_URL = "http://lakekeeper:8181/catalog"
    WAREHOUSE = "irisa-ot"
    NAMESPACE = "irisa"
    TABLE_NAME = "fake_seclink"
    
    # Batch configuration
    BATCH_SIZE = 100
    BATCH_TIMEOUT_SECONDS = 30
    
    # Create and run the consumer
    consumer = DebeziumIcebergConsumer(
        kafka_bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        kafka_topic=KAFKA_TOPIC,
        kafka_group_id=KAFKA_GROUP_ID,
        catalog_url=CATALOG_URL,
        warehouse=WAREHOUSE,
        namespace=NAMESPACE,
        table_name=TABLE_NAME,
        batch_size=BATCH_SIZE,
        batch_timeout_seconds=BATCH_TIMEOUT_SECONDS
    )
    
    # Start consuming messages
    consumer.consume_messages()


if __name__ == "__main__":
    main() 