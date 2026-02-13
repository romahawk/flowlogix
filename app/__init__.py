import os
import re
import uuid
from datetime import datetime
from flask import Flask, request, abort, redirect, jsonify, url_for, session
from flask_login import LoginManager, current_user, login_user
from flask_migrate import Migrate

from .database import db, init_db
from .models import User, Order

login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # type: ignore


def create_app():
    app = Flask(__name__)

    # === Absolute DB path anchored to project root; normalize relative sqlite URLs ===
    basedir = os.path.abspath(os.path.join(app.root_path, '..'))
    instance_dir = os.path.join(basedir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)

    default_db = os.path.join(instance_dir, 'supply_tracker.db')
    default_db_uri = f"sqlite:///{default_db.replace(os.sep, '/')}"

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')

    db_url = os.getenv('DATABASE_URL', default_db_uri)
    if db_url.startswith('sqlite:///') and not db_url.startswith('sqlite:////'):
        rel_path = db_url.replace('sqlite:///', '', 1).lstrip('/\\')
        abs_path = os.path.join(basedir, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        db_url = f"sqlite:///{abs_path.replace(os.sep, '/')}"

    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Demo flags
    app.config['DEMO_MODE'] = os.getenv('DEMO_MODE', 'false').lower() == 'true'
    app.config['DEMO_READONLY'] = os.getenv('DEMO_READONLY', 'true').lower() == 'true'
    app.config['DEMO_RESET_TOKEN'] = os.getenv('DEMO_RESET_TOKEN', 'change-me')
    app.config['DEMO_AUTO_LOGIN'] = os.getenv('DEMO_AUTO_LOGIN', 'true').lower() == 'true'
    app.config['AUTO_SEED_ON_EMPTY'] = os.getenv('AUTO_SEED_ON_EMPTY', 'true').lower() == 'true'
    app.config['USE_SEED_BOOT'] = os.getenv('USE_SEED_BOOT', 'true').lower() == 'true'  # prefer seed_boot by default

    # Init extensions
    init_db(app)
    login_manager.init_app(app)
    Migrate(app, db)

    # ✅ API-friendly auth behavior:
    # - For /api/* return JSON 401 (no HTML redirect)
    # - For legacy UI keep redirect to login
    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith("/api/"):
            return jsonify({
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Login required"
                },
                "trace_id": str(uuid.uuid4())
            }), 401
        return redirect(url_for("auth.login"))

    # Delay importing routes to avoid early context errors
    with app.test_request_context('/'):
        from app.routes import register_routes  # type: ignore
        register_routes(app)

    # ---------------- API v1 (JSON) ----------------
    # Registered after legacy routes to avoid circular-import surprises.
    # Safe to keep in place while API module is being added incrementally.
    try:
        from app.api.v1 import api_v1_bp  # type: ignore
        app.register_blueprint(api_v1_bp, url_prefix="/api/v1")
    except Exception as e:
        app.logger.warning(f"API v1 blueprint not registered yet: {e}")

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ---------------------- Robust seeding helpers ----------------------
    def _run_seed() -> int:
        """
        Try seed_boot.ensure_seed() first (date/status aware). If not available,
        try demo_seed.seed_orders(). If nothing is available, return 0 safely.
        """
        # prefer seed_boot if flag is true
        prefer_boot = app.config.get('USE_SEED_BOOT', True)

        def _try_seed_boot():
            try:
                from .seed_boot import ensure_seed  # relative import
                n = ensure_seed() or 0
                return int(n)
            except Exception as e:
                app.logger.warning(f"seed_boot ensure_seed skipped: {e}")
                return None

        def _try_demo_seed():
            try:
                from .demo_seed import seed_orders  # relative import
                _, n = seed_orders()
                return int(n or 0)
            except Exception as e:
                app.logger.warning(f"demo_seed skipped: {e}")
                return None

        order = (_try_seed_boot, _try_demo_seed) if prefer_boot else (_try_demo_seed, _try_seed_boot)
        for fn in order:
            n = fn()
            if n is not None:
                return n
        return 0

    def _seed_if_empty_once():
        """Seed once per process if table is empty, guarded by flags."""
        if app.config.get('_DEMO_SEEDED'):
            return
        if not (app.config.get("DEMO_MODE") and app.config.get("AUTO_SEED_ON_EMPTY")):
            app.config['_DEMO_SEEDED'] = True
            return
        try:
            if Order.query.count() == 0:
                _run_seed()
        except Exception as e:
            app.logger.warning(f"Auto-seed skipped: {e}")
        finally:
            app.config['_DEMO_SEEDED'] = True

    app.config['_DEMO_SEEDED'] = False

    @app.before_request
    def _auto_seed_hook():
        _seed_if_empty_once()

    # ---------------- Auto-login demo user (never downgrade role) ----------------
    AUTO_LOGIN_PATHS = {"/", "/login", "/auth/login"}

    @app.before_request
    def demo_auto_login():
        if not (app.config.get('DEMO_MODE') and app.config.get('DEMO_AUTO_LOGIN')):
            return

        # ✅ If user explicitly logged out, do NOT auto-login again until manual login.
        if session.get("demo_disable_auto_login"):
            return

        # allow manual login when you append ?manual=1
        if request.args.get("manual") == "1":
            return

        path = request.path.rstrip('/')
        if path not in {p.rstrip('/') for p in AUTO_LOGIN_PATHS}:
            return
        if current_user.is_authenticated:
            return

        # ensure demo user exists
        u = User.query.filter_by(username="demo").first()
        if not u:
            u = User(username="demo", role="admin")  # create as admin
            try:
                setattr(u, "email", "demo@portfolio.app")
            except Exception:
                pass
            u.set_password("demo1234")
            db.session.add(u)
            db.session.commit()
        else:
            # NEVER downgrade: upgrade to admin if needed
            try:
                current_role = (u.role or '').lower()
            except Exception:
                current_role = ''
            if current_role != 'admin':
                u.role = 'admin'
                db.session.commit()

        login_user(u, remember=False)
        return redirect("/dashboard")

    # ---------------- Demo read-only guard (smart allow for read POSTs) ----------------
    SAFE_WRITE_ENDPOINTS = {'auth.login', 'auth.logout', 'auth.register'}
    SAFE_WRITE_PATHS = {'/login', '/logout', '/register'}

    WRITE_PATH_RE = re.compile(
        r"/(order|orders|warehouse|delivered|stockreport|stock|report)"
        r".*(add|create|new|edit|update|delete|remove|save|import|upload|mark|toggle|set|assign|purge|wipe|confirm|finalize)",
        re.IGNORECASE,
    )

    WRITE_ACTIONS = {
        "add", "create", "new", "edit", "update", "delete", "remove", "save", "import", "upload",
        "mark", "toggle", "set", "assign", "purge", "wipe", "confirm", "finalize"
    }

    @app.before_request
    def demo_readonly_guard():
        if not (app.config.get('DEMO_MODE') and app.config.get('DEMO_READONLY')):
            return

        # always allow static
        if request.path.startswith('/static'):
            return

        ep = (request.endpoint or '')
        path = (request.path or '')

        # allow auth endpoints and manual reset route if you have one
        if ep in SAFE_WRITE_ENDPOINTS or path in SAFE_WRITE_PATHS or path.startswith('/_admin/reset_demo'):
            return

        # smart allow for API reads that use POST (common in this app)
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            # If it's a JSON API under /api, inspect 'action' before blocking
            if path.startswith('/api/'):
                data = request.get_json(silent=True) or {}
                action = str(data.get('action', '')).lower().strip()
                if action and any(a in action for a in WRITE_ACTIONS):
                    abort(403, description='Demo is read-only. Changes are disabled.')
                # no write action -> allow
                return

            # Non-API: only block if URL looks like a write
            if WRITE_PATH_RE.search(path):
                abort(403, description='Demo is read-only. Changes are disabled.')
            # else allow
            return

    # Expose demo flags to Jinja
    @app.context_processor
    def inject_demo_flag():
        return {
            'DEMO_MODE': app.config.get('DEMO_MODE', False),
            'DEMO_AUTO_LOGIN': app.config.get('DEMO_AUTO_LOGIN', False),
        }

    # ---------------- Template filters (kept) ----------------
    @app.template_filter('format_date')
    def format_date(value):
        try:
            if isinstance(value, str):
                for fmt in ("%Y-%m-%d", "%d.%m.%y", "%d.%m.%Y"):
                    try:
                        value = datetime.strptime(value, fmt)
                        break
                    except ValueError:
                        continue
            if isinstance(value, datetime):
                return value.strftime("%d.%m.%y")
        except Exception:
            pass
        return value

    app.jinja_env.globals['getattr'] = getattr

    @app.template_filter('getattr')
    def jinja_getattr(obj, name):
        return getattr(obj, name, None)

    @app.template_filter('lookup')
    def jinja_lookup(obj, key):
        return obj.get(key) if isinstance(obj, dict) else getattr(obj, key, None)

    # ---------------- HTTP maintenance endpoints (no blueprint wiring) ----------------
    @app.get("/_admin/seed_if_empty")
    def http_seed_if_empty():
        token = request.args.get("token", "")
        if token != app.config.get("DEMO_RESET_TOKEN", "change-me"):
            abort(403, description="Forbidden: bad token")
        count = Order.query.count()
        if count > 0:
            return jsonify({"status": "skipped", "reason": "orders already present", "count": count})
        n = _run_seed()
        return jsonify({"status": "seeded", "count": n})

    @app.get("/_admin/reset_demo")
    def http_reset_demo():
        token = request.args.get("token", "")
        if token != app.config.get("DEMO_RESET_TOKEN", "change-me"):
            abort(403, description="Forbidden: bad token")
        deleted = Order.query.delete()
        db.session.commit()
        n = _run_seed()
        return jsonify({"status": "reset_ok", "deleted": int(deleted), "seeded": n})

    # ---------------- CLI: demo seed/reset/clear ----------------
    @app.cli.command('demo-seed')
    def demo_seed():
        n = _run_seed()
        print(f"Seeded {n} demo orders. Login: demo / demo1234")

    @app.cli.command('demo-reset')
    def demo_reset():
        Order.query.delete()
        db.session.commit()
        n = _run_seed()
        print(f"Demo reset complete. Seeded {n}. Login: demo / demo1234")

    @app.cli.command('demo-clear')
    def demo_clear():
        cleared = Order.query.delete()
        db.session.commit()
        print(f"✅ Demo cleared. Rows deleted: {cleared}")

    return app
