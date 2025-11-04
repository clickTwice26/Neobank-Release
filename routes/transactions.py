from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from bson.objectid import ObjectId
from datetime import datetime
from models import Transaction
from models.category import Category
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

bp = Blueprint('transactions', __name__, url_prefix='/transactions')

@bp.route('/')
@login_required
def list_transactions():
    from app import mongo
    
    user_id = str(current_user._id)
    
    # Get filter parameters
    transaction_type = request.args.get('type', 'all')
    category = request.args.get('category', 'all')
    
    # Build query for this user only
    query = {'user_id': user_id}
    if transaction_type != 'all':
        query['transaction_type'] = transaction_type
    if category != 'all':
        query['category'] = category
    
    # Fetch transactions
    transactions_cursor = mongo.db.transactions.find(query).sort('date', -1)
    transactions = [t for t in transactions_cursor]
    
    # Get user's custom categories
    categories = Category.get_user_categories(mongo, user_id)
    
    return render_template('transactions/list.html',
                         transactions=transactions,
                         transaction_type=transaction_type,
                         category=category,
                         categories=categories)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    from app import mongo, clear_cache
    
    user_id = str(current_user._id)
    
    if request.method == 'POST':
        # Get borrow-specific fields if transaction type is borrow
        borrower_name = request.form.get('borrower_name') if request.form.get('type') == 'borrow' else None
        repayment_date = None
        if request.form.get('type') == 'borrow' and request.form.get('repayment_date'):
            repayment_date = datetime.fromisoformat(request.form.get('repayment_date'))
        
        transaction = Transaction(
            amount=request.form.get('amount'),
            category=request.form.get('category'),
            description=request.form.get('description'),
            transaction_type=request.form.get('type'),
            date=datetime.fromisoformat(request.form.get('date')),
            product_name=request.form.get('product_name'),
            borrower_name=borrower_name,
            repayment_date=repayment_date
        )
        
        # Get user's categories for validation
        categories = Category.get_user_categories(mongo, user_id)
        
        # Validate transaction
        errors = transaction.validate(categories)
        if errors:
            for error in errors:
                flash(error, 'error')
            # Get distinct product names for autocomplete
            product_names = mongo.db.transactions.distinct('product_name', {
                'user_id': user_id,
                'product_name': {'$exists': True, '$ne': None, '$ne': ''}
            })
            return render_template('transactions/form.html',
                                 transaction=None,
                                 categories=categories,
                                 product_names=product_names,
                                 today=datetime.now().strftime('%Y-%m-%d'))
        
        # Add user_id to transaction
        transaction_data = transaction.to_dict()
        transaction_data['user_id'] = user_id
        
        # Save to MongoDB
        mongo.db.transactions.insert_one(transaction_data)
        
        # Clear cache
        clear_cache()
        
        flash(f'{transaction.transaction_type.capitalize()} added successfully!', 'success')
        return redirect(url_for('dashboard.index'))
    
    # Get user's categories for the form
    categories = Category.get_user_categories(mongo, user_id)
    
    # Get distinct product names for autocomplete
    product_names = mongo.db.transactions.distinct('product_name', {
        'user_id': user_id,
        'product_name': {'$exists': True, '$ne': None, '$ne': ''}
    })
    
    return render_template('transactions/form.html',
                         transaction=None,
                         categories=categories,
                         product_names=product_names,
                         today=datetime.now().strftime('%Y-%m-%d'))

@bp.route('/edit/<transaction_id>', methods=['GET', 'POST'])
@login_required
def edit(transaction_id):
    from app import mongo, clear_cache
    
    user_id = str(current_user._id)
    
    # Find transaction for this user only
    transaction_data = mongo.db.transactions.find_one({
        '_id': ObjectId(transaction_id),
        'user_id': user_id
    })
    
    if not transaction_data:
        flash('Transaction not found', 'error')
        return redirect(url_for('transactions.list_transactions'))
    
    if request.method == 'POST':
        # Get borrow-specific fields if transaction type is borrow
        borrower_name = request.form.get('borrower_name') if request.form.get('transaction_type') == 'borrow' else None
        repayment_date = None
        if request.form.get('transaction_type') == 'borrow' and request.form.get('repayment_date'):
            repayment_date = datetime.fromisoformat(request.form.get('repayment_date'))
        
        updated_transaction = Transaction(
            amount=request.form.get('amount'),
            category=request.form.get('category'),
            description=request.form.get('description'),
            transaction_type=request.form.get('transaction_type'),
            date=datetime.fromisoformat(request.form.get('date')),
            _id=ObjectId(transaction_id),
            product_name=request.form.get('product_name'),
            borrower_name=borrower_name,
            repayment_date=repayment_date
        )
        
        # Get user's categories for validation
        categories = Category.get_user_categories(mongo, user_id)
        
        # Validate transaction
        errors = updated_transaction.validate(categories)
        if errors:
            for error in errors:
                flash(error, 'error')
            categories = Category.get_user_categories(mongo, user_id)
            # Get distinct product names for autocomplete
            product_names = mongo.db.transactions.distinct('product_name', {
                'user_id': user_id,
                'product_name': {'$exists': True, '$ne': None, '$ne': ''}
            })
            return render_template('transactions/form.html',
                                 transaction=transaction_data,
                                 categories=categories,
                                 product_names=product_names,
                                 today=datetime.now().strftime('%Y-%m-%d'))
        
        # Update in MongoDB
        update_data = updated_transaction.to_dict()
        update_data['updated_at'] = datetime.now()
        mongo.db.transactions.update_one(
            {'_id': ObjectId(transaction_id)},
            {'$set': update_data}
        )
        
        # Clear cache
        clear_cache()
        
        flash('Transaction updated successfully!', 'success')
        return redirect(url_for('transactions.list_transactions'))
    
    # Get user's categories for the form
    categories = Category.get_user_categories(mongo, user_id)
    
    # Get distinct product names for autocomplete
    product_names = mongo.db.transactions.distinct('product_name', {
        'user_id': user_id,
        'product_name': {'$exists': True, '$ne': None, '$ne': ''}
    })
    
    return render_template('transactions/form.html',
                         transaction=transaction_data,
                         categories=categories,
                         product_names=product_names,
                         today=datetime.now().strftime('%Y-%m-%d'))

@bp.route('/delete/<transaction_id>', methods=['POST'])
@login_required
def delete(transaction_id):
    from app import mongo, clear_cache
    
    user_id = str(current_user._id)
    
    # Delete transaction only if it belongs to this user
    result = mongo.db.transactions.delete_one({
        '_id': ObjectId(transaction_id),
        'user_id': user_id
    })
    
    if result.deleted_count > 0:
        clear_cache()
        flash('Transaction deleted successfully!', 'success')
    else:
        flash('Transaction not found', 'error')
    
    return redirect(url_for('transactions.list_transactions'))
