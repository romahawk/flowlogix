from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.models import Order, WarehouseStock, DeliveredGoods
from app.decorators import role_required
from app.database import db
from datetime import datetime
from app.roles import can_view_all
from app.utils.logging import log_activity
import os


dashboard_bp = Blueprint('dashboard', __name__)

# ✅ Re-added inline load_products()

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
        now=datetime.now()  # ✅ Add this line
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
