from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from db import get_db

bp = Blueprint('budget', __name__, url_prefix='/budget')

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
    
    budget = cursor.execute(
        'SELECT * FROM budgets WHERE user_id = ?',
        (session['user_id'],)
    ).fetchone()
    
    expenses = []
    total_expenses = 0
    remaining = 0
    
    if budget:
        expenses = cursor.execute(
            'SELECT * FROM expenses WHERE budget_id = ? ORDER BY date DESC',
            (budget['id'],)
        ).fetchall()
        
        total = cursor.execute(
            'SELECT SUM(amount) as total FROM expenses WHERE budget_id = ?',
            (budget['id'],)
        ).fetchone()
        
        total_expenses = total['total'] if total['total'] else 0
        remaining = budget['total_budget'] - total_expenses
    
    conn.close()
    
    return render_template('budget.html', budget=budget, expenses=expenses, 
                         total_expenses=total_expenses, remaining=remaining)

@bp.route('/set_budget', methods=['POST'])
@login_required
def set_budget():
    total_budget = float(request.form['total_budget'])
    
    conn = get_db()
    cursor = conn.cursor()
    
    existing = cursor.execute('SELECT * FROM budgets WHERE user_id = ?', (session['user_id'],)).fetchone()
    
    if existing:
        cursor.execute('UPDATE budgets SET total_budget = ? WHERE user_id = ?',
                      (total_budget, session['user_id']))
    else:
        cursor.execute('INSERT INTO budgets (user_id, total_budget) VALUES (?, ?)',
                      (session['user_id'], total_budget))
    
    conn.commit()
    conn.close()
    
    flash('Budget set successfully')
    return redirect(url_for('budget.index'))

@bp.route('/add_expense', methods=['POST'])
@login_required
def add_expense():
    conn = get_db()
    cursor = conn.cursor()
    
    budget = cursor.execute('SELECT * FROM budgets WHERE user_id = ?', (session['user_id'],)).fetchone()
    
    if not budget:
        flash('Please set a budget first')
        conn.close()
        return redirect(url_for('budget.index'))
    
    category = request.form['category']
    amount = float(request.form['amount'])
    date = request.form['date']
    description = request.form.get('description', '')
    
    cursor.execute(
        'INSERT INTO expenses (budget_id, category, amount, date, description) VALUES (?, ?, ?, ?, ?)',
        (budget['id'], category, amount, date, description)
    )
    conn.commit()
    conn.close()
    
    flash('Expense added successfully')
    return redirect(url_for('budget.index'))
