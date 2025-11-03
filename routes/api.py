from flask import Blueprint, jsonify, request
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
