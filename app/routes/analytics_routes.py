from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import text
from app.database import db
from app.utils.role_check import is_admin_or_superuser

# ✅ Define blueprint BEFORE using it
analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_bp.route('/')
@login_required
def view_analytics():
    if not is_admin_or_superuser(current_user):
        return "Access denied", 403
    return render_template('analytics.html', title='Analytics Dashboard')


@analytics_bp.route('/api/transit_efficiency')
@login_required
def transit_efficiency_data():
    if not is_admin_or_superuser(current_user):
        return jsonify({'error': 'Forbidden'}), 403

    query = text("""
        SELECT 
            transport,
            julianday(COALESCE(ata, eta)) - julianday(etd) AS delivery_days
        FROM "order"
        WHERE etd IS NOT NULL
    """)

    result = db.session.execute(query)
    data = {}

    for row in result:
        transport = row[0]
        days = row[1]
        if transport and days is not None:
            data.setdefault(transport, []).append(days)

    # Calculate averages
    averages = {k: round(sum(v) / len(v), 2) for k, v in data.items()}

    return jsonify(averages)
