from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User, Order, WarehouseStock, DeliveredGoods
from datetime import datetime
from flask import request
import os
from werkzeug.utils import secure_filename
from flask import send_from_directory
from flask import current_app
from app.roles import can_view_all

PRODUCTS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'products.txt'))
def load_products():
    try:
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            return sorted(set(line.strip() for line in f if line.strip()))
    except FileNotFoundError:
        return []

main = Blueprint('main', __name__)

@main.app_context_processor
def inject_globals():
    return dict(current_user=current_user, current_path=request.path)

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            remember = True if request.form.get('remember') == 'on' else False
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
        else:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('main.login'))

    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/dashboard_alt')
@login_required
def dashboard_alt():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.asc()).all()

    # 🧮 Count summaries
    in_transit_count = Order.query.filter_by(user_id=current_user.id).count()
    warehouse_count = WarehouseStock.query.filter_by(user_id=current_user.id).count()
    delivered_count = DeliveredGoods.query.filter_by(user_id=current_user.id).count()

    return render_template(
        'dashboard.html',
        orders=orders,
        now=datetime.now(),
        product_list=load_products(),
        in_transit_count=in_transit_count,
        warehouse_count=warehouse_count,
        delivered_count=delivered_count
    )

@main.route('/add_order', methods=['POST'])
@login_required
def add_order():
    try:
        data = request.form
        quantity = float(data['quantity'])
        order_date = data['order_date']
        etd = data['etd']
        eta = data['eta']

        if quantity <= 0:
            return jsonify({'success': False, 'message': 'Quantity must be a positive number.'}), 400

        order_date_dt = datetime.strptime(order_date, '%d.%m.%y')
        etd_dt = datetime.strptime(etd, '%d.%m.%y')
        eta_dt = datetime.strptime(eta, '%d.%m.%y')

        if order_date_dt > etd_dt:
            return jsonify({'success': False, 'message': 'Order Date cannot be later than ETD.'}), 400
        if etd_dt > eta_dt:
            return jsonify({'success': False, 'message': 'ETD cannot be later than ETA.'}), 400

        new_order = Order(
            user_id=current_user.id,
            order_date=order_date,
            order_number=data['order_number'],
            product_name=data['product_name'],
            buyer=data['buyer'],
            responsible=data['responsible'],
            quantity=quantity,
            required_delivery=data['required_delivery'],
            terms_of_delivery=data['terms_of_delivery'],
            payment_date=data['payment_date'],
            etd=etd,
            eta=eta,
            ata=data['ata'],
            transit_status=data['transit_status'],
            transport=data['transport']
        )
        db.session.add(new_order)
        db.session.commit()
        # Append product name if not in products.txt
        new_product = data['product_name'].strip()
        existing_products = load_products()
        if new_product and new_product not in existing_products:
            try:
                with open(PRODUCTS_FILE, 'a', encoding='utf-8') as f:
                    f.write(f"{new_product}\n")
                print(f"✅ Product added to products.txt: {new_product}")
            except Exception as file_error:
                print(f"⚠️ Could not write to products.txt – {file_error}")


        return jsonify({'success': True, 'message': 'Order added successfully!'})

    except ValueError:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Invalid quantity format. Use a valid number.'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400
    
    

@main.route('/edit_order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def edit_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'You do not have permission to edit this order.'}), 403

    if request.method == 'POST':
        try:
            data = request.form
            quantity = float(data['quantity'])
            order_date = data['order_date']
            etd = data['etd']
            eta = data['eta']

            if quantity <= 0:
                return jsonify({'success': False, 'message': 'Quantity must be positive.'}), 400

            order_date_dt = datetime.strptime(order_date, '%d.%m.%y')
            etd_dt = datetime.strptime(etd, '%d.%m.%y')
            eta_dt = datetime.strptime(eta, '%d.%m.%y')

            if order_date_dt > etd_dt:
                return jsonify({'success': False, 'message': 'Order Date cannot be later than ETD.'}), 400
            if etd_dt > eta_dt:
                return jsonify({'success': False, 'message': 'ETD cannot be later than ETA.'}), 400

            order.order_date = order_date
            order.order_number = data['order_number']
            order.product_name = data['product_name']
            order.buyer = data['buyer']
            order.responsible = data['responsible']
            order.quantity = quantity
            order.required_delivery = data['required_delivery']
            order.terms_of_delivery = data['terms_of_delivery']
            order.payment_date = data['payment_date']
            order.etd = etd
            order.eta = eta
            order.ata = data['ata']
            order.transit_status = data['transit_status']
            order.transport = data['transport']
            db.session.commit()
            return jsonify({'success': True, 'message': 'Order updated successfully!'})
        except ValueError:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Invalid quantity format.'}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400

    return render_template('edit_order.html', order=order)

@main.route('/delete_order/<int:order_id>')
@login_required
def delete_order(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        if order.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Permission denied.'}), 403

        db.session.delete(order)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Order deleted successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

def get_delivery_year_dict(order):
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

@main.route('/api/orders')
@login_required
def get_orders():
    if can_view_all(current_user.role):
        orders = Order.query.order_by(Order.order_date.asc()).all()
    else:
        orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.asc()).all()

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
        'delivery_year': get_delivery_year_dict(order)
    } for order in orders]

    return jsonify(orders_data)

