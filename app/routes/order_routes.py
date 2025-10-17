
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from app.models import db, Order, DeliveredGoods
from datetime import datetime
from app.roles import can_view_all, can_edit
from flask import flash, redirect, url_for
from app.models import ArchivedOrder
from app.utils.products import add_product_if_new
from app.utils.logging import log_activity
from sqlalchemy.exc import SQLAlchemyError
import os

order_bp = Blueprint('order', __name__)

PRODUCTS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'products.txt'))

def load_products():
    try:
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            return sorted(set(line.strip() for line in f if line.strip()))
    except FileNotFoundError:
        return []
@order_bp.route('/add_order', methods=['POST'])
@login_required
def add_order():
    try:
        data = request.form
        quantity = float(data['quantity'])
        order_date = data['order_date'].strip()
        etd = data.get('etd', '').strip()
        eta = data.get('eta', '').strip()
        etd_dt = None
        eta_dt = None

        if quantity <= 0:
            return jsonify({'success': False, 'message': 'Quantity must be a positive number.'}), 400

        if etd:
            etd_dt = datetime.strptime(etd, '%d.%m.%y')
        if eta:
            eta_dt = datetime.strptime(eta, '%d.%m.%y')

        if etd_dt and eta_dt and etd_dt > eta_dt:
            return jsonify({'success': False, 'message': 'ETD cannot be later than ETA.'}), 400

        if etd_dt and order_date:
            order_date_dt = datetime.strptime(order_date, '%d.%m.%y')
            if order_date_dt > etd_dt:
                return jsonify({'success': False, 'message': 'Order Date cannot be later than ETD.'}), 400

        order_number = data.get('order_number', '').strip()
        if not order_number:
            return jsonify({'success': False, 'message': 'Order must have an Order Number.'}), 400

        product_name = data['product_name'].strip()

        # ✅ Save new product if missing
        add_product_if_new(product_name)

        new_order = Order(
            user_id=current_user.id,
            order_date=order_date,
            order_number=order_number,
            product_name=product_name,
            buyer=data.get('buyer', ''),
            responsible=data.get('responsible', ''),
            quantity=quantity,
            required_delivery=data.get('required_delivery', ''),
            terms_of_delivery=data.get('terms_of_delivery', ''),
            payment_date=data.get('payment_date', ''),
            etd=etd,
            eta=eta,
            ata=data.get('ata', ''),
            transit_status=data.get('transit_status', ''),
            transport=data.get('transport', '')
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


@order_bp.route('/edit_order/<int:order_id>', methods=["GET", "POST"])
@login_required
def edit_order(order_id):
    order = Order.query.get_or_404(order_id)

    # 🔐 Permissions
    if not can_edit(current_user.role) and order.user_id != current_user.id:
        if request.method == "POST":
            return jsonify({'success': False, 'message': 'You do not have permission to edit this order.'}), 403
        else:
            flash("You do not have permission to edit this order.", "danger")
            return redirect(url_for('dashboard.dashboard'))

    if request.method == "GET":
        # 🌐 Render the edit form page
        return render_template("edit_order.html", order=order)

    # 🔄 POST (AJAX edit submission)
    try:
        data = request.form

        # Basic validation
        quantity = float(data.get('quantity', 0))
        if quantity <= 0:
            return jsonify({'success': False, 'message': 'Quantity must be a positive number.'}), 400

        # Dates: parse only if non-empty
        def parse_date(value):
            return datetime.strptime(value, '%d.%m.%y') if value else None

        etd_dt = parse_date(data.get('etd', '').strip())
        eta_dt = parse_date(data.get('eta', '').strip())
        order_date_dt = parse_date(data.get('order_date', '').strip())

        if etd_dt and eta_dt and etd_dt > eta_dt:
            return jsonify({'success': False, 'message': 'ETD cannot be later than ETA.'}), 400
        if etd_dt and order_date_dt and order_date_dt > etd_dt:
            return jsonify({'success': False, 'message': 'Order Date cannot be later than ETD.'}), 400

        # Update fields
        product_name = data.get('product_name', '').strip()
        add_product_if_new(product_name)
        order.product_name = product_name

        order.order_date = data.get('order_date', '').strip()
        order.order_number = data.get('order_number', '').strip()
        order.buyer = data.get('buyer', '').strip()
        order.responsible = data.get('responsible', '').strip()
        order.quantity = quantity
        order.required_delivery = data.get('required_delivery', '').strip()
        order.terms_of_delivery = data.get('terms_of_delivery', '').strip()
        order.payment_date = data.get('payment_date', '').strip()
        order.etd = data.get('etd', '').strip()
        order.eta = data.get('eta', '').strip()
        order.ata = data.get('ata', '').strip()
        order.transit_status = data.get('transit_status', '').strip()
        order.transport = data.get('transport', '').strip()

        db.session.commit()
        log_activity("Edit Order", f"#{order.order_number} – updated fields")

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
@order_bp.route('/delete_order/<int:order_id>')
@login_required
def delete_order(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        if order.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Permission denied.'}), 403

        db.session.delete(order)
        db.session.commit()
        log_activity("Delete Order", f"#{order.order_number}")
        return jsonify({'success': True, 'message': 'Order deleted successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400


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
        except:
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

    # Create DeliveredGoods entry
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

    # Archive original order before deletion
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
