import os
import sqlite3
from pathlib import Path

def create_project_structure():
    """Create the TripMate project directory structure"""
    base_dir = Path("tripmate")
    
    directories = [
        base_dir,
        base_dir / "models",
        base_dir / "routes",
        base_dir / "static",
        base_dir / "static" / "css",
        base_dir / "static" / "js",
        base_dir / "templates",
        base_dir / "utils",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    return base_dir

def create_requirements_txt(base_dir):
    """Generate requirements.txt"""
    content = """Flask==3.0.0
Werkzeug==3.0.1
"""
    with open(base_dir / "requirements.txt", "w") as f:
        f.write(content)

def create_database_schema(base_dir):
    """Create SQLite database with schema and seed data"""
    db_path = base_dir / "tripmate.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS itineraries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        
        CREATE TABLE IF NOT EXISTS destinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            itinerary_id INTEGER NOT NULL,
            location TEXT NOT NULL,
            date TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (itinerary_id) REFERENCES itineraries(id) ON DELETE CASCADE
        );
        
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_type TEXT NOT NULL,
            item_name TEXT NOT NULL,
            date TEXT NOT NULL,
            price REAL NOT NULL,
            status TEXT DEFAULT 'confirmed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            total_budget REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            budget_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            FOREIGN KEY (budget_id) REFERENCES budgets(id) ON DELETE CASCADE
        );
    """)
    
    # Insert sample data
    from werkzeug.security import generate_password_hash
    
    cursor.execute("INSERT INTO users (name, email, hashed_password) VALUES (?, ?, ?)",
                   ("John Doe", "john@example.com", generate_password_hash("password123")))
    user_id = cursor.lastrowid
    
    cursor.execute("INSERT INTO itineraries (user_id, title) VALUES (?, ?)",
                   (user_id, "Summer Vacation 2025"))
    itinerary_id = cursor.lastrowid
    
    cursor.execute("INSERT INTO destinations (itinerary_id, location, date, notes) VALUES (?, ?, ?, ?)",
                   (itinerary_id, "Paris, France", "2025-07-01", "Visit Eiffel Tower"))
    
    cursor.execute("INSERT INTO bookings (user_id, item_type, item_name, date, price, status) VALUES (?, ?, ?, ?, ?, ?)",
                   (user_id, "flight", "Air France AF123", "2025-07-01", 450.00, "confirmed"))
    
    cursor.execute("INSERT INTO budgets (user_id, total_budget) VALUES (?, ?)",
                   (user_id, 5000.00))
    budget_id = cursor.lastrowid
    
    cursor.execute("INSERT INTO expenses (budget_id, category, amount, date, description) VALUES (?, ?, ?, ?, ?)",
                   (budget_id, "Flight", 450.00, "2025-07-01", "Paris flight"))
    
    conn.commit()
    conn.close()

def create_app_py(base_dir):
    """Generate main Flask application file"""
    content = """from flask import Flask, render_template, session, redirect, url_for
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = 'tripmate-secret-key-change-in-production'

DATABASE = 'tripmate.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

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
    app.run(debug=True, port=5000)
"""
    with open(base_dir / "app.py", "w") as f:
        f.write(content)

def create_utils_password(base_dir):
    """Generate password hashing utility"""
    content = """from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    return generate_password_hash(password)

def verify_password(hashed_password, password):
    return check_password_hash(hashed_password, password)
"""
    with open(base_dir / "utils" / "password.py", "w") as f:
        f.write(content)
    
    with open(base_dir / "utils" / "__init__.py", "w") as f:
        f.write("")

def create_models(base_dir):
    """Generate model files"""
    
    # models/__init__.py
    with open(base_dir / "models" / "__init__.py", "w") as f:
        f.write("")
    
    # models/user.py
    user_model = """import sqlite3

class User:
    def __init__(self, id, name, email, hashed_password):
        self.id = id
        self.name = name
        self.email = email
        self.hashed_password = hashed_password
    
    @staticmethod
    def get_by_email(email, conn):
        cursor = conn.cursor()
        user = cursor.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if user:
            return User(user['id'], user['name'], user['email'], user['hashed_password'])
        return None
    
    @staticmethod
    def create(name, email, hashed_password, conn):
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (name, email, hashed_password) VALUES (?, ?, ?)',
                      (name, email, hashed_password))
        conn.commit()
        return cursor.lastrowid
