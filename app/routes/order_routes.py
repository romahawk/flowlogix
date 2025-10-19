from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import db, Order, DeliveredGoods, ArchivedOrder
from datetime import datetime
from app.roles import can_view_all, can_edit
from app.utils.products import add_product_if_new
from app.utils.logging import log_activity
from sqlalchemy.exc import SQLAlchemyError
import os
import re

order_bp = Blueprint('order', __name__)

PRODUCTS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'products.txt'))

def load_products():
    try:
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            return sorted(set(line.strip() for line in f if line.strip()))
    except FileNotFoundError:
        return []

# ----------------------------
# Helpers: input normalization
# ----------------------------
def _clean_str(s: str) -> str:
    """Normalize 'None', '—', '--' => empty string; strip whitespace."""
    if not s:
        return ""
    s = s.strip()
    if s.lower() in {"none", "—", "--"}:
        return ""
    return s

def _to_ddmm_yy(s: str) -> str:
    """
    Convert a date string into 'dd.MM.yy'.
    Accepts: 'YYYY-MM-DD', 'dd.MM.yy', 'dd.MM.yyyy'.
    Returns '' for empty/normalized empties.
    If unparsable, returns the original (lets non-date fields pass).
    """
    s = _clean_str(s)
    if not s:
        return ""

    # ISO 'YYYY-MM-DD'
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        y, m, d = s.split("-")
        return f"{d}.{m}.{y[-2:]}"

    # 'dd.MM.yyyy'
    if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", s):
        d, m, y = s.split(".")
        return f"{d}.{m}.{y[-2:]}"

    # Already 'dd.MM.yy'
    if re.fullmatch(r"\d{2}\.\d{2}\.\d{2}", s):
        return s

    # Try generic parse
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d.%m.%y"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%d.%m.%y")
        except ValueError:
            pass

    # Not a date? return as-is
    return s

def _to_dt(s: str):
    """Return datetime from any of the accepted inputs; None if empty."""
    norm = _to_ddmm_yy(s)
    if not norm:
        return None
    return datetime.strptime(norm, "%d.%m.%y")

# ----------------------------
# Add Order
# ----------------------------
@order_bp.route('/add_order', methods=['POST'])
@login_required
def add_order():
    try:
        data = request.form

        # Normalize numeric
        quantity_raw = _clean_str(data.get('quantity'))
        quantity = float(quantity_raw) if quantity_raw else 0.0
        if quantity <= 0:
            return jsonify({'success': False, 'message': 'Quantity must be a positive number.'}), 400

        # Normalize dates to dd.MM.yy strings
        order_date_s       = _to_ddmm_yy(data.get('order_date'))
        payment_date_s     = _to_ddmm_yy(data.get('payment_date'))
        required_delivery_s= _to_ddmm_yy(data.get('required_delivery'))
        etd_s              = _to_ddmm_yy(data.get('etd'))
        eta_s              = _to_ddmm_yy(data.get('eta'))
        ata_s              = _to_ddmm_yy(data.get('ata'))

        # Parse to datetime for comparisons where available
        order_date_dt = _to_dt(order_date_s)
        etd_dt        = _to_dt(etd_s)
        eta_dt        = _to_dt(eta_s)

        if etd_dt and eta_dt and etd_dt > eta_dt:
            return jsonify({'success': False, 'message': 'ETD cannot be later than ETA.'}), 400
        if etd_dt and order_date_dt and order_date_dt > etd_dt:
            return jsonify({'success': False, 'message': 'Order Date cannot be later than ETD.'}), 400

        order_number = _clean_str(data.get('order_number'))
        if not order_number:
            return jsonify({'success': False, 'message': 'Order must have an Order Number.'}), 400

        product_name = _clean_str(data.get('product_name'))
        add_product_if_new(product_name)

        new_order = Order(
            user_id=current_user.id,
            order_date=order_date_s,
            order_number=order_number,
            product_name=product_name,
            buyer=_clean_str(data.get('buyer')),
            responsible=_clean_str(data.get('responsible')),
            quantity=quantity,
            required_delivery=required_delivery_s,
            terms_of_delivery=_clean_str(data.get('terms_of_delivery')),
            payment_date=payment_date_s,
            etd=etd_s,
            eta=eta_s,
            ata=ata_s,
            transit_status=_clean_str(data.get('transit_status')),
            transport=_clean_str(data.get('transport'))
        )

        db.session.add(new_order)
        db.session.commit()
        log_activity("Add Order", f"#{new_order.order_number} – {product_name}")
        return jsonify({'success': True, 'message': 'Order added successfully!'}), 200

    except ValueError:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Invalid input format. Check all fields.'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error adding order: {str(e)}'}), 500

