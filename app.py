from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_pymongo import PyMongo
from flask_login import LoginManager, current_user
from authlib.integrations.flask_client import OAuth
from redis import Redis
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from functools import wraps
import hashlib
from models import User

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MONGO_URI'] = os.getenv('DB_URL')

# Initialize MongoDB
mongo = PyMongo(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Initialize OAuth
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    from bson.objectid import ObjectId
    user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return User.from_dict(user_data)
    return None

# Initialize Redis
try:
    redis_client = Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=0,
        decode_responses=True
    )
    redis_client.ping()
    REDIS_AVAILABLE = True
except Exception as e:
    print(f"Redis connection failed: {e}")
    REDIS_AVAILABLE = False
    redis_client = None

# Rate limiting decorator
def rate_limit(max_requests=10, window=60):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not REDIS_AVAILABLE:
                return f(*args, **kwargs)
            
            # Create a unique key based on IP address
            ip = request.remote_addr
            key = f"rate_limit:{f.__name__}:{ip}"
            
            # Get current request count
            current = redis_client.get(key)
            
            if current is None:
                redis_client.setex(key, window, 1)
            elif int(current) >= max_requests:
                return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
            else:
                redis_client.incr(key)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Cache decorator
def cache_result(timeout=300):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not REDIS_AVAILABLE:
                return f(*args, **kwargs)
            
            # Create cache key from function name and arguments
            cache_key = f"cache:{f.__name__}:{hashlib.md5(str(args).encode() + str(kwargs).encode()).hexdigest()}"
            
            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return cached
            
            # Call function and cache result
            result = f(*args, **kwargs)
            if isinstance(result, (str, int, float)):
                redis_client.setex(cache_key, timeout, result)
            
            return result
        return decorated_function
    return decorator

def clear_cache(pattern="cache:*"):
    """Clear cache by pattern"""
    if REDIS_AVAILABLE:
        for key in redis_client.scan_iter(pattern):
            redis_client.delete(key)

from routes import transactions, dashboard, api, auth, settings, analytics

app.register_blueprint(transactions.bp)
app.register_blueprint(dashboard.bp)
app.register_blueprint(api.bp)
app.register_blueprint(auth.bp)
app.register_blueprint(settings.bp)
app.register_blueprint(analytics.bp)

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))

@app.template_filter('currency')
def currency_filter(value):
    """Format number as currency"""
    try:
        return f"৳{float(value):,.2f}"
    except (ValueError, TypeError):
        return "৳0.00"

@app.template_filter('date_format')
def date_format_filter(value, format='%b %d, %Y'):
    """Format datetime object"""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except:
            return value
    return value.strftime(format) if value else ''

@app.template_filter('string')
def string_filter(value):
    """Convert ObjectId or any value to string"""
    return str(value)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=6767)