@main.route('/warehouse')
@login_required
def warehouse():
    if can_view_all(current_user.role):
        warehouse_items = WarehouseStock.query.all()
    else:
        warehouse_items = WarehouseStock.query.filter_by(user_id=current_user.id).all()
    return render_template('warehouse.html', warehouse_items=warehouse_items)

@main.route('/delivered')
@login_required
def delivered():
    if can_view_all(current_user.role):
        delivered_items = DeliveredGoods.query.all()
    else:
        delivered_items = DeliveredGoods.query.filter_by(user_id=current_user.id).all()

    for item in delivered_items:
        if isinstance(item.delivery_date, str):
            try:
                item.delivery_date = datetime.strptime(item.delivery_date, '%Y-%m-%d')
            except ValueError:
                pass

    return render_template('delivered.html', delivered_items=delivered_items)

@main.route('/add_warehouse_manual', methods=['POST'])
@login_required
def add_warehouse_manual():
    try:
        order_number = request.form['order_number']
        product_name = request.form['product_name']
        quantity = float(request.form['quantity'])
        ata = request.form['ata']
        transport = request.form['transport']
        notes = request.form.get('notes', 'Manual Entry')

        if quantity <= 0:
            flash("Quantity must be greater than 0", "danger")
            return redirect(url_for('main.warehouse'))

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

        flash("Manual order successfully added to warehouse.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding manual order: {e}", "danger")

    return redirect(url_for('main.warehouse'))


@main.route('/deliver_partial/<int:item_id>', methods=['POST'])
@login_required
def deliver_partial(item_id):
    item = WarehouseStock.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('main.warehouse'))

    try:
        qty_to_deliver = float(request.form['quantity'])
    except ValueError:
        flash('Invalid quantity entered.', 'danger')
        return redirect(url_for('main.warehouse'))

    if qty_to_deliver <= 0 or qty_to_deliver > float(item.quantity):
        flash(f"Invalid quantity. Must be between 1 and {item.quantity}.", 'danger')
        return redirect(url_for('main.warehouse'))

    # Adjust warehouse quantity or delete if zero
    item.quantity = float(item.quantity) - qty_to_deliver
    if item.quantity <= 0:
        db.session.delete(item)
    else:
        db.session.add(item)


    # Create a DeliveredGoods entry
    delivery = DeliveredGoods(
        user_id=current_user.id,
        order_number=item.order_number,
        product_name=item.product_name,
        quantity=qty_to_deliver,
        transport=item.transport,
        delivery_source="From Warehouse",
        notes=item.notes,
        delivery_date=datetime.now().strftime('%d.%m.%y')
    )
    db.session.add(delivery)

    db.session.commit()
    flash(f'Delivered {qty_to_deliver} from warehouse.', 'success')
    return redirect(url_for('main.warehouse'))


@main.route('/edit_warehouse/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_warehouse(item_id):
    item = WarehouseStock.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('main.warehouse'))

    if request.method == 'POST':
        item.quantity = float(request.form['quantity'])
        item.ata = request.form['ata']
        item.notes = request.form.get("notes")
        db.session.commit()
        flash('Warehouse item updated successfully!', 'success')
        return redirect(url_for('main.warehouse'))

    return render_template('edit_warehouse.html', item=item)


@main.route('/edit_delivered/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_delivered(item_id):
    item = DeliveredGoods.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('main.delivered'))

    if request.method == 'POST':
        item.quantity = float(request.form['quantity'])
        item.delivery_source = request.form['delivery_source']
        item.delivery_date = request.form['delivery_date']
        item.notes = request.form.get("notes")
        db.session.commit()
        flash('Delivered item updated successfully!', 'success')
        return redirect(url_for('main.delivered'))

    return render_template('edit_delivered.html', item=item)

@main.route('/stock_order/<int:order_id>', methods=['POST'])
@login_required
def stock_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('main.dashboard'))

    if not order.order_number or not order.product_name:
        flash('Order must have an Order Number and Product Name before stocking.', 'danger')
        return redirect(url_for('main.dashboard'))

    # Create WarehouseStock record
    new_stock = WarehouseStock(
        user_id=order.user_id,
        order_number=order.order_number,
        product_name=order.product_name,
        quantity=order.quantity,
        ata=order.ata,
        transport=order.transport,
        transit_status='In Stock'
    )
    db.session.add(new_stock)
    db.session.delete(order)
    db.session.commit()

    flash(f'Order {order.order_number} moved to Warehouse.', 'success')
    return redirect(url_for('main.dashboard'))


