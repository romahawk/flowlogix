from app.models import ActivityLog, db
from flask_login import current_user
from datetime import datetime

def log_activity(action, details):
    from flask import has_request_context
    user_id = current_user.id if has_request_context() and current_user.is_authenticated else None
    log = ActivityLog(
        user_id=user_id,
        action=action,
        details=details,
        timestamp=datetime.utcnow()
    )
    db.session.add(log)
    db.session.commit()
