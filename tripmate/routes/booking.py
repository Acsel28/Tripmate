from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
import random
from db import get_db

bp = Blueprint('booking', __name__, url_prefix='/booking')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

DUMMY_FLIGHTS = [
    {'name': 'Air France AF123', 'price': 450.00, 'departure': '08:00', 'arrival': '12:00'},
    {'name': 'Lufthansa LH456', 'price': 520.00, 'departure': '10:30', 'arrival': '14:30'},
    {'name': 'British Airways BA789', 'price': 480.00, 'departure': '14:00', 'arrival': '18:00'},
]

DUMMY_HOTELS = [
    {'name': 'Grand Hotel Paris', 'price': 180.00, 'rating': 4.5},
    {'name': 'Cozy Inn', 'price': 120.00, 'rating': 4.0},
    {'name': 'Luxury Resort', 'price': 350.00, 'rating': 5.0},
]

@bp.route('/')
@login_required
def index():
    conn = get_db()
    cursor = conn.cursor()
    
    bookings = cursor.execute(
        'SELECT * FROM bookings WHERE user_id = ? ORDER BY created_at DESC',
        (session['user_id'],)
    ).fetchall()
    
    conn.close()
    
    return render_template('booking.html', bookings=bookings, flights=DUMMY_FLIGHTS, hotels=DUMMY_HOTELS)

@bp.route('/book', methods=['POST'])
@login_required
def book():
    item_type = request.form['item_type']
    item_name = request.form['item_name']
    date = request.form['date']
    price = float(request.form['price'])
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO bookings (user_id, item_type, item_name, date, price, status) VALUES (?, ?, ?, ?, ?, ?)',
        (session['user_id'], item_type, item_name, date, price, 'confirmed')
    )
    conn.commit()
    conn.close()
    
    flash('Booking confirmed successfully')
    return redirect(url_for('booking.index'))
