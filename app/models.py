from .database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(50), default='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def is_active(self): return True
    def get_id(self): return str(self.id)
    def is_authenticated(self): return True
    def is_anonymous(self): return False


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_date = db.Column(db.String(10), nullable=False)
    order_number = db.Column(db.String(50), nullable=True)
    product_name = db.Column(db.String(100), nullable=False)
    buyer = db.Column(db.String(100), nullable=False)
    responsible = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.String(50), nullable=False)
    required_delivery = db.Column(db.String(10), nullable=True)
    terms_of_delivery = db.Column(db.String(100), nullable=True)
    payment_date = db.Column(db.String(10))
    etd = db.Column(db.String(10), nullable=True)
    eta = db.Column(db.String(10), nullable=True)
    ata = db.Column(db.String(10))
    transit_status = db.Column(db.String(20), nullable=False)
    transport = db.Column(db.String(20), nullable=False)
    pod_filename = db.Column(db.String(120))


class WarehouseStock(db.Model):
    __tablename__ = 'warehouse_stock'  # ✅ Ensure FK consistency
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_number = db.Column(db.String(50), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.String(50), nullable=False)
    ata = db.Column(db.String(10), nullable=True)
    transit_status = db.Column(db.String(20), default='In Stock', nullable=False)
    notes = db.Column(db.String(120))
    transport = db.Column(db.String(20))
    is_manual = db.Column(db.Boolean, default=False)
    pod_filename = db.Column(db.String(120))
    warehouse_address = db.Column(db.String(255))
    client = db.Column(db.String(255))
    pos_no = db.Column(db.String(50))
    customer_ref = db.Column(db.String(50))
    is_archived = db.Column(db.Boolean, default=False)


class DeliveredGoods(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_number = db.Column(db.String(50), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.String(50), nullable=False)
    delivery_source = db.Column(db.String(50), nullable=False)
    delivery_date = db.Column(db.String(10), nullable=False)
    transport = db.Column(db.String(20))
    notes = db.Column(db.String(120))
    pod_filename = db.Column(db.String(120))
    warehouse_address = db.Column(db.String(255))
    client = db.Column(db.String(255))
    pos_no = db.Column(db.String(50))
    customer_ref = db.Column(db.String(50))

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    target_id = db.Column(db.Integer, nullable=False)
    target_type = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class ArchivedOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_order_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    order_date = db.Column(db.String(20))
    order_number = db.Column(db.String(100))
    product_name = db.Column(db.String(255))
    buyer = db.Column(db.String(100))
    responsible = db.Column(db.String(100))
    quantity = db.Column(db.Float)
    required_delivery = db.Column(db.String(100))
    terms_of_delivery = db.Column(db.String(100))
    payment_date = db.Column(db.String(20))
    etd = db.Column(db.String(20))
    eta = db.Column(db.String(20))
    ata = db.Column(db.String(20))
    transit_status = db.Column(db.String(100))
    transport = db.Column(db.String(100))
    source = db.Column(db.String(100))
    notes = db.Column(db.Text)
    archived_at = db.Column(db.DateTime, default=datetime.utcnow)


class StockReportEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stage = db.Column(db.String(20))  # "Arrived", "Stocked", "Delivered"
    entrance_date = db.Column(db.Date)
    article_batch = db.Column(db.String(50))
    colli = db.Column(db.Integer)
    packing = db.Column(db.String(50))
    pcs = db.Column(db.Integer)
    colli_per_pal = db.Column(db.Integer)
    pcs_total = db.Column(db.Integer)
    pal = db.Column(db.Integer)
    product = db.Column(db.String(100))
    gross_kg = db.Column(db.Float)
    net_kg = db.Column(db.Float)
    sender = db.Column(db.String(100))
    customs_status = db.Column(db.String(10))  # "EU", "T1"
    stockref = db.Column(db.String(50))

    warehouse_address = db.Column(db.String(255))
    client = db.Column(db.String(255))
    pos_no = db.Column(db.String(50))
    customer_ref = db.Column(db.String(50))

    related_order_id = db.Column(db.Integer, db.ForeignKey('warehouse_stock.id', name='fk_stockreport_warehouse'))

    related_order = db.relationship('WarehouseStock', backref='stock_reports')

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(100))
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User')
