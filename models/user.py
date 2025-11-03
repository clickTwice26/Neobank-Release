from datetime import datetime
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import re

class User(UserMixin):
    """User model for authentication"""
    
    def __init__(self, username, email, password=None, password_hash=None, _id=None, google_id=None, profile_picture=None, daily_expense_limit=None):
        self._id = _id or ObjectId()
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.google_id = google_id
        self.profile_picture = profile_picture
        self.daily_expense_limit = daily_expense_limit or 1000.0  # Default 1000 Taka
        if password and not password_hash:
            self.password_hash = generate_password_hash(password)
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def get_id(self):
        """Required for Flask-Login"""
        return str(self._id)
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            '_id': self._id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'google_id': self.google_id,
            'profile_picture': self.profile_picture,
            'daily_expense_limit': self.daily_expense_limit,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @staticmethod
    def from_dict(data):
        """Create user from dictionary"""
        user = User(
            username=data.get('username'),
            email=data.get('email'),
            password_hash=data.get('password_hash'),
            _id=data.get('_id'),
            google_id=data.get('google_id'),
            profile_picture=data.get('profile_picture'),
            daily_expense_limit=data.get('daily_expense_limit', 1000.0)
        )
        user.created_at = data.get('created_at', datetime.now())
        user.updated_at = data.get('updated_at', datetime.now())
        return user
    
    def check_password(self, password):
        """Check if password matches hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def validate(self):
        """Validate user data"""
        errors = []
        
        # Username validation
        if not self.username or len(self.username.strip()) == 0:
            errors.append('Username is required')
        elif len(self.username) < 3:
            errors.append('Username must be at least 3 characters')
        elif len(self.username) > 30:
            errors.append('Username must be less than 30 characters')
        elif not re.match(r'^[a-zA-Z0-9_]+$', self.username):
            errors.append('Username can only contain letters, numbers, and underscores')
        
        # Email validation
        if not self.email or len(self.email.strip()) == 0:
            errors.append('Email is required')
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', self.email):
            errors.append('Invalid email format')
        
        # Password validation (only for non-OAuth users)
        if not self.password_hash and not self.google_id:
            errors.append('Password is required')
        
        return errors
    
    @staticmethod
    def validate_password(password):
        """Validate password strength"""
        errors = []
        
        if not password or len(password) == 0:
            errors.append('Password is required')
        elif len(password) < 6:
            errors.append('Password must be at least 6 characters')
        elif len(password) > 100:
            errors.append('Password must be less than 100 characters')
        
        return errors
