from flask import Blueprint

api_v1_bp = Blueprint("api_v1", __name__)

from . import orders, auth  # noqa: E402,F401
