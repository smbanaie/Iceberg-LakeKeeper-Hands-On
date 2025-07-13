#!/usr/bin/env python3
"""
Simple test script for the banking reconciliation system.
This script demonstrates the basic functionality without requiring the full Docker environment.
"""

import os
import uuid
import pandas as pd
from datetime import datetime, timedelta

# Create sample data directories if they don't exist
os.makedirs('data/raw', exist_ok=True)
os.makedirs('data/stage', exist_ok=True)
os.makedirs('data/reconciled', exist_ok=True)

print("=== Apache Iceberg Banking Reconciliation System - Simple Test ===")
print("This script demonstrates the basic functionality without the full Docker environment.")

# Generate sample transaction data
print("\n1. Generating sample transaction data...")

# Define source systems
SOURCE_SYSTEMS = ['core_banking', 'card_processor', 'payment_gateway']

# Sample transaction data for core_banking
core_banking_data = [
    {
        'transaction_id': f"CB-{uuid.uuid4().hex[:8].upper()}",
        'source_system': 'core_banking',
        'transaction_date': (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d %H:%M:%S'),
        'amount': round(100 + i * 10, 2),
        'account_id': f"ACC{10000 + i}",
        'transaction_type': 'payment',
        'reference_id': f"REF-{1000000 + i}",
        'status': 'completed',
        'payload': '{"description": "Sample transaction"}',
        'created_at': (datetime.now() - timedelta(days=i, minutes=30)).strftime('%Y-%m-%d %H:%M:%S'),
        'processing_timestamp': (datetime.now() - timedelta(days=i, minutes=15)).strftime('%Y-%m-%d %H:%M:%S')
    }
    for i in range(10)
]

# Sample transaction data for card_processor (with some discrepancies)
card_processor_data = [
    {
        'transaction_id': f"CP-{uuid.uuid4().hex[:8].upper()}",
        'source_system': 'card_processor',
        'transaction_date': (datetime.now() - timedelta(days=i, minutes=5)).strftime('%Y-%m-%d %H:%M:%S'),  # Slight time difference
        'amount': round(100 + i * 10, 2) if i % 3 != 0 else round(100 + i * 10 + 0.5, 2),  # Some amount discrepancies
        'account_id': f"ACC{10000 + i}",
        'transaction_type': 'payment',
        'reference_id': f"REF-{1000000 + i}",
        'status': 'completed' if i % 4 != 0 else 'pending',  # Some status discrepancies
        'payload': '{"description": "Card transaction"}',
        'created_at': (datetime.now() - timedelta(days=i, minutes=25)).strftime('%Y-%m-%d %H:%M:%S'),
        'processing_timestamp': (datetime.now() - timedelta(days=i, minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
    }
    for i in range(9)  # One missing transaction
]

# Add a transaction that only exists in card_processor
card_processor_data.append({
    'transaction_id': f"CP-{uuid.uuid4().hex[:8].upper()}",
    'source_system': 'card_processor',
    'transaction_date': (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d %H:%M:%S'),
    'amount': 500.00,
    'account_id': "ACC20000",
    'transaction_type': 'refund',
    'reference_id': "REF-2000000",
    'status': 'completed',
    'payload': '{"description": "Card refund"}',
    'created_at': (datetime.now() - timedelta(days=15, minutes=30)).strftime('%Y-%m-%d %H:%M:%S'),
    'processing_timestamp': (datetime.now() - timedelta(days=15, minutes=15)).strftime('%Y-%m-%d %H:%M:%S')
})

# Save sample data to CSV files
core_banking_df = pd.DataFrame(core_banking_data)
card_processor_df = pd.DataFrame(card_processor_data)

core_banking_df.to_csv('data/raw/core_banking_transactions.csv', index=False)
card_processor_df.to_csv('data/raw/card_processor_transactions.csv', index=False)

print(f"Generated {len(core_banking_data)} core banking transactions")
print(f"Generated {len(card_processor_data)} card processor transactions")

# Simulate transaction matching and reconciliation
print("\n2. Performing transaction reconciliation...")

# Load the data
core_banking_df = pd.read_csv('data/raw/core_banking_transactions.csv')
card_processor_df = pd.read_csv('data/raw/card_processor_transactions.csv')

# Match transactions based on account_id and amount
matched = []
unmatched_core = []
unmatched_card = []

# Track processed card transactions
processed_card_indices = set()

# For each core banking transaction, find a matching card transaction
for idx_core, core_tx in core_banking_df.iterrows():
    found_match = False
    
    for idx_card, card_tx in card_processor_df.iterrows():
        if idx_card in processed_card_indices:
            continue
            
        # Check if account_id matches
        if core_tx['account_id'] == card_tx['account_id']:
            # Check if amount is within tolerance (exact or small difference)
            amount_diff = abs(float(core_tx['amount']) - float(card_tx['amount']))
            if amount_diff <= 1.0:  # $1 tolerance
                # We have a match
                match_status = "MATCHED" if amount_diff == 0 and core_tx['status'] == card_tx['status'] else "PARTIAL"
                discrepancy_type = None
                
                if amount_diff > 0:
                    discrepancy_type = "AMOUNT"
                elif core_tx['status'] != card_tx['status']:
                    discrepancy_type = "STATUS"
                
                matched.append({
                    'reconciliation_id': str(uuid.uuid4()),
                    'batch_id': 'BATCH-001',
                    'primary_transaction_id': core_tx['transaction_id'],
                    'secondary_transaction_id': card_tx['transaction_id'],
                    'match_status': match_status,
                    'discrepancy_type': discrepancy_type,
                    'discrepancy_amount': amount_diff if amount_diff > 0 else None,
                    'reconciliation_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'notes': f"{'Exact match' if match_status == 'MATCHED' else 'Partial match with discrepancies'}"
                })
                
                processed_card_indices.add(idx_card)
                found_match = True
                break
    
    if not found_match:
        unmatched_core.append({
            'reconciliation_id': str(uuid.uuid4()),
            'batch_id': 'BATCH-001',
            'primary_transaction_id': core_tx['transaction_id'],
            'secondary_transaction_id': None,
            'match_status': 'UNMATCHED',
            'discrepancy_type': 'MISSING_SECONDARY',
            'discrepancy_amount': float(core_tx['amount']),
            'reconciliation_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'notes': f"Transaction in core_banking not found in card_processor"
        })

# Find unmatched card transactions
for idx_card, card_tx in card_processor_df.iterrows():
    if idx_card not in processed_card_indices:
        unmatched_card.append({
            'reconciliation_id': str(uuid.uuid4()),
            'batch_id': 'BATCH-001',
            'primary_transaction_id': None,
            'secondary_transaction_id': card_tx['transaction_id'],
            'match_status': 'UNMATCHED',
            'discrepancy_type': 'MISSING_PRIMARY',
            'discrepancy_amount': float(card_tx['amount']),
            'reconciliation_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'notes': f"Transaction in card_processor not found in core_banking"
        })

# Combine all results
all_results = matched + unmatched_core + unmatched_card
results_df = pd.DataFrame(all_results)

# Save reconciliation results
results_df.to_csv('data/reconciled/reconciliation_results.csv', index=False)

# Generate summary
print("\n3. Reconciliation Summary:")
print(f"Total transactions processed: {len(core_banking_df) + len(card_processor_df)}")
print(f"Matched transactions: {len(matched)}")
print(f"Unmatched core banking transactions: {len(unmatched_core)}")
print(f"Unmatched card processor transactions: {len(unmatched_card)}")

# Calculate match rate
match_rate = len(matched) / (len(matched) + len(unmatched_core) + len(unmatched_card)) * 100
print(f"Match rate: {match_rate:.2f}%")

# Display some sample results
print("\n4. Sample Reconciliation Results:")
if matched:
    print("\nMatched Transactions (sample):")
    print(pd.DataFrame(matched[:3]))

if unmatched_core:
    print("\nUnmatched Core Banking Transactions (sample):")
    print(pd.DataFrame(unmatched_core[:3]))

if unmatched_card:
    print("\nUnmatched Card Processor Transactions (sample):")
    print(pd.DataFrame(unmatched_card[:3]))

print("\nReconciliation results saved to data/reconciled/reconciliation_results.csv")
print("\nTest completed successfully!")
