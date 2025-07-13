#!/usr/bin/env python3
"""
Script to generate sample transaction data for the banking reconciliation system.
"""

import os
import json
import uuid
import random
from datetime import datetime, timedelta
import pandas as pd
from faker import Faker

# Initialize Faker
fake = Faker()

# Define source systems
SOURCE_SYSTEMS = ['core_banking', 'card_processor', 'payment_gateway']

# Define transaction types
TRANSACTION_TYPES = ['deposit', 'withdrawal', 'transfer', 'payment', 'refund', 'fee']

# Define status values
STATUS_VALUES = ['completed', 'pending', 'failed', 'reversed']

def generate_account_ids(num_accounts=100):
    """Generate a list of random account IDs."""
    return [f"ACC{fake.unique.random_number(digits=8)}" for _ in range(num_accounts)]

def generate_transaction_id(source_system):
    """Generate a transaction ID with a prefix based on the source system."""
    prefixes = {
        'core_banking': 'CB',
        'card_processor': 'CP',
        'payment_gateway': 'PG'
    }
    prefix = prefixes.get(source_system, 'TX')
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"

def generate_reference_id():
    """Generate a reference ID for transactions."""
    return f"REF-{fake.unique.random_number(digits=10)}"

def generate_transaction_data(source_system, account_ids, start_date, end_date, count=1000):
    """Generate transaction data for a specific source system."""
    transactions = []

    for _ in range(count):
        # Generate random transaction date within the date range
        transaction_date = fake.date_time_between_dates(
            datetime_start=start_date,
            datetime_end=end_date
        )

        # Generate random amount (between $1 and $10,000)
        amount = round(random.uniform(1, 10000), 2)

        # Select random account ID
        account_id = random.choice(account_ids)

        # Generate transaction ID
        transaction_id = generate_transaction_id(source_system)

        # Select random transaction type
        transaction_type = random.choice(TRANSACTION_TYPES)

        # Generate reference ID
        reference_id = generate_reference_id()

        # Select random status
        status = random.choice(STATUS_VALUES)

        # Generate additional payload data
        payload = {
            'description': fake.sentence(),
            'location': fake.city(),
            'merchant': fake.company() if transaction_type in ['payment', 'refund'] else None,
            'category': fake.word(),
            'metadata': {
                'device': fake.user_agent(),
                'ip_address': fake.ipv4(),
                'channel': random.choice(['web', 'mobile', 'atm', 'branch', 'phone'])
            }
        }

        # Create transaction record
        transaction = {
            'transaction_id': transaction_id,
            'source_system': source_system,
            'transaction_date': transaction_date,
            'amount': amount,
            'account_id': account_id,
            'transaction_type': transaction_type,
            'reference_id': reference_id,
            'status': status,
            'payload': json.dumps(payload),
            'created_at': transaction_date - timedelta(minutes=random.randint(1, 60)),
            'processing_timestamp': transaction_date + timedelta(seconds=random.randint(1, 30))
        }

        transactions.append(transaction)

    return transactions

def create_matching_transactions(primary_transactions, secondary_system, error_rate=0.05):
    """
    Create matching transactions for a secondary system based on primary transactions.
    Introduces discrepancies based on the error rate.
    """
    secondary_transactions = []

    for primary_tx in primary_transactions:
        # Create a copy of the primary transaction
        secondary_tx = primary_tx.copy()

        # Change the transaction ID and source system
        secondary_tx['transaction_id'] = generate_transaction_id(secondary_system)
        secondary_tx['source_system'] = secondary_system

        # Introduce discrepancies based on error rate
        if random.random() < error_rate:
            # Choose a type of discrepancy
            discrepancy_type = random.choice(['amount', 'date', 'status', 'missing'])

            if discrepancy_type == 'amount':
                # Change the amount slightly
                original_amount = secondary_tx['amount']
                secondary_tx['amount'] = round(original_amount * random.uniform(0.95, 1.05), 2)

            elif discrepancy_type == 'date':
                # Shift the date slightly
                original_date = secondary_tx['transaction_date']
                secondary_tx['transaction_date'] = original_date + timedelta(
                    minutes=random.randint(-120, 120)
                )

            elif discrepancy_type == 'status':
                # Change the status
                original_status = secondary_tx['status']
                new_status = random.choice([s for s in STATUS_VALUES if s != original_status])
                secondary_tx['status'] = new_status

            elif discrepancy_type == 'missing':
                # Skip this transaction (don't add to secondary)
                continue

        secondary_transactions.append(secondary_tx)

    # Add some transactions that only exist in the secondary system
    extra_count = int(len(primary_transactions) * 0.02)  # 2% extra transactions
    account_ids = [tx['account_id'] for tx in primary_transactions]
    start_date = min(tx['transaction_date'] for tx in primary_transactions)
    end_date = max(tx['transaction_date'] for tx in primary_transactions)

    extra_transactions = generate_transaction_data(
        secondary_system,
        account_ids,
        start_date,
        end_date,
        count=extra_count
    )

    secondary_transactions.extend(extra_transactions)

    return secondary_transactions

def save_to_csv(transactions, filename):
    """Save transactions to a CSV file."""
    df = pd.DataFrame(transactions)

    # Convert datetime objects to strings
    for col in ['transaction_date', 'created_at', 'processing_timestamp']:
        df[col] = df[col].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))

    # Save to CSV
    df.to_csv(filename, index=False)
    print(f"Saved {len(transactions)} transactions to {filename}")

def main():
    """Main function to generate sample data."""
    print("Generating sample transaction data...")

    # Create data directory if it doesn't exist
    os.makedirs('/opt/bitnami/spark/data/raw', exist_ok=True)

    # Define date range for transactions (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    # Generate account IDs
    account_ids = generate_account_ids(num_accounts=100)

    # Generate primary transactions (core banking)
    primary_system = 'core_banking'
    primary_transactions = generate_transaction_data(
        primary_system,
        account_ids,
        start_date,
        end_date,
        count=5000
    )

    # Save primary transactions
    save_to_csv(
        primary_transactions,
        f'/opt/bitnami/spark/data/raw/{primary_system}_transactions.csv'
    )

    # Generate matching transactions for secondary systems
    for secondary_system in [s for s in SOURCE_SYSTEMS if s != primary_system]:
        secondary_transactions = create_matching_transactions(
            primary_transactions,
            secondary_system,
            error_rate=0.05
        )

        # Save secondary transactions
        save_to_csv(
            secondary_transactions,
            f'/opt/bitnami/spark/data/raw/{secondary_system}_transactions.csv'
        )

    print("Sample data generation complete.")

if __name__ == "__main__":
    main()
