from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from bson.objectid import ObjectId
from models.category import Category

bp = Blueprint('settings', __name__, url_prefix='/settings')

@bp.route('/')
@login_required
def index():
    """Settings home page"""
    return render_template('settings/index.html')

@bp.route('/categories')
@login_required
def categories():
    """Manage categories"""
    from app import mongo
    
    user_id = str(current_user._id)
    
    # Get all user categories
    all_categories = list(mongo.db.categories.find({'user_id': user_id}).sort('transaction_type', 1))
    
    # If user has no categories, initialize them
    if not all_categories:
        Category.initialize_user_categories(mongo, user_id)
        all_categories = list(mongo.db.categories.find({'user_id': user_id}).sort('transaction_type', 1))
    
    # Group by transaction type
    grouped_categories = {
        'expense': [],
        'income': [],
        'borrow': []
    }
    
    for cat in all_categories:
        trans_type = cat.get('transaction_type')
        if trans_type in grouped_categories:
            grouped_categories[trans_type].append(cat)
    
    return render_template('settings/categories.html', categories=grouped_categories)

@bp.route('/categories/add', methods=['POST'])
@login_required
def add_category():
    """Add a new category"""
    from app import mongo, clear_cache
    
    user_id = str(current_user._id)
    
    category = Category(
        name=request.form.get('name'),
        transaction_type=request.form.get('transaction_type'),
        user_id=user_id,
        is_default=False
    )
    
    # Validate category
    errors = category.validate()
    if errors:
        for error in errors:
            flash(error, 'error')
        return redirect(url_for('settings.categories'))
    
    # Check if category already exists for this user
    existing = mongo.db.categories.find_one({
        'user_id': user_id,
        'name': category.name,
        'transaction_type': category.transaction_type
    })
    
    if existing:
        flash('Category already exists', 'error')
        return redirect(url_for('settings.categories'))
    
    # Save to MongoDB
    mongo.db.categories.insert_one(category.to_dict())
    
    # Clear cache
    clear_cache()
    
    flash(f'Category "{category.name}" added successfully!', 'success')
    return redirect(url_for('settings.categories'))

@bp.route('/categories/edit/<category_id>', methods=['POST'])
@login_required
def edit_category(category_id):
    """Edit a category"""
    from app import mongo, clear_cache
    
    user_id = str(current_user._id)
    
    # Find category for this user only
    category_data = mongo.db.categories.find_one({
        '_id': ObjectId(category_id),
        'user_id': user_id
    })
    
    if not category_data:
        flash('Category not found', 'error')
        return redirect(url_for('settings.categories'))
    
    new_name = request.form.get('name')
    
    # Validate new name
    if not new_name or len(new_name.strip()) == 0:
        flash('Category name is required', 'error')
        return redirect(url_for('settings.categories'))
    
    if len(new_name) > 50:
        flash('Category name must be less than 50 characters', 'error')
        return redirect(url_for('settings.categories'))
    
    # Check if new name already exists
    existing = mongo.db.categories.find_one({
        'user_id': user_id,
        'name': new_name,
        'transaction_type': category_data['transaction_type'],
        '_id': {'$ne': ObjectId(category_id)}
    })
    
    if existing:
        flash('Category name already exists', 'error')
        return redirect(url_for('settings.categories'))
    
    # Update category
    mongo.db.categories.update_one(
        {'_id': ObjectId(category_id)},
        {'$set': {
            'name': new_name,
            'updated_at': Category.from_dict(category_data).updated_at
        }}
    )
    
    # Update all transactions using this category
    mongo.db.transactions.update_many(
        {'user_id': user_id, 'category': category_data['name']},
        {'$set': {'category': new_name}}
    )
    
    # Clear cache
    clear_cache()
    
    flash(f'Category updated successfully!', 'success')
    return redirect(url_for('settings.categories'))

