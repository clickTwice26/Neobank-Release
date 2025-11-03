from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/stats')
def stats():
    from app import mongo, rate_limit
    
    period = request.args.get('period', 'month')
    
    if period == 'week':
        start_date = datetime.now() - timedelta(days=7)
    elif period == 'year':
        start_date = datetime.now() - timedelta(days=365)
    else:
        start_date = datetime.now() - timedelta(days=30)
    
    transactions = list(mongo.db.transactions.find({
        'date': {'$gte': start_date}
    }))
    
    total_income = sum(t['amount'] for t in transactions if t['transaction_type'] == 'income')
    total_expense = sum(t['amount'] for t in transactions if t['transaction_type'] == 'expense')
    
    return jsonify({
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': total_income - total_expense,
        'transaction_count': len(transactions)
    })

@bp.route('/categories')
def categories():
    from app import mongo
    from models import Transaction
    
    transaction_type = request.args.get('type', 'expense')
    
    return jsonify({
        'categories': Transaction.CATEGORIES.get(transaction_type, [])
    })

@bp.route('/search-products')
@login_required
def search_products():
    from app import mongo
    
    query = request.args.get('q', '').strip()
    user_id = str(current_user._id)
    
    if not query:
        # Return all distinct product names if no query
        products = mongo.db.transactions.distinct('product_name', {
            'user_id': user_id,
            'product_name': {'$exists': True, '$ne': None, '$ne': ''}
        })
    else:
        # Search for product names containing the query (case-insensitive)
        products = mongo.db.transactions.distinct('product_name', {
            'user_id': user_id,
            'product_name': {
                '$exists': True, 
                '$ne': None, 
                '$ne': '',
                '$regex': query,
                '$options': 'i'  # case-insensitive
            }
        })
    
    # Sort and limit results
    products = sorted(products)[:10]
    
    return jsonify({
        'products': products
    })

@bp.route('/analytics/trends')
@login_required
def analytics_trends():
    from app import mongo
    from collections import defaultdict
    
    user_id = str(current_user._id)
    period = request.args.get('period', '6months')
    
    # Calculate start date based on period
    if period == '1month':
        start_date = datetime.now() - timedelta(days=30)
        group_by = 'day'
    elif period == '3months':
        start_date = datetime.now() - timedelta(days=90)
        group_by = 'week'
    elif period == '1year':
        start_date = datetime.now() - timedelta(days=365)
        group_by = 'month'
    else:  # 6months
        start_date = datetime.now() - timedelta(days=180)
        group_by = 'month'
    
    transactions = list(mongo.db.transactions.find({
        'user_id': user_id,
        'date': {'$gte': start_date}
    }).sort('date', 1))
    
    # Group transactions by time period
    income_data = defaultdict(float)
    expense_data = defaultdict(float)
    
    for t in transactions:
        date = t['date']
        if group_by == 'day':
            key = date.strftime('%Y-%m-%d')
        elif group_by == 'week':
            # Get week number
            key = date.strftime('%Y-W%U')
        else:  # month
            key = date.strftime('%Y-%m')
        
        if t.get('transaction_type') == 'income':
            income_data[key] += t['amount']
        elif t.get('transaction_type') == 'expense':
            expense_data[key] += t['amount']
    
    # Create sorted labels and data arrays
    all_keys = sorted(set(list(income_data.keys()) + list(expense_data.keys())))
    
    labels = []
    income_values = []
    expense_values = []
    
    # If no data, create empty dataset with at least current period
    if not all_keys:
        if group_by == 'day':
            labels = [(datetime.now() - timedelta(days=i)).strftime('%b %d') for i in range(7, -1, -1)]
        elif group_by == 'month':
            labels = [(datetime.now() - timedelta(days=30*i)).strftime('%b %Y') for i in range(5, -1, -1)]
        else:
            labels = [(datetime.now() - timedelta(days=7*i)).strftime('Week %U') for i in range(4, -1, -1)]
        income_values = [0] * len(labels)
        expense_values = [0] * len(labels)
    else:
        for key in all_keys:
            if group_by == 'day':
                labels.append(datetime.strptime(key, '%Y-%m-%d').strftime('%b %d'))
            elif group_by == 'week':
                labels.append(f"Week {key.split('-W')[1]}")
            else:
                labels.append(datetime.strptime(key, '%Y-%m').strftime('%b %Y'))
            
            income_values.append(income_data[key])
            expense_values.append(expense_data[key])
    
    return jsonify({
        'labels': labels,
        'income': income_values,
        'expense': expense_values
    })