# ----------------------------
# Edit Order (GET/POST)
# ----------------------------
@order_bp.route('/edit_order/<int:order_id>', methods=["GET", "POST"])
@login_required
def edit_order(order_id):
    order = Order.query.get_or_404(order_id)

    # Permissions
    if not can_edit(current_user.role) and order.user_id != current_user.id:
        if request.method == "POST":
            return jsonify({'success': False, 'message': 'You do not have permission to edit this order.'}), 403
        else:
            flash("You do not have permission to edit this order.", "danger")
            return redirect(url_for('dashboard.dashboard'))

    if request.method == "GET":
        return render_template("edit_order.html", order=order)

    # POST
    try:
        data = request.form

        # Numeric
        qty_raw = _clean_str(data.get('quantity'))
        quantity = float(qty_raw) if qty_raw else 0.0
        if quantity <= 0:
            return jsonify({'success': False, 'message': 'Quantity must be a positive number.'}), 400

        # Dates (normalize then compare)
        order_date_s       = _to_ddmm_yy(data.get('order_date'))
        payment_date_s     = _to_ddmm_yy(data.get('payment_date'))
        required_delivery_s= _to_ddmm_yy(data.get('required_delivery'))
        etd_s              = _to_ddmm_yy(data.get('etd'))
        eta_s              = _to_ddmm_yy(data.get('eta'))
        ata_s              = _to_ddmm_yy(data.get('ata'))

        order_date_dt = _to_dt(order_date_s)
        etd_dt        = _to_dt(etd_s)
        eta_dt        = _to_dt(eta_s)

        if etd_dt and eta_dt and etd_dt > eta_dt:
            return jsonify({'success': False, 'message': 'ETD cannot be later than ETA.'}), 400
        if etd_dt and order_date_dt and order_date_dt > etd_dt:
            return jsonify({'success': False, 'message': 'Order Date cannot be later than ETD.'}), 400

        # Update fields
        product_name = _clean_str(data.get('product_name'))
        add_product_if_new(product_name)
        order.product_name = product_name

        order.order_date       = order_date_s
        order.order_number     = _clean_str(data.get('order_number'))
        order.buyer            = _clean_str(data.get('buyer'))
        order.responsible      = _clean_str(data.get('responsible'))
        order.quantity         = quantity
        order.required_delivery= required_delivery_s
        order.terms_of_delivery= _clean_str(data.get('terms_of_delivery'))
        order.payment_date     = payment_date_s
        order.etd              = etd_s
        order.eta              = eta_s
        order.ata              = ata_s
        order.transit_status   = _clean_str(data.get('transit_status'))
        order.transport        = _clean_str(data.get('transport'))

        db.session.commit()
        log_activity("Edit Order", f"#{order.order_number} – updated fields")

        # If the edit page submits via normal form post, redirect; if via AJAX, the redirect is ignored by fetch.
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({'success': True})
        flash('Order updated successfully.', 'success')
        return redirect(url_for('dashboard.dashboard'))

    except ValueError:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Invalid input format. Check your fields.'}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Unexpected error: {str(e)}'}), 500

# ----------------------------
# Delete Order
# ----------------------------
@order_bp.route('/delete_order/<int:order_id>')
@login_required
def delete_order(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        if order.user_id != current_user.id and not can_edit(current_user.role):
            return jsonify({'success': False, 'message': 'Permission denied.'}), 403

        db.session.delete(order)
        db.session.commit()
        log_activity("Delete Order", f"#{order.order_number}")
        return jsonify({'success': True, 'message': 'Order deleted successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

# ----------------------------
# API: Orders JSON (used by dashboard)
# ----------------------------
@order_bp.route('/api/orders')
@login_required
def get_orders():
    if can_view_all(current_user.role):
        orders = Order.query.order_by(Order.order_date.asc()).all()
    else:
        orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.asc()).all()

    def get_delivery_year(order):
        try:
            date_fields = [order.required_delivery, order.eta, order.ata]
            date_objs = [
                datetime.strptime(d, '%d.%m.%y')
                for d in date_fields if d and d.strip()
            ]
            if date_objs:
                return max(date_objs).year
        except Exception:
            pass
        try:
            return datetime.strptime(order.order_date, '%d.%m.%y').year
        except Exception:
            return None

    orders_data = [{
        'id': order.id,
        'order_date': order.order_date,
        'order_number': order.order_number,
        'product_name': order.product_name,
        'buyer': order.buyer,
        'responsible': order.responsible,
        'quantity': order.quantity,
        'required_delivery': order.required_delivery,
        'terms_of_delivery': order.terms_of_delivery,
        'payment_date': order.payment_date,
        'etd': order.etd,
        'eta': order.eta,
        'ata': order.ata,
        'transit_status': order.transit_status,
        'transport': order.transport,
        'delivery_year': get_delivery_year(order)
    } for order in orders]

    return jsonify(orders_data)

# ----------------------------
# Direct Deliver (dashboard)
# ----------------------------
@order_bp.route('/deliver_direct/<int:order_id>', methods=['POST'])
@login_required
def deliver_direct(order_id):
    order = Order.query.get_or_404(order_id)

    # Access control
    if not can_edit(current_user.role) and order.user_id != current_user.id:
        flash("You don't have permission to deliver this order.", "danger")
        return redirect(url_for('dashboard.dashboard'))

    if not order.order_number:
        flash("Order must have an order number to be delivered.", "warning")
        return redirect(url_for('dashboard.dashboard'))

    delivered_item = DeliveredGoods(
        user_id=order.user_id,
        order_number=order.order_number,
        product_name=order.product_name,
        quantity=order.quantity,
        delivery_source="Direct from Transit",
        delivery_date=datetime.now().strftime('%Y-%m-%d'),
        notes="Delivered directly from dashboard",
        transport=order.transport
    )

    archived_order = ArchivedOrder(
        original_order_id=order.id,
        user_id=order.user_id,
        order_date=order.order_date,
        order_number=order.order_number,
        product_name=order.product_name,
        buyer=order.buyer,
        responsible=order.responsible,
        quantity=order.quantity,
        required_delivery=order.required_delivery,
        terms_of_delivery=order.terms_of_delivery,
        payment_date=order.payment_date,
        etd=order.etd,
        eta=order.eta,
        ata=order.ata,
        transit_status=order.transit_status,
        transport=order.transport,
        source='dashboard'
    )

    try:
        db.session.add(archived_order)
        db.session.add(delivered_item)
        db.session.delete(order)
        db.session.commit()
        flash("Order delivered and archived successfully!", "success")
        log_activity("Deliver Order (Direct)", f"#{order.order_number} → Delivered from Dashboard")
    except Exception as e:
        db.session.rollback()
        flash(f"Error delivering order: {e}", "danger")

    return redirect(url_for('dashboard.dashboard'))
