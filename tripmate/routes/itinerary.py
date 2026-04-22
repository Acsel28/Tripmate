from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from db import get_db

bp = Blueprint('itinerary', __name__, url_prefix='/itinerary')

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
    
    itineraries = cursor.execute(
        'SELECT * FROM itineraries WHERE user_id = ? ORDER BY created_at DESC',
        (session['user_id'],)
    ).fetchall()
    
    conn.close()
    
    return render_template('itinerary.html', itineraries=itineraries)

@bp.route('/create', methods=['POST'])
@login_required
def create():
    title = request.form['title']
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO itineraries (user_id, title) VALUES (?, ?)',
                  (session['user_id'], title))
    conn.commit()
    conn.close()
    
    flash('Itinerary created successfully')
    return redirect(url_for('itinerary.index'))

@bp.route('/<int:itinerary_id>')
@login_required
def view(itinerary_id):
    conn = get_db()
    cursor = conn.cursor()
    
    itinerary = cursor.execute(
        'SELECT * FROM itineraries WHERE id = ? AND user_id = ?',
        (itinerary_id, session['user_id'])
    ).fetchone()
    
    if not itinerary:
        flash('Itinerary not found')
        conn.close()
        return redirect(url_for('itinerary.index'))
    
    destinations = cursor.execute(
        'SELECT * FROM destinations WHERE itinerary_id = ? ORDER BY date',
        (itinerary_id,)
    ).fetchall()
    
    conn.close()
    
    return render_template('itinerary_detail.html', itinerary=itinerary, destinations=destinations)

@bp.route('/<int:itinerary_id>/add_destination', methods=['POST'])
@login_required
def add_destination(itinerary_id):
    location = request.form['location']
    date = request.form['date']
    notes = request.form.get('notes', '')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO destinations (itinerary_id, location, date, notes) VALUES (?, ?, ?, ?)',
                  (itinerary_id, location, date, notes))
    conn.commit()
    conn.close()
    
    flash('Destination added successfully')
    return redirect(url_for('itinerary.view', itinerary_id=itinerary_id))

@bp.route('/destination/<int:destination_id>/delete', methods=['POST'])
@login_required
def delete_destination(destination_id):
    conn = get_db()
    cursor = conn.cursor()
    
    destination = cursor.execute('SELECT * FROM destinations WHERE id = ?', (destination_id,)).fetchone()
    if destination:
        itinerary_id = destination['itinerary_id']
        cursor.execute('DELETE FROM destinations WHERE id = ?', (destination_id,))
        conn.commit()
        flash('Destination deleted successfully')
    
    conn.close()
    return redirect(url_for('itinerary.view', itinerary_id=itinerary_id))
