from flask import Blueprint, render_template, session, redirect, url_for
from functools import wraps
from db import get_db

bp = Blueprint('reports', __name__, url_prefix='/reports')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
def index():
    conn = get_db()
    cursor = conn.cursor()
    
    user_id = session['user_id']
    
    itineraries = cursor.execute(
        'SELECT * FROM itineraries WHERE user_id = ?',
        (user_id,)
    ).fetchall()
    
    itinerary_data = []
    for itinerary in itineraries:
        destinations = cursor.execute(
            'SELECT * FROM destinations WHERE itinerary_id = ?',
            (itinerary['id'],)
        ).fetchall()
        itinerary_data.append({
            'itinerary': itinerary,
            'destinations': destinations
        })
    
    bookings = cursor.execute(
        'SELECT * FROM bookings WHERE user_id = ?',
        (user_id,)
    ).fetchall()
    
    total_booking_cost = sum([b['price'] for b in bookings])
    
    budget = cursor.execute(
        'SELECT * FROM budgets WHERE user_id = ?',
        (user_id,)
    ).fetchone()
    
    expenses = []
    total_expenses = 0
    remaining = 0
    
    if budget:
        expenses = cursor.execute(
            'SELECT * FROM expenses WHERE budget_id = ?',
            (budget['id'],)
        ).fetchall()
        
        total = cursor.execute(
            'SELECT SUM(amount) as total FROM expenses WHERE budget_id = ?',
            (budget['id'],)
        ).fetchone()
        
        total_expenses = total['total'] if total['total'] else 0
        remaining = budget['total_budget'] - total_expenses
    
    conn.close()
    
    return render_template('report.html',
                         itinerary_data=itinerary_data,
                         bookings=bookings,
                         total_booking_cost=total_booking_cost,
                         budget=budget,
                         expenses=expenses,
                         total_expenses=total_expenses,
                         remaining=remaining)