"""
    with open(base_dir / "models" / "user.py", "w") as f:
        f.write(user_model)

def create_routes(base_dir):
    """Generate all route files"""
    
    # routes/__init__.py
    with open(base_dir / "routes" / "__init__.py", "w") as f:
        f.write("")
    
    # routes/auth.py
    auth_routes = """from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
from utils.password import hash_password, verify_password
from models.user import User

bp = Blueprint('auth', __name__, url_prefix='/auth')

def get_db():
    conn = sqlite3.connect('tripmate.db')
    conn.row_factory = sqlite3.Row
    return conn

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db()
        
        existing_user = User.get_by_email(email, conn)
        if existing_user:
            flash('Email already registered')
            conn.close()
            return redirect(url_for('auth.register'))
        
        hashed_password = hash_password(password)
        user_id = User.create(name, email, hashed_password, conn)
        
        conn.close()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db()
        user = User.get_by_email(email, conn)
        conn.close()
        
        if user and verify_password(user.hashed_password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password')
    
    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
"""
    with open(base_dir / "routes" / "auth.py", "w") as f:
        f.write(auth_routes)
    
    # routes/itinerary.py
    itinerary_routes = """from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
from functools import wraps

bp = Blueprint('itinerary', __name__, url_prefix='/itinerary')

def get_db():
    conn = sqlite3.connect('tripmate.db')
    conn.row_factory = sqlite3.Row
    return conn

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
"""
    with open(base_dir / "routes" / "itinerary.py", "w") as f:
        f.write(itinerary_routes)
    
    # routes/booking.py
    booking_routes = """from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
from functools import wraps
import random

bp = Blueprint('booking', __name__, url_prefix='/booking')

def get_db():
    conn = sqlite3.connect('tripmate.db')
    conn.row_factory = sqlite3.Row
    return conn

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
"""
    with open(base_dir / "routes" / "booking.py", "w") as f:
        f.write(booking_routes)
    
    # routes/budget.py
    budget_routes = """from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
from functools import wraps

bp = Blueprint('budget', __name__, url_prefix='/budget')

def get_db():
    conn = sqlite3.connect('tripmate.db')
    conn.row_factory = sqlite3.Row
    return conn

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
"""
    with open(base_dir / "routes" / "budget.py", "w") as f:
        f.write(budget_routes)
    
    # routes/reports.py
    reports_routes = """from flask import Blueprint, render_template, session, redirect, url_for
import sqlite3
from functools import wraps

bp = Blueprint('reports', __name__, url_prefix='/reports')

def get_db():
    conn = sqlite3.connect('tripmate.db')
    conn.row_factory = sqlite3.Row
    return conn

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
"""
    with open(base_dir / "routes" / "reports.py", "w") as f:
        f.write(reports_routes)

def create_templates(base_dir):
    """Generate all HTML templates"""
    
    # templates/base.html
    base_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}TripMate{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    {% if session.user_id %}
    <nav class="navbar">
        <div class="container">
            <a href="{{ url_for('dashboard') }}" class="logo">TripMate</a>
            <ul class="nav-links">
                <li><a href="{{ url_for('dashboard') }}">Dashboard</a></li>
                <li><a href="{{ url_for('itinerary.index') }}">Itineraries</a></li>
                <li><a href="{{ url_for('booking.index') }}">Bookings</a></li>
                <li><a href="{{ url_for('budget.index') }}">Budget</a></li>
                <li><a href="{{ url_for('reports.index') }}">Reports</a></li>
                <li><a href="{{ url_for('auth.logout') }}">Logout</a></li>
            </ul>
        </div>
    </nav>
    {% endif %}
    
    <div class="container main-content">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="alert">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </div>
    
    <script src="{{ url_for('static', filename='js/script.js') }}"></script>
</body>
</html>
"""
    with open(base_dir / "templates" / "base.html", "w") as f:
        f.write(base_html)
    
    # templates/login.html
    login_html = """{% extends "base.html" %}

{% block title %}Login - TripMate{% endblock %}

{% block content %}
<div class="auth-container">
    <h2>Login to TripMate</h2>
    <form method="POST" action="{{ url_for('auth.login') }}">
        <div class="form-group">
            <label for="email">Email:</label>
            <input type="email" id="email" name="email" required>
        </div>
        <div class="form-group">
            <label for="password">Password:</label>
            <input type="password" id="password" name="password" required>
        </div>
        <button type="submit" class="btn btn-primary">Login</button>
    </form>
    <p class="auth-link">Don't have an account? <a href="{{ url_for('auth.register') }}">Register here</a></p>
</div>
{% endblock %}
"""
    with open(base_dir / "templates" / "login.html", "w") as f:
        f.write(login_html)
    
    # templates/register.html
    register_html = """{% extends "base.html" %}

{% block title %}Register - TripMate{% endblock %}

{% block content %}
<div class="auth-container">
    <h2>Register for TripMate</h2>
    <form method="POST" action="{{ url_for('auth.register') }}">
        <div class="form-group">
            <label for="name">Name:</label>
            <input type="text" id="name" name="name" required>
        </div>
        <div class="form-group">
            <label for="email">Email:</label>
            <input type="email" id="email" name="email" required>
        </div>
        <div class="form-group">
            <label for="password">Password:</label>
            <input type="password" id="password" name="password" required>
        </div>
        <button type="submit" class="btn btn-primary">Register</button>
    </form>
    <p class="auth-link">Already have an account? <a href="{{ url_for('auth.login') }}">Login here</a></p>
</div>
{% endblock %}
"""
    with open(base_dir / "templates" / "register.html", "w") as f:
        f.write(register_html)
    
    # templates/dashboard.html
    dashboard_html = """{% extends "base.html" %}

{% block title %}Dashboard - TripMate{% endblock %}

{% block content %}
<h1>Welcome, {{ user_name }}!</h1>

<div class="dashboard-grid">
    <div class="dashboard-card">
        <h3>Recent Itineraries</h3>
        {% if itineraries %}
            <ul>
            {% for itinerary in itineraries %}
                <li>
                    <a href="{{ url_for('itinerary.view', itinerary_id=itinerary.id) }}">
                        {{ itinerary.title }}
                    </a>
                </li>
            {% endfor %}
            </ul>
        {% else %}
            <p>No itineraries yet</p>
        {% endif %}
        <a href="{{ url_for('itinerary.index') }}" class="btn btn-secondary">View All</a>
    </div>
    
    <div class="dashboard-card">
        <h3>Recent Bookings</h3>
        {% if bookings %}
            <ul>
            {% for booking in bookings %}
                <li>{{ booking.item_name }} - ${{ booking.price }}</li>
            {% endfor %}
            </ul>
        {% else %}
            <p>No bookings yet</p>
        {% endif %}
        <a href="{{ url_for('booking.index') }}" class="btn btn-secondary">View All</a>
    </div>
    
    <div class="dashboard-card">
        <h3>Budget Summary</h3>
        {% if budget %}
            <p>Total Budget: ${{ budget.total_budget }}</p>
            <p>Spent: ${{ total_expenses }}</p>
            <p>Remaining: ${{ budget.total_budget - total_expenses }}</p>
        {% else %}
            <p>No budget set</p>
        {% endif %}
        <a href="{{ url_for('budget.index') }}" class="btn btn-secondary">Manage Budget</a>
    </div>
</div>
{% endblock %}
"""
    with open(base_dir / "templates" / "dashboard.html", "w") as f:
        f.write(dashboard_html)
    
    # templates/itinerary.html
    itinerary_html = """{% extends "base.html" %}

{% block title %}Itineraries - TripMate{% endblock %}

{% block content %}
<h1>My Itineraries</h1>

<div class="form-card">
    <h3>Create New Itinerary</h3>
    <form method="POST" action="{{ url_for('itinerary.create') }}">
        <div class="form-group">
            <label for="title">Title:</label>
            <input type="text" id="title" name="title" required>
        </div>
        <button type="submit" class="btn btn-primary">Create</button>
    </form>
</div>

<div class="itinerary-list">
    {% for itinerary in itineraries %}
        <div class="card">
            <h3>{{ itinerary.title }}</h3>
            <p>Created: {{ itinerary.created_at }}</p>
            <a href="{{ url_for('itinerary.view', itinerary_id=itinerary.id) }}" class="btn btn-secondary">View Details</a>
        </div>
    {% endfor %}
</div>
{% endblock %}
"""
    with open(base_dir / "templates" / "itinerary.html", "w") as f:
        f.write(itinerary_html)
    
    # templates/itinerary_detail.html
    itinerary_detail_html = """{% extends "base.html" %}

{% block title %}{{ itinerary.title }} - TripMate{% endblock %}

{% block content %}
<h1>{{ itinerary.title }}</h1>

<div class="form-card">
    <h3>Add Destination</h3>
    <form method="POST" action="{{ url_for('itinerary.add_destination', itinerary_id=itinerary.id) }}">
        <div class="form-group">
            <label for="location">Location:</label>
            <input type="text" id="location" name="location" required>
        </div>
        <div class="form-group">
            <label for="date">Date:</label>
            <input type="date" id="date" name="date" required>
        </div>
        <div class="form-group">
            <label for="notes">Notes:</label>
            <textarea id="notes" name="notes" rows="3"></textarea>
        </div>
        <button type="submit" class="btn btn-primary">Add Destination</button>
    </form>
</div>

<h2>Destinations</h2>
<div class="destination-list">
    {% for destination in destinations %}
        <div class="card">
            <h3>{{ destination.location }}</h3>
            <p><strong>Date:</strong> {{ destination.date }}</p>
            <p><strong>Notes:</strong> {{ destination.notes }}</p>
            <form method="POST" action="{{ url_for('itinerary.delete_destination', destination_id=destination.id) }}" style="display:inline;">
                <button type="submit" class="btn btn-danger">Delete</button>
            </form>
        </div>
    {% endfor %}
</div>
{% endblock %}
"""
    with open(base_dir / "templates" / "itinerary_detail.html", "w") as f:
        f.write(itinerary_detail_html)
    
    # templates/booking.html
    booking_html = """{% extends "base.html" %}

{% block title %}Bookings - TripMate{% endblock %}

{% block content %}
<h1>My Bookings</h1>

<div class="booking-search">
    <h2>Search Flights</h2>
    <div class="search-results">
        {% for flight in flights %}
            <div class="card">
                <h3>{{ flight.name }}</h3>
                <p>Departure: {{ flight.departure }} | Arrival: {{ flight.arrival }}</p>
                <p><strong>Price: ${{ flight.price }}</strong></p>
                <form method="POST" action="{{ url_for('booking.book') }}">
                    <input type="hidden" name="item_type" value="flight">
                    <input type="hidden" name="item_name" value="{{ flight.name }}">
                    <input type="hidden" name="price" value="{{ flight.price }}">
                    <div class="form-group">
                        <label for="date">Travel Date:</label>
                        <input type="date" name="date" required>
                    </div>
                    <button type="submit" class="btn btn-primary">Book</button>
                </form>
            </div>
        {% endfor %}
    </div>
    
    <h2>Search Hotels</h2>
    <div class="search-results">
        {% for hotel in hotels %}
            <div class="card">
                <h3>{{ hotel.name }}</h3>
                <p>Rating: {{ hotel.rating }} stars</p>
                <p><strong>Price: ${{ hotel.price }}/night</strong></p>
                <form method="POST" action="{{ url_for('booking.book') }}">
                    <input type="hidden" name="item_type" value="hotel">
                    <input type="hidden" name="item_name" value="{{ hotel.name }}">
                    <input type="hidden" name="price" value="{{ hotel.price }}">
                    <div class="form-group">
                        <label for="date">Check-in Date:</label>
                        <input type="date" name="date" required>
                    </div>
                    <button type="submit" class="btn btn-primary">Book</button>
                </form>
            </div>
        {% endfor %}
    </div>
</div>

<h2>My Bookings</h2>
<div class="booking-list">
    {% for booking in bookings %}
        <div class="card">
            <h3>{{ booking.item_name }}</h3>
            <p><strong>Type:</strong> {{ booking.item_type }}</p>
            <p><strong>Date:</strong> {{ booking.date }}</p>
            <p><strong>Price:</strong> ${{ booking.price }}</p>
            <p><strong>Status:</strong> {{ booking.status }}</p>
        </div>
    {% endfor %}
</div>
{% endblock %}
"""
    with open(base_dir / "templates" / "booking.html", "w") as f:
        f.write(booking_html)
    
    # templates/budget.html
    budget_html = """{% extends "base.html" %}

{% block title %}Budget - TripMate{% endblock %}

{% block content %}
<h1>Budget Tracker</h1>

<div class="form-card">
    <h3>Set Total Budget</h3>
    <form method="POST" action="{{ url_for('budget.set_budget') }}">
        <div class="form-group">
            <label for="total_budget">Total Budget ($):</label>
            <input type="number" step="0.01" id="total_budget" name="total_budget" 
                   value="{{ budget.total_budget if budget else '' }}" required>
        </div>
        <button type="submit" class="btn btn-primary">Set Budget</button>
    </form>
</div>

{% if budget %}
<div class="budget-summary">
    <div class="card">
        <h3>Budget Overview</h3>
        <p><strong>Total Budget:</strong> ${{ budget.total_budget }}</p>
        <p><strong>Total Spent:</strong> ${{ total_expenses }}</p>
        <p><strong>Remaining:</strong> ${{ remaining }}</p>
    </div>
</div>

<div class="form-card">
    <h3>Add Expense</h3>
    <form method="POST" action="{{ url_for('budget.add_expense') }}">
        <div class="form-group">
            <label for="category">Category:</label>
            <input type="text" id="category" name="category" required>
        </div>
        <div class="form-group">
            <label for="amount">Amount ($):</label>
            <input type="number" step="0.01" id="amount" name="amount" required>
        </div>
        <div class="form-group">
            <label for="date">Date:</label>
            <input type="date" id="date" name="date" required>
        </div>
        <div class="form-group">
            <label for="description">Description:</label>
            <input type="text" id="description" name="description">
        </div>
        <button type="submit" class="btn btn-primary">Add Expense</button>
    </form>
</div>

<h2>Expenses</h2>
<div class="expense-list">
    {% for expense in expenses %}
        <div class="card">
            <h3>{{ expense.category }}</h3>
            <p><strong>Amount:</strong> ${{ expense.amount }}</p>
            <p><strong>Date:</strong> {{ expense.date }}</p>
            <p><strong>Description:</strong> {{ expense.description }}</p>
        </div>
    {% endfor %}
</div>
{% endif %}
{% endblock %}
"""
    with open(base_dir / "templates" / "budget.html", "w") as f:
        f.write(budget_html)
    
    # templates/report.html
    report_html = """{% extends "base.html" %}

{% block title %}Reports - TripMate{% endblock %}

{% block content %}
<h1>Travel Reports</h1>

<div class="report-section">
    <h2>Itinerary Summary</h2>
    {% for data in itinerary_data %}
        <div class="card">
            <h3>{{ data.itinerary.title }}</h3>
            <p><strong>Created:</strong> {{ data.itinerary.created_at }}</p>
            <h4>Destinations:</h4>
            <ul>
            {% for dest in data.destinations %}
                <li>{{ dest.location }} - {{ dest.date }}</li>
            {% endfor %}
            </ul>
        </div>
    {% endfor %}
</div>

<div class="report-section">
    <h2>Booking Summary</h2>
    <p><strong>Total Bookings:</strong> {{ bookings|length }}</p>
    <p><strong>Total Cost:</strong> ${{ total_booking_cost }}</p>
    {% for booking in bookings %}
        <div class="card">
            <h3>{{ booking.item_name }}</h3>
            <p><strong>Type:</strong> {{ booking.item_type }}</p>
            <p><strong>Date:</strong> {{ booking.date }}</p>
            <p><strong>Price:</strong> ${{ booking.price }}</p>
        </div>
    {% endfor %}
</div>

<div class="report-section">
    <h2>Budget Summary</h2>
    {% if budget %}
        <div class="card">
            <p><strong>Total Budget:</strong> ${{ budget.total_budget }}</p>
            <p><strong>Total Expenses:</strong> ${{ total_expenses }}</p>
            <p><strong>Remaining:</strong> ${{ remaining }}</p>
            
            <h4>Expense Breakdown:</h4>
            {% for expense in expenses %}
                <p>{{ expense.category }}: ${{ expense.amount }} ({{ expense.date }})</p>
            {% endfor %}
        </div>
    {% else %}
        <p>No budget data available</p>
    {% endif %}
</div>
{% endblock %}
"""
    with open(base_dir / "templates" / "report.html", "w") as f:
        f.write(report_html)

def create_static_files(base_dir):
    """Generate CSS and JS files"""
    
    # static/css/style.css
    css_content = """* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: #f4f4f4;
    color: #333;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.navbar {
    background-color: #2c3e50;
    color: white;
    padding: 15px 0;
    margin-bottom: 30px;
}

.navbar .container {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    font-size: 24px;
    font-weight: bold;
    color: white;
    text-decoration: none;
}

.nav-links {
    display: flex;
    list-style: none;
    gap: 20px;
}

.nav-links a {
    color: white;
    text-decoration: none;
    padding: 8px 15px;
    border-radius: 4px;
    transition: background-color 0.3s;
}

.nav-links a:hover {
    background-color: #34495e;
}

.main-content {
    min-height: 70vh;
}

.auth-container {
    max-width: 400px;
    margin: 50px auto;
    background: white;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.auth-container h2 {
    margin-bottom: 20px;
    color: #2c3e50;
}

.form-group {
    margin-bottom: 15px;
}

.form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: 500;
}

.form-group input,
.form-group textarea,
.form-group select {
    width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
}

.btn {
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    transition: background-color 0.3s;
}

.btn-primary {
    background-color: #3498db;
    color: white;
}

.btn-primary:hover {
    background-color: #2980b9;
}

.btn-secondary {
    background-color: #95a5a6;
    color: white;
}

.btn-secondary:hover {
    background-color: #7f8c8d;
}

.btn-danger {
    background-color: #e74c3c;
    color: white;
}

.btn-danger:hover {
    background-color: #c0392b;
}

.auth-link {
    margin-top: 15px;
    text-align: center;
}

.alert {
    padding: 15px;
    margin-bottom: 20px;
    border-radius: 4px;
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
}

.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    margin-top: 20px;
}

.dashboard-card {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.dashboard-card h3 {
    margin-bottom: 15px;
    color: #2c3e50;
}

.dashboard-card ul {
    list-style: none;
    margin-bottom: 15px;
}

.dashboard-card li {
    padding: 8px 0;
    border-bottom: 1px solid #eee;
}

.card {
    background: white;
    padding: 20px;
    margin-bottom: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.card h3 {
    margin-bottom: 10px;
    color: #2c3e50;
}

.form-card {
    background: white;
    padding: 20px;
    margin-bottom: 30px;
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.itinerary-list,
.destination-list,
.booking-list,
.expense-list {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
}

.budget-summary {
    margin-bottom: 30px;
}

.report-section {
    margin-bottom: 40px;
}

.report-section h2 {
    margin-bottom: 20px;
    color: #2c3e50;
    border-bottom: 2px solid #3498db;
    padding-bottom: 10px;
}

.search-results {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    margin-bottom: 40px;
}
"""
    with open(base_dir / "static" / "css" / "style.css", "w") as f:
        f.write(css_content)
    
    # static/js/script.js
    js_content = """document.addEventListener('DOMContentLoaded', function() {
    console.log('TripMate loaded successfully');
    
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 3000);
    });
});
"""
    with open(base_dir / "static" / "js" / "script.js", "w") as f:
        f.write(js_content)

def main():
    """Main function to generate the entire project"""
    print("Generating TripMate project...")
    
    base_dir = create_project_structure()
    print("✓ Created directory structure")
    
    create_requirements_txt(base_dir)
    print("✓ Generated requirements.txt")
    
    create_database_schema(base_dir)
    print("✓ Created database with schema and seed data")
    
    create_app_py(base_dir)
    print("✓ Generated app.py")
    
    create_utils_password(base_dir)
    print("✓ Generated utils/password.py")
    
    create_models(base_dir)
    print("✓ Generated models")
    
    create_routes(base_dir)
    print("✓ Generated routes")
    
    create_templates(base_dir)
    print("✓ Generated templates")
    
    create_static_files(base_dir)
    print("✓ Generated static files")
    
    print("\n" + "="*50)
    print("TripMate project generated successfully!")
    print("="*50)
    print("\nTo run the application:")
    print("1. cd tripmate")
    print("2. pip install -r requirements.txt")
    print("3. python app.py")
    print("\nDefault login credentials:")
    print("Email: john@example.com")
    print("Password: password123")
    print("\nThe app will be available at http://127.0.0.1:5000")

if __name__ == "__main__":
    main()
