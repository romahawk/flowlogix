from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import ActivityLog, User, db
from app.roles import role_required
from flask import request, redirect, url_for, flash

activity_bp = Blueprint('activity', __name__)

@activity_bp.route('/activity_logs')
@login_required
@role_required('admin')
def activity_logs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    pagination = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).paginate(page=page, per_page=per_page)
    logs = pagination.items

    return render_template("activity_logs.html", logs=logs, pagination=pagination, per_page=per_page)


# Delete single log
@activity_bp.route('/activity_logs/delete/<int:log_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_log(log_id):
    log = ActivityLog.query.get_or_404(log_id)
    db.session.delete(log)
    db.session.commit()
    flash("Log entry deleted.", "success")
    return redirect(url_for('activity.activity_logs'))

# Delete all logs
@activity_bp.route('/activity_logs/clear', methods=['POST'])
@login_required
@role_required('admin')
def clear_logs():
    ActivityLog.query.delete()
    db.session.commit()
    flash("All activity logs have been cleared.", "success")
    return redirect(url_for('activity.activity_logs'))