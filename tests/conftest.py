import os
import pytest
from app import create_app
from app.database import db as _db


@pytest.fixture(scope="session")
def app():
    os.environ.setdefault("SECRET_KEY", "test-secret")
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    os.environ["DEMO_MODE"] = "false"
    os.environ["AUTO_SEED_ON_EMPTY"] = "false"
    os.environ["USE_SEED_BOOT"] = "false"

    application = create_app()
    application.config["TESTING"] = True
    application.config["WTF_CSRF_ENABLED"] = False

    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
