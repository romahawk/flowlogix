# database.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    with app.app_context():
        try:
            db.create_all()
        except OperationalError as e:
            if "already exists" not in str(e):
                raise