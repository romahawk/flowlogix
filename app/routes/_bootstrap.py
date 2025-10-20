# app/routes/_bootstrap.py
from __future__ import annotations
from typing import Optional
from flask import current_app


def _already_wired(app) -> bool:
    """Prevent double-registration across multiple create_app() calls or imports."""
    return bool(app.config.get("_ROUTES_WIRED", False))


def _mark_wired(app) -> None:
    app.config["_ROUTES_WIRED"] = True


def register_routes(app):
    """Call your primary registrar once; fallback to core routes only if it fails."""
    if _already_wired(app):
        return

    # 1) Try your existing big registrar first
    try:
        from app.routes import __init__ as big_routes  # your 248-line module
        if hasattr(big_routes, "register_routes"):
            big_routes.register_routes(app)
            _mark_wired(app)
            return
    except Exception as exc:
        app.logger.warning(f"[routes] big registrar raised; falling back: {exc}")

    # 2) Fallback: only the essential blueprints so the app boots
    try:
        from app.routes.auth_routes import auth_bp
        from app.routes.dashboard_routes import dashboard_bp
        from app.routes.order_routes import order_bp
        from app.routes.warehouse_routes import warehouse_bp
        from app.routes.delivered_routes import delivered_bp
    except Exception as exc:
        app.logger.warning(f"[routes] fallback import failed: {exc}")
        return

    for bp in (auth_bp, dashboard_bp, order_bp, warehouse_bp, delivered_bp):
        try:
            app.register_blueprint(bp)
        except Exception as exc:
            app.logger.warning(f"[routes] skip {getattr(bp,'name',bp)}: {exc}")

    _mark_wired(app)
