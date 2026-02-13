from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'login':
            username = request.form['username']
            password = request.form['password']
            remember = True if request.form.get('remember') == 'on' else False

            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user, remember=remember)

                # ✅ user logged in intentionally → allow demo auto-login again
                session.pop("demo_disable_auto_login", None)

                flash('Logged in successfully!', 'success')
                return redirect(url_for('dashboard.dashboard'))
            else:
                flash('Invalid username or password.', 'danger')

        elif form_type == 'register':
            username = request.form['username']
            password = request.form['password']

            if not username or not password:
                flash('Please fill out all fields.', 'warning')
            elif User.query.filter_by(username=username).first():
                flash('Username already taken.', 'danger')
            else:
                hashed_password = generate_password_hash(password)
                new_user = User(username=username)
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                flash('Registered successfully!', 'success')

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()

    # ✅ user explicitly logged out → don't auto-login demo user again
    session["demo_disable_auto_login"] = True

    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