@bp.route('/categories/delete/<category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    """Delete a category"""
    from app import mongo, clear_cache
    
    user_id = str(current_user._id)
    
    # Find category for this user only
    category_data = mongo.db.categories.find_one({
        '_id': ObjectId(category_id),
        'user_id': user_id
    })
    
    if not category_data:
        flash('Category not found', 'error')
        return redirect(url_for('settings.categories'))
    
    # Check if category is in use
    transactions_count = mongo.db.transactions.count_documents({
        'user_id': user_id,
        'category': category_data['name']
    })
    
    if transactions_count > 0:
        flash(f'Cannot delete category "{category_data["name"]}" as it is used in {transactions_count} transaction(s). Please reassign those transactions first.', 'error')
        return redirect(url_for('settings.categories'))
    
    # Delete category
    mongo.db.categories.delete_one({'_id': ObjectId(category_id)})
    
    # Clear cache
    clear_cache()
    
    flash(f'Category "{category_data["name"]}" deleted successfully!', 'success')
    return redirect(url_for('settings.categories'))

@bp.route('/daily-limit', methods=['GET', 'POST'])
@login_required
def daily_limit():
    """Manage daily expense limit"""
    from app import mongo
    
    user_id = str(current_user._id)
    
    if request.method == 'POST':
        try:
            limit = float(request.form.get('daily_limit', 0))
            
            if limit < 0:
                flash('Daily limit must be a positive number', 'error')
                return redirect(url_for('settings.daily_limit'))
            
            # Update user's daily limit
            mongo.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'daily_expense_limit': limit}}
            )
            
            # Update current_user object
            current_user.daily_expense_limit = limit
            
            flash(f'Daily expense limit set to ৳{limit:.2f}', 'success')
            return redirect(url_for('settings.index'))
            
        except ValueError:
            flash('Please enter a valid number', 'error')
            return redirect(url_for('settings.daily_limit'))
    
    # Get current limit
    user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    current_limit = user_data.get('daily_expense_limit', 1000.0) if user_data else 1000.0
    
    return render_template('settings/daily_limit.html', current_limit=current_limit)

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change or set user password (works for both regular and OAuth users)"""
    from app import mongo
    from werkzeug.security import check_password_hash, generate_password_hash
    
    user_id = str(current_user._id)
    
    # Get user from database
    user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    
    if not user_data:
        flash('User not found', 'error')
        return redirect(url_for('settings.index'))
    
    # Check if user has a password set
    has_password = 'password' in user_data and user_data['password']
    is_oauth_user = 'google_id' in user_data and user_data['google_id']
    
    if request.method == 'POST':
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # For OAuth users setting password for the first time
        if is_oauth_user and not has_password:
            # No current password needed
            if not new_password or not confirm_password:
                flash('New password and confirmation are required', 'error')
                return redirect(url_for('settings.change_password'))
        else:
            # Regular users or OAuth users with existing password
            if not current_password or not new_password or not confirm_password:
                flash('All fields are required', 'error')
                return redirect(url_for('settings.change_password'))
            
            # Verify current password
            if not check_password_hash(user_data['password'], current_password):
                flash('Current password is incorrect', 'error')
                return redirect(url_for('settings.change_password'))
            
            # Check if new password is different from old password
            if current_password == new_password:
                flash('New password must be different from current password', 'error')
                return redirect(url_for('settings.change_password'))
        
        # Validate new password
        if len(new_password) < 6:
            flash('New password must be at least 6 characters long', 'error')
            return redirect(url_for('settings.change_password'))
        
        # Check if new password matches confirmation
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('settings.change_password'))
        
        # Update password
        hashed_password = generate_password_hash(new_password)
        mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'password': hashed_password}}
        )
        
        if is_oauth_user and not has_password:
            flash('Password set successfully! You can now login with email and password.', 'success')
        else:
            flash('Password changed successfully!', 'success')
        
        return redirect(url_for('settings.index'))
    
    return render_template('settings/change_password.html', 
                         has_password=has_password,
                         is_oauth_user=is_oauth_user)
