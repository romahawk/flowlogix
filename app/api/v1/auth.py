from flask_login import login_required, current_user

from . import api_v1_bp
from .errors import ok


@api_v1_bp.route("/auth/me", methods=["GET"])
@login_required
def me():
    return ok({
        "id": current_user.id,
        "username": getattr(current_user, "username", ""),
        "role": getattr(current_user, "role", "user"),
    })
