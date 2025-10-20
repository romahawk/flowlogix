# app/routes/_bootstrap.py
from __future__ import annotations
from typing import Optional
from flask import current_app

def _optional(path: str, attr: str):
    try:
        mod = __import__(path, fromlist=[attr])
        return getattr(mod, attr)
    except Exception as exc:
        current_app.logger.warning(f"[routes] optional import failed: {path}.{attr}: {exc}")
        return None

def register_routes(app):
    """
    Safe bootstrap that imports your existing big registrar and any optional
    blueprints without preventing the app from starting if one fails.
    """
    # Your existing registrar (keeps all your current wiring)
    try:
        from app.routes import __init__ as big_routes  # your 248-line module
        if hasattr(big_routes, "register_routes"):
            big_routes.register_routes(app)
            return
    except Exception as exc:
        app.logger.warning(f"[routes] fallback path: existing registrar raised: {exc}")

    # Fallback: register core blueprints so the app still boots
    from app.routes.auth_routes import auth_bp
    from app.routes.dashboard_routes import dashboard_bp
    from app.routes.order_routes import order_bp
    from app.routes.warehouse_routes import warehouse_bp
    from app.routes.delivered_routes import delivered_bp

    for bp in (auth_bp, dashboard_bp, order_bp, warehouse_bp, delivered_bp):
        try:
            app.register_blueprint(bp)
        except Exception as exc:
            app.logger.warning(f"[routes] skip blueprint {getattr(bp,'name',bp)}: {exc}")
