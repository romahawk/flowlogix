import os
import re
from datetime import datetime
from flask import Flask, request, abort, redirect, has_request_context
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

    # Init extensions
    init_db(app)
    login_manager.init_app(app)
    Migrate(app, db)

    # --- Register routes normally (NO test_request_context) ---
    from app.routes import register_routes
    register_routes(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ---------- One-time auto-seed on first request ----------
    app.config['_DEMO_SEEDED'] = False

    @app.before_request
    def demo_seed_on_first_request():
        if not has_request_context():
            return
        if app.config.get('_DEMO_SEEDED'):
            return
        if not (app.config.get("DEMO_MODE") and os.getenv("AUTO_SEED_ON_EMPTY", "true").lower() == "true"):
            app.config['_DEMO_SEEDED'] = True
            return
        try:
            if Order.query.count() == 0:
                # If you migrated to seed_boot.ensure_seed(), swap the import here.
                from app.demo_seed import seed_orders
                seed_orders()
        except Exception as e:
            app.logger.warning(f"Auto-seed skipped: {e}")
        finally:
            app.config['_DEMO_SEEDED'] = True

    # ---------------- Auto-login demo user ----------------
    AUTO_LOGIN_PATHS = {"/", "/login", "/auth/login"}

    @app.before_request
    def demo_auto_login():
        if not has_request_context():
            return
        if not (app.config.get('DEMO_MODE') and app.config.get('DEMO_AUTO_LOGIN')):
            return
        if request.args.get("manual") == "1":
            return
        path = request.path.rstrip('/')
        if path not in {p.rstrip('/') for p in AUTO_LOGIN_PATHS} and current_user.is_authenticated:
            return
        if current_user.is_authenticated:
            return

        # ensure demo user exists
        u = User.query.filter_by(username="demo").first()
        if not u:
            u = User(username="demo", role="admin")
            try:
                setattr(u, "email", "demo@portfolio.app")
            except Exception:
                pass
            u.set_password("demo1234")
            db.session.add(u)
            db.session.commit()
        else:
            if (u.role or '').lower() != 'admin':
                u.role = 'admin'
                db.session.commit()

        login_user(u, remember=False)
        if path in {"", "/login", "/auth/login"}:
            return redirect("/dashboard")

    # ---------------- Demo read-only guard ----------------
    SAFE_WRITE_ENDPOINTS = {'auth.login', 'auth.logout', 'auth.register'}
    SAFE_WRITE_PATHS = {'/login', '/logout', '/register'}

    WRITE_PATH_RE = re.compile(
        r"/(order|orders|warehouse|delivered|stockreport|stock|report)"
        r".*(add|create|new|edit|update|delete|remove|save|import|upload|mark|toggle|set|assign|purge|wipe|confirm|finalize)",
        re.IGNORECASE,
    )

    WRITE_ACTIONS = {
        "add","create","new","edit","update","delete","remove","save","import","upload",
        "mark","toggle","set","assign","purge","wipe","confirm","finalize"
    }

    @app.before_request
    def demo_readonly_guard():
        if not has_request_context():
            return
        if not (app.config.get('DEMO_MODE') and app.config.get('DEMO_READONLY')):
            return

        if request.path.startswith('/static'):
            return

        ep = (request.endpoint or '')
        path = (request.path or '')

        if ep in SAFE_WRITE_ENDPOINTS or path in SAFE_WRITE_PATHS or path.startswith('/_admin/reset_demo'):
            return

        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            if path.startswith('/api/'):
                data = request.get_json(silent=True) or {}
                action = str(data.get('action', '')).lower().strip()
                if action and any(a in action for a in WRITE_ACTIONS):
                    abort(403, description='Demo is read-only. Changes are disabled.')
                return

            if WRITE_PATH_RE.search(path):
                abort(403, description='Demo is read-only. Changes are disabled.')
            return

    # Expose demo flags to Jinja
    @app.context_processor
    def inject_demo_flag():
        return {
            'DEMO_MODE': app.config.get('DEMO_MODE', False),
            'DEMO_AUTO_LOGIN': app.config.get('DEMO_AUTO_LOGIN', False),
        }

    # ---------------- Template filters ----------------
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

    # ---------------- CLI ----------------
    @app.cli.command('demo-seed')
    def demo_seed():
        from app.demo_seed import seed_orders
        username, n = seed_orders()
        print(f"Seeded {n} demo orders. Login: {username} / demo1234")

    @app.cli.command('demo-reset')
    def demo_reset():
        from app.demo_seed import seed_orders
        Order.query.delete()
        db.session.commit()
        username, n = seed_orders()
        print(f"Demo reset complete. Seeded {n}. Login: {username} / demo1234")

    @app.cli.command('demo-clear')
    def demo_clear():
        cleared = Order.query.delete()
        db.session.commit()
        print(f"✅ Demo cleared. Rows deleted: {cleared}")

    # ---------------- Admin-less maintenance endpoints (token protected) -------------
    from flask import jsonify

    def _check_token():
        token = request.args.get("token", "")
        expected = app.config.get("DEMO_RESET_TOKEN", "change-me")
        if token != expected:
            abort(403, description="Forbidden: bad token")

    def _run_seed():
        """Choose which seeder to use based on USE_SEED_BOOT env flag."""
        use_seed_boot = str(app.config.get("USE_SEED_BOOT", "false")).lower() == "true"
        if use_seed_boot:
            from app.seed_boot import ensure_seed
            return int(ensure_seed() or 0)
        else:
            from app.demo_seed import seed_orders
            _, n = seed_orders()
            return int(n or 0)

    @app.get("/_admin/seed_if_empty")
    def _seed_if_empty():
        _check_token()
        cnt = Order.query.count()
        if cnt > 0:
            return jsonify({"status": "skipped", "reason": "orders already present", "count": cnt})
        n = _run_seed()
        return jsonify({"status": "seeded", "count": n})

    @app.get("/_admin/reset_demo")
    def _reset_demo():
        _check_token()
        deleted = Order.query.delete()
        db.session.commit()
        n = _run_seed()
        return jsonify({"status": "reset_ok", "deleted": int(deleted), "seeded": n})

    return app
