from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils.password import hash_password, verify_password
from models.user import User
from db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

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
