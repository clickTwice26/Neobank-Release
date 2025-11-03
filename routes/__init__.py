from .dashboard import bp as dashboard_bp
from .transactions import bp as transactions_bp
from .api import bp as api_bp
from .auth import bp as auth_bp

__all__ = ['dashboard_bp', 'transactions_bp', 'api_bp', 'auth_bp']
