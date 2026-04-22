import os

from flask import Flask, render_template, session, redirect, url_for
from functools import wraps

from db import get_db

app = Flask(__name__)
app.secret_key = os.environ.get('TRIPMATE_SECRET_KEY', 'tripmate-secret-key-change-in-production')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

from routes import auth, itinerary, booking, budget, reports

app.register_blueprint(auth.bp)
app.register_blueprint(itinerary.bp)
app.register_blueprint(booking.bp)
app.register_blueprint(budget.bp)
app.register_blueprint(reports.bp)

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()
    cursor = conn.cursor()
    
    user_id = session['user_id']
    
    itineraries = cursor.execute(
        'SELECT * FROM itineraries WHERE user_id = ? ORDER BY created_at DESC LIMIT 5',
        (user_id,)
    ).fetchall()
    
    bookings = cursor.execute(
        'SELECT * FROM bookings WHERE user_id = ? ORDER BY created_at DESC LIMIT 5',
        (user_id,)
    ).fetchall()
    
    budget = cursor.execute(
        'SELECT * FROM budgets WHERE user_id = ?',
        (user_id,)
    ).fetchone()
    
    total_expenses = 0
    if budget:
        expenses = cursor.execute(
            'SELECT SUM(amount) as total FROM expenses WHERE budget_id = ?',
            (budget['id'],)
        ).fetchone()
        total_expenses = expenses['total'] if expenses['total'] else 0
    
    conn.close()
    
    return render_template('dashboard.html', 
                         itineraries=itineraries,
                         bookings=bookings,
                         budget=budget,
                         total_expenses=total_expenses,
                         user_name=session.get('user_name'))

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true',
            host='0.0.0.0',
            port=int(os.environ.get('PORT', '8000')))
