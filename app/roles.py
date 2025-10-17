# roles.py
from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if str(current_user.role).lower() != required_role.lower():
                flash("You do not have access to this page.", "danger")
                return redirect(url_for('dashboard.dashboard'))
            return f(*args, **kwargs)
        return wrapped
    return decorator

# === Role Constants ===
ADMIN = 'admin'
SUPERUSER = 'superuser'

# Define company-specific roles
USER_COMPANY_ROLES = [
    'user_company1',
    'user_company2',
    'user_company3',
    'user_company4',
    'user_company5',
    'user_company6',
    'user_company7',
    'user_company8',
    'user_company9',
    'user_company10',
]

ALL_ROLES = [ADMIN, SUPERUSER] + USER_COMPANY_ROLES

# === Role Permissions Map ===
ROLE_PERMISSIONS = {
    ADMIN: {
        'can_view_all': True,
        'can_edit': True,
        'can_manage_users': True,
    },
    SUPERUSER: {
        'can_view_all': True,
        'can_edit': False,
        'can_manage_users': False,
    },
}

# Extend permissions to all company users (read/write, but scoped)
for role in USER_COMPANY_ROLES:
    ROLE_PERMISSIONS[role] = {
        'can_view_all': False,
        'can_edit': True,
        'can_manage_users': False,
    }

# === Utility Functions ===

def can_view_all(role):
    """Can this role view all orders in the system?"""
    return ROLE_PERMISSIONS.get(role, {}).get('can_view_all', False)

def can_edit(role):
    """Can this role add/edit/delete orders?"""
    return ROLE_PERMISSIONS.get(role, {}).get('can_edit', False)

def can_manage_users(role):
    """Can this role create/delete users?"""
    return ROLE_PERMISSIONS.get(role, {}).get('can_manage_users', False)
