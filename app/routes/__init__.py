
from flask import request
from flask_login import current_user

def inject_globals():
    return dict(current_user=current_user, current_path=request.path)

def register_routes(app):
    from .auth_routes import auth_bp
    from .dashboard_routes import dashboard_bp
    from .order_routes import order_bp
    from .warehouse_routes import warehouse_bp
    from .delivered_routes import delivered_bp
    from .restore_routes import restore_bp
    from .upload_routes import upload_bp
    from .stats_routes import stats_bp
    from .onboarding_routes import onboarding_bp
    from .analytics_routes import analytics_bp
    from .products_routes import products_bp
    from .admin_routes import admin_bp
    from .activity_routes import activity_bp
    import time


    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(warehouse_bp)
    app.register_blueprint(delivered_bp)
    app.register_blueprint(restore_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(onboarding_bp)
    app.register_blueprint(analytics_bp)
    app.context_processor(inject_globals)
    app.config['VERSION'] = str(int(time.time()))
    app.register_blueprint(products_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(activity_bp)


