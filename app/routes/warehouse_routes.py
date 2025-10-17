from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import db, Order, WarehouseStock, DeliveredGoods, StockReportEntry
from app.roles import can_edit, can_view_all
from datetime import datetime, timedelta
from flask import jsonify, make_response
from app.utils.logging import log_activity
from sqlalchemy import or_, func, extract
import os
from weasyprint import HTML
from app.roles import can_view_all

warehouse_bp = Blueprint('warehouse', __name__)

@warehouse_bp.route('/warehouse')
@login_required
def warehouse():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')

    # NEW: sort parameters
    sort_key = request.args.get('sort', 'ata')  # Default to ATA
    sort_dir = request.args.get('direction', 'desc')

    if can_view_all(current_user.role):
        query = WarehouseStock.query.filter_by(is_archived=False)
    else:
        query = WarehouseStock.query.filter_by(is_archived=False, user_id=current_user.id)

    if search:
        like_term = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(WarehouseStock.order_number).like(like_term),
                func.lower(WarehouseStock.product_name).like(like_term),
                func.lower(WarehouseStock.notes).like(like_term)
            )
        )

    # NEW: apply sorting
    sort_column_map = {
        'order_number': WarehouseStock.order_number,
        'product_name': WarehouseStock.product_name,
        'quantity': WarehouseStock.quantity,
        'ata': WarehouseStock.ata,
        'transport': WarehouseStock.transport
    }

    if sort_key in sort_column_map:
        sort_column = sort_column_map[sort_key]
        if sort_dir == 'asc':
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
    else:
        # Fallback if invalid sort_key
        query = query.order_by(WarehouseStock.ata.desc())

    pagination = query.paginate(page=page, per_page=per_page)
    warehouse_items = pagination.items

    reported_ids = [entry.related_order_id for entry in StockReportEntry.query.all() if entry.related_order_id]

    return render_template(
        'warehouse.html',
        warehouse_items=warehouse_items,
        pagination=pagination,
        per_page=per_page,
        reported_ids=reported_ids,
        sort_key=sort_key,
        sort_dir=sort_dir
    )


@warehouse_bp.route('/add_warehouse_manual', methods=['POST'])
@login_required
def add_warehouse_manual():
    if not can_edit(current_user.role):
        flash("Access denied.", "danger")
        return redirect(url_for('warehouse.warehouse'))

    try:
        order_number = request.form['order_number']
        product_name = request.form['product_name']
        quantity = float(request.form['quantity'])
        ata = request.form['ata']
        transport = request.form['transport']
        notes = request.form.get('notes', 'Manual Entry')

        if quantity <= 0:
            flash("Quantity must be greater than 0", "danger")
            return redirect(url_for('warehouse.warehouse'))

        new_item = WarehouseStock(
            user_id=current_user.id,
            order_number=order_number,
            product_name=product_name,
            quantity=quantity,
            ata=ata,
            transport=transport,
            notes=notes,
            is_manual=True
        )
        db.session.add(new_item)
        db.session.commit()
        log_activity("Manual Warehouse Entry", f"#{order_number} – {product_name}")
        flash("Manual order successfully added to warehouse.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding manual order: {e}", "danger")

    return redirect(url_for('warehouse.warehouse'))

@warehouse_bp.route('/stock_order/<int:order_id>', methods=['POST'])
@login_required
def stock_order(order_id):
    if not can_edit(current_user.role):
        flash("Access denied.", "danger")
        return redirect(url_for('dashboard.dashboard'))

    order = Order.query.get_or_404(order_id)
    new_stock = WarehouseStock(
        user_id=order.user_id,
        order_number=order.order_number,
        product_name=order.product_name,
        quantity=order.quantity,
        ata=order.ata,
        transport=order.transport,
        notes="Stocked from order"
    )
    db.session.add(new_stock)
    db.session.delete(order)
    db.session.commit()
    log_activity("Move to Warehouse", f"#{order.order_number} – stocked from Dashboard")
    flash("Order moved to warehouse.", "success")
    return redirect(url_for('dashboard.dashboard'))

