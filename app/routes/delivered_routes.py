from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, DeliveredGoods, WarehouseStock, Order, StockReportEntry
from datetime import datetime
from app.roles import can_edit, can_view_all
from app.utils.logging import log_activity
from sqlalchemy import or_, func, extract
from app.roles import can_view_all

delivered_bp = Blueprint('delivered', __name__)

@delivered_bp.route('/delivered')
@login_required
def delivered():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Filters
    transport = request.args.get('transport')
    month = request.args.get('month')
    year = request.args.get('year')
    search = request.args.get('search', '')
    sort_key = request.args.get('sort', 'delivery_date')
    sort_dir = request.args.get('direction', 'desc')

    # Base query
    if can_view_all(current_user.role):
        query = DeliveredGoods.query
    else:
        query = DeliveredGoods.query.filter_by(user_id=current_user.id)

    # Apply filters
    if transport:
        query = query.filter_by(transport=transport)
    if month:
        query = query.filter(extract('month', DeliveredGoods.delivery_date) == int(month))
    if year:
        query = query.filter(extract('year', DeliveredGoods.delivery_date) == int(year))
    if search:
        like_term = f"%{search.lower()}%"
        query = query.filter(or_(
            func.lower(DeliveredGoods.order_number).like(like_term),
            func.lower(DeliveredGoods.product_name).like(like_term),
            func.lower(DeliveredGoods.notes).like(like_term)
        ))

    # Sorting logic
    sort_column = getattr(DeliveredGoods, sort_key, DeliveredGoods.delivery_date)
    if sort_dir == 'asc':
        sort_order = sort_column.asc().nullslast()
    else:
        sort_order = sort_column.desc().nullsfirst()
    query = query.order_by(sort_order)


    pagination = query.paginate(page=page, per_page=per_page)

    # Reported Orders
    reported_order_numbers = set()
    for entry in StockReportEntry.query.all():
        related = WarehouseStock.query.get(entry.related_order_id) or DeliveredGoods.query.get(entry.related_order_id)
        if related:
            reported_order_numbers.add(related.order_number)

    return render_template(
        'delivered.html',
        delivered_items=pagination.items,
        pagination=pagination,
        per_page=per_page,
        reported_order_numbers=reported_order_numbers,
        sort_key=sort_key,
        sort_dir=sort_dir
    )


@delivered_bp.route('/restore_from_delivered', methods=['POST'])
@login_required
def restore_to_dashboard():
    item_id = request.args.get('item_id', type=int)
    item = DeliveredGoods.query.get_or_404(item_id)

    # Role-based access checks
    if not can_edit(current_user.role):
        return 'Forbidden', 403

    if not can_view_all(current_user.role):
        if not item.user_id or item.user_id != current_user.id:
            return 'Unauthorized', 403

    # Normalize transport
    transport_value = (item.transport or "").strip()
    if not transport_value:
        transport_value = "Not specified"

    try:
        new_order = Order(
            user_id=item.user_id or current_user.id,
            order_date=datetime.now().strftime('%d.%m.%y'),
            order_number=item.order_number,
            product_name=item.product_name,
            buyer="Restored",
            responsible="Restored",
            quantity=item.quantity,
            required_delivery="",
            terms_of_delivery="Restored",
            payment_date="",
            etd=datetime.now().strftime('%Y-%m-%d'),
            eta=datetime.now().strftime('%Y-%m-%d'),
            ata=datetime.now().strftime('%Y-%m-%d'),
            transit_status="in process",
            transport=transport_value
        )

        db.session.add(new_order)
        db.session.delete(item)
        db.session.commit()

        log_activity("Restore from Delivered", f"Order #{item.order_number}")
        return '', 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Restore error: {str(e)}")
        return 'Internal Server Error', 500



@delivered_bp.route('/delivered/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_delivered(item_id):
    item = DeliveredGoods.query.get_or_404(item_id)

    if not can_edit(current_user.role):
        flash("Access denied.", "danger")
        return redirect(url_for('delivered.delivered'))

    if request.method == 'POST':
        item.order_number = request.form.get('order_number')
        item.product_name = request.form.get('product_name')
        item.quantity = request.form.get('quantity')
        item.delivery_date = request.form.get('delivery_date')
        item.transport = request.form.get('transport')
        item.notes = request.form.get('notes')
        db.session.commit()
        log_activity("Edit Delivered Item", f"#{item.order_number}")
        flash("Delivered item updated successfully.", "success")
        return redirect(url_for('delivered.delivered'))

    return render_template('edit_delivered.html', item=item)
