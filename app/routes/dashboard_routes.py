from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.models import Order, WarehouseStock, DeliveredGoods
from app.decorators import role_required
from app.database import db
from datetime import datetime, date
from app.roles import can_view_all
from app.utils.logging import log_activity
import os


dashboard_bp = Blueprint('dashboard', __name__)

# --- date helpers -----------------------------------------------------------

_DATE_FORMATS = ("%Y-%m-%d", "%d.%m.%Y", "%d.%m.%y", "%d/%m/%Y")

def parse_date(value):
    """Return a date or None from mixed string/date inputs."""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        s = value.strip()
        for fmt in _DATE_FORMATS:
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                pass
    return None

def fmt(d):
    return d.strftime("%d.%m.%y") if d else ""


@dashboard_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('auth.login'))


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    from app.roles import can_view_all
    from app.models import Order, WarehouseStock, DeliveredGoods

    if can_view_all(current_user.role):
        in_transit_count = Order.query.count()
        warehouse_count = WarehouseStock.query.filter_by(is_archived=False).count()
        delivered_count = DeliveredGoods.query.count()
    else:
        in_transit_count = Order.query.filter_by(user_id=current_user.id).count()
        warehouse_count = WarehouseStock.query.filter_by(user_id=current_user.id, is_archived=False).count()
        delivered_count = DeliveredGoods.query.filter_by(user_id=current_user.id).count()

    return render_template(
        'dashboard.html',
        in_transit_count=in_transit_count,
        warehouse_count=warehouse_count,
        delivered_count=delivered_count,
        now=datetime.now()
    )


