from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return render_template('landing.html')

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
                new_user = User(username=username)
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                flash('Registered successfully!', 'success')

    return render_template('login.html')


@auth_bp.route('/demo')
def demo_enter():
    """Direct demo entry — always resets session and auto-logs in as demo user."""
    from flask import current_app
    session.pop("demo_disable_auto_login", None)
    if not current_app.config.get("DEMO_MODE"):
        return redirect(url_for('auth.login'))
    u = User.query.filter_by(username="demo").first()
    if not u:
        u = User(username="demo", role="admin")
        try:
            setattr(u, "email", "demo@portfolio.app")
        except Exception:
            pass
        u.set_password("demo1234")
        db.session.add(u)
        db.session.commit()
    elif (u.role or '').lower() != 'admin':
        u.role = 'admin'
        db.session.commit()
    login_user(u, remember=False)
    return redirect(url_for('dashboard.dashboard'))


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()

    # ✅ user explicitly logged out → don't auto-login demo user again
    session["demo_disable_auto_login"] = True

    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
