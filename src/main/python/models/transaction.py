"""
Transaction model for the banking reconciliation system.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any


@dataclass
class Transaction:
    """
    Represents a financial transaction from any source system.
    """
    transaction_id: str
    source_system: str
    transaction_date: datetime
    amount: Decimal
    account_id: str
    transaction_type: str
    reference_id: str
    status: str
    payload: Optional[str] = None
    created_at: Optional[datetime] = None
    processing_timestamp: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        """
        Create a Transaction instance from a dictionary.
        
        Args:
            data: Dictionary containing transaction data
            
        Returns:
            Transaction instance
        """
        # Convert string dates to datetime objects if needed
        for date_field in ['transaction_date', 'created_at', 'processing_timestamp']:
            if date_field in data and isinstance(data[date_field], str):
                data[date_field] = datetime.fromisoformat(data[date_field].replace('Z', '+00:00'))
        
        # Convert amount to Decimal if it's a string
        if 'amount' in data and isinstance(data['amount'], str):
            data['amount'] = Decimal(data['amount'])
        
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Transaction instance to a dictionary.
        
        Returns:
            Dictionary representation of the transaction
        """
        result = {
            'transaction_id': self.transaction_id,
            'source_system': self.source_system,
            'transaction_date': self.transaction_date.isoformat(),
            'amount': str(self.amount),
            'account_id': self.account_id,
            'transaction_type': self.transaction_type,
            'reference_id': self.reference_id,
            'status': self.status,
            'payload': self.payload
        }
        
        if self.created_at:
            result['created_at'] = self.created_at.isoformat()
        
        if self.processing_timestamp:
            result['processing_timestamp'] = self.processing_timestamp.isoformat()
        
        return result
    
    def __str__(self) -> str:
        """String representation of the transaction."""
        return (
            f"Transaction(id={self.transaction_id}, "
            f"system={self.source_system}, "
            f"date={self.transaction_date.strftime('%Y-%m-%d %H:%M:%S')}, "
            f"amount={self.amount}, "
            f"account={self.account_id}, "
            f"type={self.transaction_type}, "
            f"status={self.status})"
        )
