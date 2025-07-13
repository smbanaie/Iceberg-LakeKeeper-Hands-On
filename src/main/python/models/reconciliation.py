"""
Reconciliation models for the banking reconciliation system.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List


@dataclass
class ReconciliationResult:
    """
    Represents the result of reconciling two transactions.
    """
    reconciliation_id: str
    batch_id: str
    primary_transaction_id: str
    secondary_transaction_id: Optional[str]
    match_status: str  # 'MATCHED', 'UNMATCHED', 'PARTIAL'
    discrepancy_type: Optional[str] = None  # 'AMOUNT', 'DATE', 'STATUS', etc.
    discrepancy_amount: Optional[Decimal] = None
    reconciliation_timestamp: Optional[datetime] = None
    notes: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReconciliationResult':
        """
        Create a ReconciliationResult instance from a dictionary.
        
        Args:
            data: Dictionary containing reconciliation data
            
        Returns:
            ReconciliationResult instance
        """
        # Convert string dates to datetime objects if needed
        if 'reconciliation_timestamp' in data and isinstance(data['reconciliation_timestamp'], str):
            data['reconciliation_timestamp'] = datetime.fromisoformat(
                data['reconciliation_timestamp'].replace('Z', '+00:00')
            )
        
        # Convert discrepancy_amount to Decimal if it's a string
        if 'discrepancy_amount' in data and isinstance(data['discrepancy_amount'], str):
            data['discrepancy_amount'] = Decimal(data['discrepancy_amount'])
        
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the ReconciliationResult instance to a dictionary.
        
        Returns:
            Dictionary representation of the reconciliation result
        """
        result = {
            'reconciliation_id': self.reconciliation_id,
            'batch_id': self.batch_id,
            'primary_transaction_id': self.primary_transaction_id,
            'secondary_transaction_id': self.secondary_transaction_id,
            'match_status': self.match_status
        }
        
        if self.discrepancy_type:
            result['discrepancy_type'] = self.discrepancy_type
        
        if self.discrepancy_amount:
            result['discrepancy_amount'] = str(self.discrepancy_amount)
        
        if self.reconciliation_timestamp:
            result['reconciliation_timestamp'] = self.reconciliation_timestamp.isoformat()
        
        if self.notes:
            result['notes'] = self.notes
        
        return result


@dataclass
class ReconciliationBatch:
    """
    Represents a batch of reconciliation operations.
    """
    batch_id: str
    reconciliation_date: datetime
    source_systems: List[str]
    start_date: datetime
    end_date: datetime
    status: str  # 'PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED'
    total_transactions: int = 0
    matched_count: int = 0
    unmatched_count: int = 0
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReconciliationBatch':
        """
        Create a ReconciliationBatch instance from a dictionary.
        
        Args:
            data: Dictionary containing batch data
            
        Returns:
            ReconciliationBatch instance
        """
        # Convert string dates to datetime objects if needed
        for date_field in ['reconciliation_date', 'start_date', 'end_date', 'created_at', 'completed_at']:
            if date_field in data and isinstance(data[date_field], str):
                data[date_field] = datetime.fromisoformat(data[date_field].replace('Z', '+00:00'))
        
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the ReconciliationBatch instance to a dictionary.
        
        Returns:
            Dictionary representation of the reconciliation batch
        """
        result = {
            'batch_id': self.batch_id,
            'reconciliation_date': self.reconciliation_date.isoformat(),
            'source_systems': self.source_systems,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'status': self.status,
            'total_transactions': self.total_transactions,
            'matched_count': self.matched_count,
            'unmatched_count': self.unmatched_count
        }
        
        if self.created_at:
            result['created_at'] = self.created_at.isoformat()
        
        if self.completed_at:
            result['completed_at'] = self.completed_at.isoformat()
        
        return result