@warehouse_bp.route('/deliver_partial/<int:item_id>', methods=['POST'])
@login_required
def deliver_partial(item_id):
    if not can_edit(current_user.role):
        flash("Access denied.", "danger")
        return redirect(url_for('warehouse.warehouse'))

    item = WarehouseStock.query.get_or_404(item_id)

    try:
        qty_to_deliver = float(request.form['quantity'])
        current_qty = float(item.quantity)
    except ValueError:
        flash('Invalid quantity entered.', 'danger')
        return redirect(url_for('warehouse.warehouse'))

    if qty_to_deliver <= 0 or qty_to_deliver > current_qty:
        flash(f"Invalid quantity. Must be between 1 and {current_qty}.", 'danger')
        return redirect(url_for('warehouse.warehouse'))

    new_qty = current_qty - qty_to_deliver
    if new_qty <= 0:
        item.is_archived = True  # ✅ Archive instead of delete
    else:
        item.quantity = new_qty


    # Not mandatory, but good future-proofing
    delivery = DeliveredGoods(
        user_id=item.user_id,
        order_number=item.order_number,
        product_name=item.product_name,
        quantity=qty_to_deliver,
        transport=item.transport,
        delivery_source="From Warehouse",
        notes=item.notes,
        warehouse_address=item.warehouse_address,
        client=item.client,
        pos_no=item.pos_no,
        customer_ref=item.customer_ref,
        delivery_date=datetime.now().strftime('%d.%m.%y')
    )

    db.session.add(delivery)
    db.session.commit()
    log_activity("Partial Delivery", f"#{item.order_number} – {qty_to_deliver} units delivered")
    flash(f'Delivered {qty_to_deliver} from warehouse.', 'success')
    return redirect(url_for('warehouse.warehouse'))