@bp.route('/analytics/categories')
@login_required
def analytics_categories():
    from app import mongo
    from collections import defaultdict
    
    user_id = str(current_user._id)
    period = request.args.get('period', '6months')
    transaction_type = request.args.get('type', 'expense')
    
    if period == '1month':
        start_date = datetime.now() - timedelta(days=30)
    elif period == '3months':
        start_date = datetime.now() - timedelta(days=90)
    elif period == '1year':
        start_date = datetime.now() - timedelta(days=365)
    else:
        start_date = datetime.now() - timedelta(days=180)
    
    transactions = list(mongo.db.transactions.find({
        'user_id': user_id,
        'transaction_type': transaction_type,
        'date': {'$gte': start_date}
    }))
    
    # Group by category
    category_totals = defaultdict(float)
    for t in transactions:
        category = t.get('category', 'Other')
        category_totals[category] += t['amount']
    
    # Sort by amount
    sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    
    return jsonify({
        'labels': [cat[0] for cat in sorted_categories],
        'data': [cat[1] for cat in sorted_categories]
    })

@bp.route('/analytics/predictions')
@login_required
def analytics_predictions():
    from app import mongo
    
    user_id = str(current_user._id)
    
    # Get last 3 months of data
    start_date = datetime.now() - timedelta(days=90)
    transactions = list(mongo.db.transactions.find({
        'user_id': user_id,
        'date': {'$gte': start_date}
    }).sort('date', 1))
    
    if len(transactions) < 10:
        return jsonify({
            'message': 'Not enough data for predictions',
            'predictions': {}
        })
    
    # Calculate monthly averages
    total_expense = sum(t['amount'] for t in transactions if t.get('transaction_type') == 'expense')
    total_income = sum(t['amount'] for t in transactions if t.get('transaction_type') == 'income')
    
    months_of_data = 3
    avg_monthly_expense = total_expense / months_of_data
    avg_monthly_income = total_income / months_of_data
    
    # Simple linear trend (last month vs first month)
    month1_expense = sum(t['amount'] for t in transactions[:len(transactions)//3] if t.get('transaction_type') == 'expense')
    month3_expense = sum(t['amount'] for t in transactions[2*len(transactions)//3:] if t.get('transaction_type') == 'expense')
    
    trend_multiplier = month3_expense / month1_expense if month1_expense > 0 else 1
    
    # Predict next month
    next_month_expense = avg_monthly_expense * trend_multiplier
    next_month_income = avg_monthly_income  # Assuming stable income
    next_month_savings = next_month_income - next_month_expense
    
    # Spending recommendations
    recommendations = []
    if next_month_savings < 0:
        recommendations.append({
            'type': 'critical',
            'message': f'You may overspend by ৳{abs(next_month_savings):.2f} next month. Consider reducing expenses.'
        })
    elif next_month_savings < avg_monthly_income * 0.2:
        recommendations.append({
            'type': 'warning',
            'message': 'Your savings rate is below 20%. Try to increase savings.'
        })
    else:
        recommendations.append({
            'type': 'success',
            'message': f'You\'re on track to save ৳{next_month_savings:.2f} next month!'
        })
    
    # Category-wise predictions
    from collections import defaultdict
    category_expenses = defaultdict(float)
    for t in transactions:
        if t.get('transaction_type') == 'expense':
            category_expenses[t.get('category', 'Other')] += t['amount']
    
    predicted_categories = {cat: (amt / months_of_data) for cat, amt in category_expenses.items()}
    
    return jsonify({
        'next_month': {
            'expense': round(next_month_expense, 2),
            'income': round(next_month_income, 2),
            'savings': round(next_month_savings, 2)
        },
        'trend': 'increasing' if trend_multiplier > 1.1 else 'decreasing' if trend_multiplier < 0.9 else 'stable',
        'recommendations': recommendations,
        'category_predictions': predicted_categories
    })

@bp.route('/analytics/spending-pattern')
@login_required
def analytics_spending_pattern():
    from app import mongo
    from collections import defaultdict
    
    user_id = str(current_user._id)
    
    # Get last 90 days
    start_date = datetime.now() - timedelta(days=90)
    transactions = list(mongo.db.transactions.find({
        'user_id': user_id,
        'transaction_type': 'expense',
        'date': {'$gte': start_date}
    }))
    
    # Analyze spending by day of week
    day_totals = defaultdict(float)
    day_counts = defaultdict(int)
    
    for t in transactions:
        day_name = t['date'].strftime('%A')
        day_totals[day_name] += t['amount']
        day_counts[day_name] += 1
    
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_averages = {day: (day_totals[day] / day_counts[day] if day_counts[day] > 0 else 0) for day in days_order}
    
    return jsonify({
        'day_of_week': {
            'labels': days_order,
            'data': [day_averages[day] for day in days_order]
        }
    })

@bp.route('/analytics/monthly-breakdown')
@login_required
def analytics_monthly_breakdown():
    from app import mongo
    from collections import defaultdict
    import calendar
    
    user_id = str(current_user._id)
    period = request.args.get('period', '6months')
    
    # Calculate start date based on period
    if period == '1month':
        months_back = 1
    elif period == '3months':
        months_back = 3
    elif period == '1year':
        months_back = 12
    else:  # 6months
        months_back = 6
    
    # Get transactions for the period
    start_date = datetime.now() - timedelta(days=30 * months_back)
    transactions = list(mongo.db.transactions.find({
        'user_id': user_id,
        'date': {'$gte': start_date}
    }).sort('date', -1))
    
    # Group by month
    monthly_data = defaultdict(lambda: {'income': 0, 'expense': 0, 'borrow': 0})
    
    for t in transactions:
        month_key = t['date'].strftime('%Y-%m')
        trans_type = t.get('transaction_type', 'expense')
        amount = t.get('amount', 0)
        
        if trans_type in ['income', 'expense', 'borrow']:
            monthly_data[month_key][trans_type] += amount
    
    # Sort months in descending order (most recent first)
    sorted_months = sorted(monthly_data.keys(), reverse=True)
    
    # Build response
    breakdown = []
    for month_key in sorted_months:
        data = monthly_data[month_key]
        
        # Parse month for display
        month_date = datetime.strptime(month_key, '%Y-%m')
        month_name = month_date.strftime('%B %Y')
        
        breakdown.append({
            'month': month_name,
            'month_key': month_key,
            'income': round(data['income'], 2),
            'expense': round(data['expense'], 2),
            'borrow': round(data['borrow'], 2),
            'net': round(data['income'] - data['expense'], 2),
            'savings_rate': round((data['income'] - data['expense']) / data['income'] * 100, 1) if data['income'] > 0 else 0
        })
    
    # Calculate totals
    totals = {
        'income': sum(item['income'] for item in breakdown),
        'expense': sum(item['expense'] for item in breakdown),
        'borrow': sum(item['borrow'] for item in breakdown),
        'net': sum(item['net'] for item in breakdown)
    }
    
    return jsonify({
        'breakdown': breakdown,
        'totals': totals
    })

@bp.route('/daily-spending-check')
@login_required
def daily_spending_check():
    from app import mongo
    
    user_id = str(current_user._id)
    
    # Get user's daily limit
    user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    daily_limit = user_data.get('daily_expense_limit', 1000.0) if user_data else 1000.0
    
    # Get today's expenses
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
    
    today_expenses = list(mongo.db.transactions.find({
        'user_id': user_id,
        'transaction_type': 'expense',
        'date': {'$gte': today_start, '$lte': today_end}
    }))
    
    total_spent = sum(t['amount'] for t in today_expenses)
    remaining = daily_limit - total_spent
    percentage = (total_spent / daily_limit * 100) if daily_limit > 0 else 0
    
    # Determine status
    if percentage >= 100:
        status = 'exceeded'
        message = f'You have exceeded your daily limit by ৳{abs(remaining):.2f}!'
        level = 'error'
    elif percentage >= 90:
        status = 'warning'
        message = f'Warning! You have ৳{remaining:.2f} left (90% spent)'
        level = 'warning'
    elif percentage >= 70:
        status = 'caution'
        message = f'You have ৳{remaining:.2f} left today (70% spent)'
        level = 'info'
    else:
        status = 'ok'
        message = f'You have ৳{remaining:.2f} left today'
        level = 'success'
    
    return jsonify({
        'daily_limit': daily_limit,
        'total_spent': total_spent,
        'remaining': remaining,
        'percentage': round(percentage, 1),
        'status': status,
        'message': message,
        'level': level,
        'transaction_count': len(today_expenses)
    })