@main.route('/deliver_direct/<int:order_id>', methods=['POST'])
@login_required
def deliver_direct(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash("Unauthorized access", "danger")
        return redirect(url_for("main.dashboard"))

    if not order.order_number or not order.product_name:
        flash('Order must have an Order Number and Product Name before delivering.', 'danger')
        return redirect(url_for('main.dashboard'))

    delivered = DeliveredGoods(
        user_id=order.user_id,
        order_number=order.order_number,
        product_name=order.product_name,
        quantity=order.quantity,
        delivery_source="Direct from Transit",
        delivery_date=order.ata,
        transport=order.transport,
    )

    db.session.add(delivered)
    db.session.delete(order)
    db.session.commit()

    flash(f"Order {order.order_number} delivered successfully.", "success")
    return redirect(url_for("main.dashboard"))


@main.route('/restore_to_dashboard/<int:item_id>', methods=['POST'])
@login_required
def restore_to_dashboard(item_id):
    item = WarehouseStock.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('main.warehouse'))

    today = datetime.now().strftime('%d.%m.%y')  # 🟢 FIXED FORMAT

    restored_order = Order(
        user_id=current_user.id,
        order_date=today,
        order_number=item.order_number,
        product_name=item.product_name,
        buyer="Restored",
        responsible="Restored",
        quantity=item.quantity,
        required_delivery=today,
        terms_of_delivery="Restored",
        payment_date="",
        etd=today,
        eta=today,
        ata=item.ata or today,
        transit_status="arrived",
        transport="truck"
    )

    db.session.add(restored_order)
    db.session.delete(item)
    db.session.commit()

    flash('Item restored to dashboard.', 'success')
    return redirect(url_for('main.warehouse'))


@main.route('/restore_from_delivered/<int:item_id>', methods=['POST'])
@login_required
def restore_from_delivered(item_id):
    item = DeliveredGoods.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('main.delivered'))

    today = datetime.now().strftime('%d.%m.%y')  # 🟢 FIXED FORMAT

    if item.delivery_source == "Direct from Transit":
        restored_order = Order(
            user_id=current_user.id,
            order_date=today,
            order_number=item.order_number,
            product_name=item.product_name,
            buyer="Restored",
            responsible="Restored",
            quantity=item.quantity,
            required_delivery=today,
            terms_of_delivery="Restored",
            payment_date="",
            etd=today,
            eta=today,
            ata=item.delivery_date or today,
            transit_status="arrived",
            transport="truck"
        )
        db.session.add(restored_order)
    else:  # From Warehouse
        restored_stock = WarehouseStock(
            user_id=current_user.id,
            order_number=item.order_number,
            product_name=item.product_name,
            quantity=item.quantity,
            ata=item.delivery_date or today
        )
        db.session.add(restored_stock)

    db.session.delete(item)
    db.session.commit()

    flash('Delivered item restored.', 'success')
    return redirect(url_for('main.delivered'))

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@main.route('/upload_pod/<int:item_id>', methods=['POST'])
@login_required
def upload_pod(item_id):
    file = request.files['pod']
    if file and file.filename:
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        item = DeliveredGoods.query.get_or_404(item_id)
        item.pod_filename = filename
        db.session.commit()

        flash("POD uploaded.", "success")
    else:
        flash("No file selected.", "danger")

    return redirect(url_for('main.delivered'))

@main.route('/view_pod/<filename>')
@login_required
def view_pod(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@main.route('/delete_pod/<int:item_id>', methods=['POST'])
@login_required
def delete_pod(item_id):
    item = DeliveredGoods.query.get_or_404(item_id)
    if item.pod_filename:
        file_path = os.path.join(UPLOAD_FOLDER, item.pod_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        item.pod_filename = None
        db.session.commit()
        flash("POD deleted.", "success")
    else:
        flash("No POD file to delete.", "warning")
    return redirect(url_for('main.delivered'))

#Delete Manual Warehouse Entry
@main.route('/delete_warehouse/<int:item_id>', methods=['POST'])
@login_required
def delete_warehouse(item_id):
    item = WarehouseStock.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('main.warehouse'))

    db.session.delete(item)
    db.session.commit()
    flash('Warehouse item deleted successfully.', 'success')
    return redirect(url_for('main.warehouse'))

@main.route('/stats')
@login_required
def stats():
    from app.models import Order, WarehouseStock, DeliveredGoods
    return {
        "orders": Order.query.count(),
        "warehouse": WarehouseStock.query.count(),
        "delivered": DeliveredGoods.query.count()
    }
