from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from models import Transaction
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

bp = Blueprint('dashboard', __name__)

@bp.route('/dashboard')
@login_required
def index():
    from app import mongo, redis_client, REDIS_AVAILABLE, clear_cache
    
    user_id = str(current_user._id)
    
    # Get date range for filtering
    period = request.args.get('period', 'month')
    
    if period == 'week':
        start_date = datetime.now() - timedelta(days=7)
    elif period == 'year':
        start_date = datetime.now() - timedelta(days=365)
    else:  # month
        start_date = datetime.now() - timedelta(days=30)
    
    # Fetch transactions from MongoDB for this user only
    transactions = list(mongo.db.transactions.find({
        'user_id': user_id,
        'date': {'$gte': start_date}
    }).sort('date', -1))
    
    # Calculate totals
    total_income = sum(t['amount'] for t in transactions if t['transaction_type'] == 'income')
    total_expense = sum(t['amount'] for t in transactions if t['transaction_type'] == 'expense')
    balance = total_income - total_expense
    
    # Get recent transactions (last 5)
    recent_transactions = transactions[:5]
    
    # Calculate category breakdown for expenses
    expense_by_category = {}
    for t in transactions:
        if t['transaction_type'] == 'expense':
            category = t['category']
            expense_by_category[category] = expense_by_category.get(category, 0) + t['amount']
    
    return render_template('dashboard.html',
                         total_income=total_income,
                         total_expense=total_expense,
                         balance=balance,
                         recent_transactions=recent_transactions,
                         expense_by_category=expense_by_category,
                         period=period)
