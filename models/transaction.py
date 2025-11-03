from datetime import datetime
from bson.objectid import ObjectId

class Transaction:
    """Transaction model for expenses, income, and borrows"""
    
    TRANSACTION_TYPES = ['expense', 'income', 'borrow']
    
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
        ],
        'borrow': [
            'Personal Loan',
            'Business Loan',
            'Emergency',
            'Other'
        ]
    }
    
    def __init__(self, amount, category, description, transaction_type, date=None, _id=None, 
                 borrower_name=None, repayment_date=None, product_name=None):
        self._id = _id or ObjectId()
        self.amount = float(amount)
        self.category = category
        self.description = description
        self.transaction_type = transaction_type
        self.date = date or datetime.now()
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        # Product name
        self.product_name = product_name
        # Borrow-specific fields
        self.borrower_name = borrower_name
        self.repayment_date = repayment_date
    
    def to_dict(self):
        """Convert transaction to dictionary"""
        data = {
            '_id': self._id,
            'amount': self.amount,
            'category': self.category,
            'description': self.description,
            'transaction_type': self.transaction_type,
            'date': self.date,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        # Add product name if present
        if self.product_name:
            data['product_name'] = self.product_name
        # Add borrow-specific fields if present
        if self.transaction_type == 'borrow':
            data['borrower_name'] = self.borrower_name
            data['repayment_date'] = self.repayment_date
        return data
    
    @staticmethod
    def from_dict(data):
        """Create transaction from dictionary"""
        return Transaction(
            amount=data.get('amount'),
            category=data.get('category'),
            description=data.get('description'),
            transaction_type=data.get('transaction_type'),
            date=data.get('date'),
            _id=data.get('_id'),
            product_name=data.get('product_name'),
            borrower_name=data.get('borrower_name'),
            repayment_date=data.get('repayment_date')
        )
    
    def validate(self, user_categories=None):
        """Validate transaction data"""
        errors = []
        
        if not self.amount or self.amount <= 0:
            errors.append('Amount must be greater than 0')
        
        if self.transaction_type not in self.TRANSACTION_TYPES:
            errors.append(f'Transaction type must be one of: {", ".join(self.TRANSACTION_TYPES)}')
        
        # Validate category against user's categories if provided
        if user_categories:
            valid_categories = user_categories.get(self.transaction_type, [])
            if self.category not in valid_categories:
                errors.append(f'Invalid category for {self.transaction_type}')
        else:
            # Fallback to default categories
            if self.category not in self.CATEGORIES.get(self.transaction_type, []):
                errors.append(f'Invalid category for {self.transaction_type}')
        
        if not self.description or len(self.description.strip()) == 0:
            errors.append('Description is required')
        
        # Validate borrow-specific fields
        if self.transaction_type == 'borrow':
            if not self.borrower_name or len(self.borrower_name.strip()) == 0:
                errors.append('Borrower name is required for borrow transactions')
            
            if not self.repayment_date:
                errors.append('Repayment date is required for borrow transactions')
        
        return errors
