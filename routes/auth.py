from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, current_user, login_required
from bson.objectid import ObjectId
from models.user import User
from models.category import Category
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    from app import mongo, rate_limit
    
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register.html')
        
        # Validate password strength
        password_errors = User.validate_password(password)
        if password_errors:
            for error in password_errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        # Create user object
        user = User(username=username, email=email, password=password)
        
        # Validate user data
        errors = user.validate()
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        # Check if username already exists
        existing_user = mongo.db.users.find_one({'username': username})
        if existing_user:
            flash('Username already taken', 'error')
            return render_template('auth/register.html')
        
        # Check if email already exists
        existing_email = mongo.db.users.find_one({'email': email})
        if existing_email:
            flash('Email already registered', 'error')
            return render_template('auth/register.html')
        
        # Save user to database
        result = mongo.db.users.insert_one(user.to_dict())
        user._id = result.inserted_id
        
        # Initialize default categories for new user
        Category.initialize_user_categories(mongo, user._id)
        
        # Log user in automatically
        login_user(user)
        
        flash('Account created successfully! Welcome to NeoBank!', 'success')
        return redirect(url_for('dashboard.index'))
    
    return render_template('auth/register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    from app import mongo, rate_limit
    
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Try to find user by username first, then by email
        user_data = mongo.db.users.find_one({'username': username})
        
        # If not found by username, try email
        if not user_data:
            user_data = mongo.db.users.find_one({'email': username})
        
        if not user_data:
            flash('Invalid username/email or password', 'error')
            return render_template('auth/login.html')
        
        # Check if user has a password set
        if 'password' not in user_data or not user_data['password']:
            flash('This account uses OAuth login. Please use "Sign in with Google" or set a password in settings.', 'error')
            return render_template('auth/login.html')
        
        # Create user object and check password
        user = User.from_dict(user_data)
        if not user.check_password(password):
            flash('Invalid username/email or password', 'error')
            return render_template('auth/login.html')
        
        # Log user in
        login_user(user, remember=True)
        
        flash(f'Welcome back, {user.username}!', 'success')
        
        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('dashboard.index'))
    
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('auth.login'))

@bp.route('/google')
def google_login():
    from app import google
    
    redirect_uri = url_for('auth.google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@bp.route('/google/callback')
def google_callback():
    from app import google, mongo
    
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        
        if not user_info:
            flash('Failed to get user information from Google', 'error')
            return redirect(url_for('auth.login'))
        
        google_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name', '')
        picture = user_info.get('picture', '')
        
        # Check if user already exists with this Google ID
        user_data = mongo.db.users.find_one({'google_id': google_id})
        
        if user_data:
            # User exists, log them in
            user = User.from_dict(user_data)
            login_user(user, remember=True)
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard.index'))
        
        # Check if email already exists (user might have registered manually)
        existing_email = mongo.db.users.find_one({'email': email})
        if existing_email:
            # Link Google account to existing user
            mongo.db.users.update_one(
                {'email': email},
                {'$set': {
                    'google_id': google_id,
                    'profile_picture': picture
                }}
            )
            user = User.from_dict(mongo.db.users.find_one({'email': email}))
            login_user(user, remember=True)
            flash('Google account linked successfully!', 'success')
            return redirect(url_for('dashboard.index'))
        
        # Create new user
        # Generate username from name or email
        username = name.replace(' ', '_').lower() if name else email.split('@')[0]
        
        # Ensure username is unique
        base_username = username
        counter = 1
        while mongo.db.users.find_one({'username': username}):
            username = f"{base_username}{counter}"
            counter += 1
        
        new_user = User(
            username=username,
            email=email,
            google_id=google_id,
            profile_picture=picture
        )
        
        result = mongo.db.users.insert_one(new_user.to_dict())
        new_user._id = result.inserted_id
        
        # Initialize default categories for new user
        Category.initialize_user_categories(mongo, new_user._id)
        
        login_user(new_user, remember=True)
        flash(f'Account created successfully! Welcome to NeoBank, {username}!', 'success')
        return redirect(url_for('dashboard.index'))
        
    except Exception as e:
        print(f"Google OAuth error: {e}")
        flash('Failed to authenticate with Google. Please try again.', 'error')
        return redirect(url_for('auth.login'))

