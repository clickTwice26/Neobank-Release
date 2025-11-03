from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from collections import defaultdict
import calendar

bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@bp.route('/')
@login_required
def index():
    from app import mongo
    
    user_id = str(current_user._id)
    
    # Get date range (default: last 6 months)
    period = request.args.get('period', '6months')
    
    if period == '1month':
        start_date = datetime.now() - timedelta(days=30)
        period_label = 'Last 30 Days'
    elif period == '3months':
        start_date = datetime.now() - timedelta(days=90)
        period_label = 'Last 3 Months'
    elif period == '1year':
        start_date = datetime.now() - timedelta(days=365)
        period_label = 'Last Year'
    else:  # 6months default
        start_date = datetime.now() - timedelta(days=180)
        period_label = 'Last 6 Months'
    
    # Get all transactions for the user in the period
    transactions = list(mongo.db.transactions.find({
        'user_id': user_id,
        'date': {'$gte': start_date}
    }).sort('date', 1))
    
    # Calculate basic stats
    total_income = sum(t['amount'] for t in transactions if t.get('transaction_type') == 'income')
    total_expense = sum(t['amount'] for t in transactions if t.get('transaction_type') == 'expense')
    total_borrow = sum(t['amount'] for t in transactions if t.get('transaction_type') == 'borrow')
    balance = total_income - total_expense
    transaction_count = len(transactions)
    
    # Average per day
    days_in_period = (datetime.now() - start_date).days or 1
    avg_daily_expense = total_expense / days_in_period
    avg_daily_income = total_income / days_in_period
    
    # Get top spending categories
    category_totals = defaultdict(float)
    for t in transactions:
        if t.get('transaction_type') == 'expense':
            category_totals[t.get('category', 'Other')] += t['amount']
    
    top_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Get recent insights
    insights = generate_insights(transactions, total_income, total_expense, avg_daily_expense)
    
    return render_template('analytics/index.html',
                         period=period,
                         period_label=period_label,
                         total_income=total_income,
                         total_expense=total_expense,
                         total_borrow=total_borrow,
                         balance=balance,
                         transaction_count=transaction_count,
                         avg_daily_expense=avg_daily_expense,
                         avg_daily_income=avg_daily_income,
                         top_categories=top_categories,
                         insights=insights)

def generate_insights(transactions, total_income, total_expense, avg_daily_expense):
    """Generate intelligent insights based on transaction data"""
    insights = []
    
    # Spending vs Income insight
    if total_income > 0:
        spending_ratio = (total_expense / total_income) * 100
        if spending_ratio > 90:
            insights.append({
                'type': 'warning',
                'icon': 'bx-error-circle',
                'title': 'High Spending Alert',
                'message': f'You\'re spending {spending_ratio:.0f}% of your income. Consider reducing expenses.'
            })
        elif spending_ratio < 50:
            insights.append({
                'type': 'success',
                'icon': 'bx-check-circle',
                'title': 'Great Savings!',
                'message': f'You\'re only spending {spending_ratio:.0f}% of your income. Keep it up!'
            })
    
    # Category concentration
    category_totals = defaultdict(float)
    for t in transactions:
        if t.get('transaction_type') == 'expense':
            category_totals[t.get('category', 'Other')] += t['amount']
    
    if category_totals:
        max_category = max(category_totals.items(), key=lambda x: x[1])
        if total_expense > 0 and (max_category[1] / total_expense) > 0.4:
            insights.append({
                'type': 'info',
                'icon': 'bx-info-circle',
                'title': 'Category Focus',
                'message': f'{max_category[0]} accounts for {(max_category[1]/total_expense*100):.0f}% of your spending.'
            })
    
    # Trend analysis
    if len(transactions) >= 60:  # At least 2 months of data
        mid_point = len(transactions) // 2
        first_half_expense = sum(t['amount'] for t in transactions[:mid_point] if t.get('transaction_type') == 'expense')
        second_half_expense = sum(t['amount'] for t in transactions[mid_point:] if t.get('transaction_type') == 'expense')
        
        if second_half_expense > first_half_expense * 1.2:
            insights.append({
                'type': 'warning',
                'icon': 'bx-trending-up',
                'title': 'Spending Increasing',
                'message': 'Your spending has increased by more than 20% recently.'
            })
        elif second_half_expense < first_half_expense * 0.8:
            insights.append({
                'type': 'success',
                'icon': 'bx-trending-down',
                'title': 'Spending Decreasing',
                'message': 'Great! Your spending has decreased by more than 20%.'
            })
    
    # Daily average insight
    if avg_daily_expense > 100:
        monthly_projection = avg_daily_expense * 30
        insights.append({
            'type': 'info',
            'icon': 'bx-calculator',
            'title': 'Monthly Projection',
            'message': f'At your current rate, you\'ll spend ৳{monthly_projection:.2f} this month.'
        })
    
    return insights
