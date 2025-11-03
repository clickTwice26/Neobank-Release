from datetime import datetime
from bson.objectid import ObjectId

class Transaction:
    """Transaction model for expenses and income"""
    
    TRANSACTION_TYPES = ['expense', 'income']
    
    CATEGORIES = {
        'expense': [
            'Food & Dining',
            'Transportation',
            'Shopping',
            'Entertainment',
            'Bills & Utilities',
            'Healthcare',
            'Education',
            'Other'
        ],
        'income': [
            'Salary',
            'Freelance',
            'Investment',
            'Gift',
            'Other'
        ]
    }
    
    def __init__(self, amount, category, description, transaction_type, date=None, _id=None):
        self._id = _id or ObjectId()
        self.amount = float(amount)
        self.category = category
        self.description = description
        self.transaction_type = transaction_type
        self.date = date or datetime.now()
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self):
        """Convert transaction to dictionary"""
        return {
            '_id': self._id,
            'amount': self.amount,
            'category': self.category,
            'description': self.description,
            'transaction_type': self.transaction_type,
            'date': self.date,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @staticmethod
    def from_dict(data):
        """Create transaction from dictionary"""
        return Transaction(
            amount=data.get('amount'),
            category=data.get('category'),
            description=data.get('description'),
            transaction_type=data.get('transaction_type'),
            date=data.get('date'),
            _id=data.get('_id')
        )
    
    def validate(self):
        """Validate transaction data"""
        errors = []
        
        if not self.amount or self.amount <= 0:
            errors.append('Amount must be greater than 0')
        
        if self.transaction_type not in self.TRANSACTION_TYPES:
            errors.append(f'Transaction type must be one of: {", ".join(self.TRANSACTION_TYPES)}')
        
        if self.category not in self.CATEGORIES.get(self.transaction_type, []):
            errors.append(f'Invalid category for {self.transaction_type}')
        
        if not self.description or len(self.description.strip()) == 0:
            errors.append('Description is required')
        
        return errors