@warehouse_bp.route('/edit_warehouse/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_warehouse(item_id):
    if not can_edit(current_user.role):
        flash("Access denied.", "danger")
        return redirect(url_for('warehouse.warehouse'))

    item = WarehouseStock.query.get_or_404(item_id)

    if request.method == 'POST':
        item.quantity = float(request.form['quantity'])
        item.ata = request.form['ata']
        item.notes = request.form.get("notes")
        db.session.commit()
        log_activity("Edit Warehouse Item", f"#{item.order_number}")
        flash('Warehouse item updated successfully!', 'success')
        return redirect(url_for('warehouse.warehouse'))

    return render_template('edit_warehouse.html', item=item)

@warehouse_bp.route('/delete_warehouse/<int:item_id>', methods=['POST'])
@login_required
def delete_warehouse(item_id):
    if not can_edit(current_user.role):
        flash("Access denied.", "danger")
        return redirect(url_for('warehouse.warehouse'))

    item = WarehouseStock.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    log_activity("Delete Warehouse Item", f"#{item.order_number}")
    flash('Warehouse item deleted successfully.', 'success')
    return redirect(url_for('warehouse.warehouse'))

@warehouse_bp.route('/stockreport/<int:item_id>', methods=['GET', 'POST'])
@login_required
def stockreport_entry_form(item_id):
    if not can_edit(current_user.role):
        flash("Access denied.", "danger")
        return redirect(url_for('warehouse.warehouse'))

    item = WarehouseStock.query.get_or_404(item_id)

    # Load existing products (optional legacy support)
    products_path = os.path.join(os.getcwd(), 'products.txt')
    if os.path.exists(products_path):
        with open(products_path, 'r', encoding='utf-8') as f:
            product_options = sorted({line.strip() for line in f if line.strip()})
    else:
        product_options = []

    if request.method == 'POST':
        try:
            form = request.form
            entrance_str = form.get('entrance_date')
            entrance_date = datetime.strptime(entrance_str, '%Y-%m-%d') if entrance_str else None

            # Product name is inherited directly from WarehouseStock item
            product_name = item.product_name

            entry = StockReportEntry(
                stage=form.get('stage'),
                entrance_date=entrance_date,
                article_batch=form.get('article_batch'),
                colli=int(form.get('colli') or 0),
                packing=form.get('packing', ''),
                pcs=int(form.get('pcs') or 0),
                colli_per_pal=int(form.get('colli_per_pal') or 0),
                pcs_total=int(form.get('pcs_total') or 0),
                pal=int(form.get('pal') or 0),
                product=product_name,
                gross_kg=float(form.get('gross_kg') or 0),
                net_kg=float(form.get('net_kg') or 0),
                sender=form.get('sender', ''),
                customs_status=form.get('customs_status', ''),
                stockref=form.get('stockref', ''),
                warehouse_address=form.get('warehouse_address', ''),
                client=form.get('client', ''),
                pos_no=form.get('pos_no', ''),
                customer_ref=form.get('customer_ref', ''),
                related_order_id=item.id
            )

            db.session.add(entry)
            db.session.commit()
            log_activity("Add Stockreport Entry", f"#{item.order_number}")
            flash("Stockreport entry saved successfully.", "success")
            return redirect(url_for('warehouse.warehouse'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error saving stockreport entry: {e}", "danger")

    return render_template('stockreport_form.html', item=item, product_options=product_options)

@warehouse_bp.route('/stockreport/view/<int:item_id>')
@login_required
def view_stockreport_entries(item_id):
    entries = StockReportEntry.query.filter_by(related_order_id=item_id).all()

    if not entries:
        flash("No stockreport entries found.", "warning")
        return redirect(url_for('warehouse.warehouse'))

    # Use the first entry as a base for shared metadata
    first_entry = entries[0]

    # ✅ Compute customs-related fields
    atb_frist = customs_ozl = free_till = None
    if first_entry.customs_status == "T1" and first_entry.entrance_date:
        atb_frist = first_entry.entrance_date.strftime("%d.%m.%Y")
        customs_ozl = "OZL Hamburg"
        free_till = (first_entry.entrance_date + timedelta(days=90)).strftime("%d.%m.%Y")

        # ✅ Attach to the first entry for template access
        setattr(first_entry, 'atb_first', atb_frist)
        setattr(first_entry, 'customs_ozl', customs_ozl)
        setattr(first_entry, 'free_till', free_till)

    # ✅ Ensure signature fields are passed from entry if present
    signature_date_client = getattr(first_entry, 'signature_date_client', None)
    signature_client = getattr(first_entry, 'signature_client', None)
    signature_date_warehouse = getattr(first_entry, 'signature_date_warehouse', None)
    signature_warehouse = getattr(first_entry, 'signature_warehouse', None)

    return render_template(
        "view_stockreport.html",
        entries=entries,
        item=first_entry,
        signature_date_client=signature_date_client,
        signature_client=signature_client,
        signature_date_warehouse=signature_date_warehouse,
        signature_warehouse=signature_warehouse
    )


@warehouse_bp.route('/stockreport/download/<int:item_id>')
@login_required
def download_stockreport(item_id):
    item = WarehouseStock.query.get_or_404(item_id)
    if not can_view_all(current_user.role) and current_user.id != item.user_id:
        flash("Access denied.", "danger")
        return redirect(url_for('warehouse.warehouse'))
    entries = StockReportEntry.query.filter_by(related_order_id=item_id).all()
    html_content = render_template('view_stockreport.html', item=item, entries=entries)
    pdf_content = HTML(string=html_content, base_url=request.url_root).write_pdf()
    response = make_response(pdf_content)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=StockReport.pdf'
    return response

@warehouse_bp.route('/stockreport/edit/<int:entry_id>', methods=['POST'])
@login_required
def edit_stockreport(entry_id):
    entry = StockReportEntry.query.get_or_404(entry_id)
    order = entry.related_order

    try:
        # Handle special field types
        if 'entrance_date' in request.form:
            date_str = request.form.get('entrance_date')
            if date_str:
                entry.entrance_date = datetime.strptime(date_str, '%Y-%m-%d')

        # Update other fields
        entry_fields = [
            'article_batch', 'colli', 'packing', 'pcs', 'colli_per_pal', 'pcs_total',
            'pal', 'product', 'gross_kg', 'net_kg', 'sender', 'customs_status', 'stockref'
        ]
        for field in entry_fields:
            if field in request.form:
                setattr(entry, field, request.form.get(field))

        # Order-level header fields
        order_fields = [
            'warehouse_address', 'pos_no', 'client', 'customer_ref',
            'atb_first', 'customs_ozl', 'free_till',
            'signature_date_client', 'signature_client',
            'signature_date_warehouse', 'signature_warehouse'
        ]
        for field in order_fields:
            if field in request.form:
                setattr(order, field, request.form.get(field))

        db.session.commit()
        log_activity("Edit Stockreport Entry", f"Entry #{entry_id} for #{order.order_number}")

        return '', 204

    except Exception as e:
        print("❌ Error saving stockreport edit:", e)
        return "Internal server error", 500



@warehouse_bp.route('/stockreport/delete/<int:entry_id>', methods=['POST'])
@login_required
def delete_stockreport(entry_id):
    entry = StockReportEntry.query.get_or_404(entry_id)
    item_id = entry.related_order_id

    try:
        db.session.delete(entry)
        db.session.commit()
        log_activity("Delete Stockreport Entry", f"Entry #{entry_id}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"success": True})
        else:
            flash("Stockreport deleted.", "success")
            return redirect(url_for('warehouse.warehouse'))

    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"success": False, "error": str(e)}), 400
        flash(f"Delete failed: {e}", "danger")
        return redirect(url_for('warehouse.warehouse'))
    
@warehouse_bp.route('/stockreport/view_by_order/<string:order_number>')
@login_required
def view_stockreport_by_order(order_number):
    # Try WarehouseStock first
    item = WarehouseStock.query.filter_by(order_number=order_number).first()

    # Fallback to DeliveredGoods
    if not item:
        item = DeliveredGoods.query.filter_by(order_number=order_number).first_or_404()

    # Permission check (only if from WarehouseStock)
    if isinstance(item, WarehouseStock):
        if not can_view_all(current_user.role) and current_user.id != item.user_id:
            flash("Access denied.", "danger")
            return redirect(url_for('warehouse.warehouse'))

    # Load stock entries
    entries = StockReportEntry.query.filter_by(related_order_id=item.id).all()

    # Inherit report header fields from StockReportEntry (first entry)
    first_entry = entries[0] if entries else None

    # Calculate customs info
    atb_frist = customs_ozl = free_till = None
    if first_entry and first_entry.customs_status == "T1" and first_entry.entrance_date:
        atb_frist = first_entry.entrance_date.strftime("%d.%m.%Y")
        customs_ozl = "OZL Hamburg"
        free_till = (first_entry.entrance_date + timedelta(days=90)).strftime("%d.%m.%Y")

    return render_template(
        "view_stockreport.html",
        entries=entries,
        item=item,
        atb_frist=atb_frist,
        customs_ozl=customs_ozl,
        free_till=free_till,
        signature_date_client=getattr(first_entry, 'signature_date_client', None),
        signature_client=getattr(first_entry, 'signature_client', None),
        signature_date_warehouse=getattr(first_entry, 'signature_date_warehouse', None),
        signature_warehouse=getattr(first_entry, 'signature_warehouse', None),
        report_header=getattr(first_entry, '__dict__', {})  # 🚨 Pass extra fields
    )
