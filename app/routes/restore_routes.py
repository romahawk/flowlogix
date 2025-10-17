
from flask import Blueprint, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Order, WarehouseStock, DeliveredGoods
from datetime import datetime
from app.utils.logging import log_activity


restore_bp = Blueprint('restore', __name__)

@restore_bp.route('/restore_to_dashboard', methods=['POST'])
@login_required
def restore_to_dashboard():
    item_id = request.args.get("item_id")
    item = WarehouseStock.query.get_or_404(item_id)

    if item.user_id != current_user.id:
        flash("Unauthorized access", "danger")
        return redirect(url_for("warehouse.warehouse"))

    today = datetime.today().date()
    default_text = "Restored"

    restored_order = Order(
        user_id=current_user.id,
        order_date=item.ata or today,
        order_number=item.order_number or f"Restored-{item.id}",
        product_name=item.product_name or default_text,
        buyer=item.client or default_text,
        responsible=default_text,
        quantity=item.quantity or 0.01,
        required_delivery=item.ata or today,
        terms_of_delivery=default_text,
        payment_date=item.ata or today,
        etd=item.ata or today,
        eta=item.ata or today,
        ata=item.ata or today,
        transit_status="in process",
        transport=item.transport or "unknown",
        pod_filename=None
    )

    db.session.add(restored_order)
    db.session.delete(item)
    db.session.commit()
    log_activity("Restore from Warehouse", f"#{item.order_number} → Dashboard")
    flash("Order restored to dashboard.", "success")
    return redirect(url_for("dashboard.dashboard"))



@restore_bp.route('/restore_from_delivered', methods=['POST'])
@login_required
def restore_from_delivered():
    item_id = request.args.get("item_id")
    item = DeliveredGoods.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash("Unauthorized access", "danger")
        return redirect(url_for("delivered.delivered"))

    restored_order = Order(
        user_id=current_user.id,
        order_date=datetime.now().strftime('%d.%m.%y'),
        order_number=item.order_number,
        product_name=item.product_name,
        buyer="Restored",
        responsible="Restored",
        quantity=item.quantity,
        required_delivery="",
        terms_of_delivery="Restored",
        payment_date="",
        etd="",
        eta="",
        # ata=item.ata,
        transit_status="in process",
        transport=item.transport,
    )

    db.session.add(restored_order)
    db.session.delete(item)
    db.session.commit()
    log_activity("Restore from Warehouse", f"#{item.order_number} → Dashboard")
    flash("Order restored to dashboard.", "success")
    return redirect(url_for("dashboard.dashboard"))