@dashboard_bp.route('/delete_order/<int:order_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    if not can_view_all(current_user.role) and order.user_id != current_user.id:
        flash("Unauthorized delete attempt.", "error")
        return redirect(url_for('dashboard.dashboard'))

    db.session.delete(order)
    db.session.commit()
    log_activity("Delete Order (Admin)", f"#{order.order_number}")
    flash('Order deleted successfully.', 'success')
    return redirect(url_for('dashboard.dashboard'))


@dashboard_bp.route('/add_order', methods=['POST'])
@login_required
def add_order():
    from app.models import Order
    from app.utils.products import add_product_if_new

    form = request.form
    new_order = Order(
        order_date=form.get("order_date"),
        order_number=form.get("order_number"),
        product_name=form.get("product_name"),
        buyer=form.get("buyer"),
        responsible=form.get("responsible"),
        quantity=form.get("quantity"),
        required_delivery=form.get("required_delivery"),
        terms_of_delivery=form.get("terms_of_delivery"),
        payment_date=form.get("payment_date"),
        etd=form.get("etd"),
        eta=form.get("eta"),
        ata=form.get("ata"),
        transit_status=form.get("transit_status"),
        transport=form.get("transport"),
        user_id=current_user.id
    )

    # ✅ Add the new product to the list if not already present
    add_product_if_new(new_order.product_name)

    db.session.add(new_order)
    db.session.commit()
    log_activity("Add Order", f"#{new_order.order_number}")

    return jsonify({"success": True})


# ===========================
# 🔹 Data APIs for dashboard
# ===========================

@dashboard_bp.get('/api/kpi')
@login_required
def api_kpi():
    """Return KPI counts + month-over-month dynamics for the 4 dashboard cards."""
    from datetime import date, timedelta

    today = date.today()
    first_this = today.replace(day=1)
    first_last = (first_this - timedelta(days=1)).replace(day=1)
    last_last   = first_this - timedelta(days=1)

    def pd(s):
        """Parse a stored date string to date or None."""
        if not s:
            return None
        for fmt in ("%d.%m.%y", "%d.%m.%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                pass
        return None

    def pct(curr, prev):
        if prev == 0:
            return None
        return round((curr - prev) / prev * 100)

    def in_range(d, lo, hi):
        return d is not None and lo <= d <= hi

    q  = Order.query
    ws = WarehouseStock.query
    dg = DeliveredGoods.query
    if not can_view_all(current_user.role):
        q  = q.filter_by(user_id=current_user.id)
        ws = ws.filter_by(user_id=current_user.id)
        dg = dg.filter_by(user_id=current_user.id)

    orders    = q.all()
    warehouse = ws.filter_by(is_archived=False).all()
    delivered = dg.all()

    # ── In Transit ──────────────────────────────────────────────────────────
    transit_total = len(orders)
    transit_this  = sum(1 for o in orders if in_range(pd(o.order_date), first_this, today))
    transit_last  = sum(1 for o in orders if in_range(pd(o.order_date), first_last, last_last))

    # ── Warehouse ────────────────────────────────────────────────────────────
    wh_total = len(warehouse)
    wh_this  = sum(1 for w in warehouse if in_range(pd(w.ata), first_this, today))
    wh_last  = sum(1 for w in warehouse if in_range(pd(w.ata), first_last, last_last))

    # ── Delivered ────────────────────────────────────────────────────────────
    dg_total = len(delivered)
    dg_this  = sum(1 for d in delivered if in_range(pd(d.delivery_date), first_this, today))
    dg_last  = sum(1 for d in delivered if in_range(pd(d.delivery_date), first_last, last_last))

    # ── Delayed (ETA passed, no ATA yet) ─────────────────────────────────────
    def is_delayed(o):
        eta = pd(o.eta)
        return eta is not None and eta < today and not o.ata

    delayed_total = sum(1 for o in orders if is_delayed(o))
    # "became overdue this month" = eta within this month range and still no ata
    delayed_this  = sum(1 for o in orders
                        if pd(o.eta) is not None
                        and in_range(pd(o.eta), first_this, today)
                        and not o.ata)
    delayed_last  = sum(1 for o in orders
                        if pd(o.eta) is not None
                        and in_range(pd(o.eta), first_last, last_last)
                        and not o.ata)

    return jsonify({
        "in_transit": {
            "count": transit_total,
            "delta_pct": pct(transit_this, transit_last),
            "delta_label": "vs last month",
            "positive_is_good": True,
        },
        "warehouse": {
            "count": wh_total,
            "delta_pct": pct(wh_this, wh_last),
            "delta_label": "vs last month",
            "positive_is_good": True,
        },
        "delivered": {
            "count": dg_total,
            "delta_pct": pct(dg_this, dg_last),
            "delta_label": "vs last month",
            "positive_is_good": True,
        },
        "delayed": {
            "count": delayed_total,
            "delta_pct": pct(delayed_this, delayed_last),
            "delta_label": "vs last month",
            "positive_is_good": False,
        },
    })


@dashboard_bp.get('/api/years')
@login_required
def api_years():
    """Return list of years that contain orders for the current viewer."""
    q = Order.query
    if not can_view_all(current_user.role):
        q = q.filter_by(user_id=current_user.id)

    years = set()
    for o in q:
        for fld in ("order_date", "etd", "eta", "ata"):
            d = parse_date(getattr(o, fld))
            if d:
                years.add(d.year)

    return jsonify({"years": sorted(years, reverse=True)})


@dashboard_bp.get('/api/orders')
@login_required
def api_orders():
    """Return orders (optionally filtered by year) in a shape expected by dashboard.js."""
    year = request.args.get("year", type=int)

    q = Order.query
    if not can_view_all(current_user.role):
        q = q.filter_by(user_id=current_user.id)

    rows = []
    for o in q:
        od  = parse_date(getattr(o, "order_date"))
        etd = parse_date(getattr(o, "etd"))
        eta = parse_date(getattr(o, "eta"))
        ata = parse_date(getattr(o, "ata"))

        # If a year is requested, include if ANY relevant date matches.
        if year is not None:
            in_year = any(d and d.year == year for d in (od, etd, eta, ata))
            if not in_year:
                continue

        rows.append({
            "id": o.id,
            "order_date": fmt(od),
            "order_number": o.order_number,
            "product_name": o.product_name,
            "buyer": o.buyer,
            "responsible": o.responsible,
            "quantity": o.quantity,
            "required_delivery": o.required_delivery or "",
            "terms_of_delivery": o.terms_of_delivery or "",
            "payment_date": fmt(parse_date(getattr(o, "payment_date"))),
            "etd": fmt(etd),
            "eta": fmt(eta),
            "ata": fmt(ata),
            "transit_status": o.transit_status or "",
            "transport": o.transport or "",
        })

    # Sort newest first by order_date (fallback to ETD), robust to blanks.
    def sort_key(r):
        d = parse_date(r["order_date"]) or parse_date(r["etd"])
        return d or date.min

    rows.sort(key=sort_key, reverse=True)
    return jsonify({"orders": rows})
