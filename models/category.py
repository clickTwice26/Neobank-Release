from datetime import datetime
from bson.objectid import ObjectId

class Category:
    """Category model for custom user categories"""
    
    # Default categories that all users start with
    DEFAULT_CATEGORIES = {
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
    
    def __init__(self, name, transaction_type, user_id, _id=None, is_default=False):
        self._id = _id or ObjectId()
        self.name = name
        self.transaction_type = transaction_type  # 'expense', 'income', or 'borrow'
        self.user_id = user_id
        self.is_default = is_default  # Default categories can't be deleted
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self):
        """Convert category to dictionary"""
        return {
            '_id': self._id,
            'name': self.name,
            'transaction_type': self.transaction_type,
            'user_id': self.user_id,
            'is_default': self.is_default,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @staticmethod
    def from_dict(data):
        """Create category from dictionary"""
        return Category(
            name=data.get('name'),
            transaction_type=data.get('transaction_type'),
            user_id=data.get('user_id'),
            _id=data.get('_id'),
            is_default=data.get('is_default', False)
        )
    
    def validate(self):
        """Validate category data"""
        errors = []
        
        if not self.name or len(self.name.strip()) == 0:
            errors.append('Category name is required')
        
        if len(self.name) > 50:
            errors.append('Category name must be less than 50 characters')
        
        if self.transaction_type not in ['expense', 'income', 'borrow']:
            errors.append('Invalid transaction type')
        
        return errors
    
    @staticmethod
    def initialize_user_categories(mongo, user_id):
        """Initialize default categories for a new user"""
        categories = []
        
        for trans_type, cat_names in Category.DEFAULT_CATEGORIES.items():
            for cat_name in cat_names:
                category = Category(
                    name=cat_name,
                    transaction_type=trans_type,
                    user_id=str(user_id),
                    is_default=True
                )
                categories.append(category.to_dict())
        
        if categories:
            mongo.db.categories.insert_many(categories)
        
        return categories
    
    @staticmethod
    def get_user_categories(mongo, user_id):
        """Get all categories for a user, grouped by transaction type"""
        categories = list(mongo.db.categories.find({'user_id': str(user_id)}))
        
        # If user has no categories, initialize them
        if not categories:
            Category.initialize_user_categories(mongo, user_id)
            categories = list(mongo.db.categories.find({'user_id': str(user_id)}))
        
        # Group by transaction type
        grouped = {
            'expense': [],
            'income': [],
            'borrow': []
        }
        
        for cat in categories:
            trans_type = cat.get('transaction_type')
            if trans_type in grouped:
                grouped[trans_type].append(cat['name'])
        
        return grouped
