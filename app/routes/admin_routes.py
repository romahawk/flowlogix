from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import User, db
from app.roles import can_view_all

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/user_management')
@login_required
def user_management():
    if current_user.role != 'admin':
        flash("Access denied: Admins only.", "danger")
        return redirect(url_for('dashboard.dashboard'))

    users = User.query.all()
    return render_template('admin_users.html', users=users)

@admin_bp.route('/admin/change-role/<int:user_id>', methods=['POST'])
@login_required
def change_role(user_id):
    if current_user.role != 'admin':
        flash("Access denied: Admins only.", "danger")
        return redirect(url_for('dashboard.dashboard'))

    user = User.query.get_or_404(user_id)
    new_role = request.form.get('new_role')
    if new_role:
        user.role = new_role
        db.session.commit()
        flash(f"Role for {user.username} updated to {new_role}.", "success")

    return redirect(url_for('admin.user_management'))

@admin_bp.route('/admin/edit-user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'admin':
        flash("Access denied: Admins only.", "danger")
        return redirect(url_for('admin.user_management'))

    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username:
            user.username = username
        if password:
            user.set_password(password)
        db.session.commit()
        flash("User updated successfully.", "success")
        return redirect(url_for('admin.user_management'))

    return render_template('edit_user.html', user=user)


@admin_bp.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.id == user_id:
        flash("You can't delete your own account.", "danger")
        return redirect(url_for('admin.user_management'))

    user = User.query.get_or_404(user_id)
    
    if user.role == 'admin':
        flash("Admin users cannot be deleted.", "danger")
        return redirect(url_for('admin.user_management'))

    print(f"[DEBUG] Deleting user: {user.username} (ID: {user.id})")
    db.session.delete(user)
    db.session.commit()
    print("[DEBUG] Commit completed")

    flash(f"User {user.username} deleted.", "success")
    return redirect(url_for('admin.user_management'))


@admin_bp.route('/admin/add_user', methods=['POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        flash("Access denied: Admins only.", "danger")
        return redirect(url_for('admin.user_management'))

    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')

    if not username or not password:
        flash("Username and password are required.", "warning")
        return redirect(url_for('admin.user_management'))

    if User.query.filter_by(username=username).first():
        flash("Username already exists.", "warning")
        return redirect(url_for('admin.user_management'))

    new_user = User(username=username, role=role)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    flash("New user added successfully.", "success")
    return redirect(url_for('admin.user_management'))
