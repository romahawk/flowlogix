import os
from flask import Blueprint, request, redirect, url_for, flash, current_app, send_from_directory, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import db, DeliveredGoods
from app.utils.logging import log_activity

upload_bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('/upload_pod', methods=['POST'])
@login_required
def upload_pod():
    item_id = request.args.get('item_id')
    if not item_id:
        flash("Missing item ID", "danger")
        return redirect(request.referrer or url_for('delivered.delivered'))

    item = DeliveredGoods.query.get_or_404(item_id)
    if item.user_id != current_user.id and current_user.role != 'admin':
        flash("Unauthorized access", "danger")
        return redirect(url_for('delivered.delivered'))


    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.referrer or url_for('delivered.delivered'))

    file = request.files['file']

    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.referrer or url_for('delivered.delivered'))

    if file and allowed_file(file.filename):
        filename = secure_filename(str(file.filename or ''))
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        item.pod_filename = filename
        db.session.commit()
        log_activity("Upload POD", f"{item.order_number} – {filename}")
        flash('File uploaded successfully', 'success')
        return redirect(request.referrer or url_for('delivered.delivered'))

    else:
        flash('File type not allowed', 'danger')
        return redirect(request.referrer or url_for('delivered.delivered'))

@upload_bp.route('/view_pod/<filename>')
@login_required
def view_pod(filename):
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
    try:
        return send_from_directory(upload_folder, filename)
    except FileNotFoundError:
        abort(404)

@upload_bp.route('/delete_pod/<int:item_id>', methods=['POST'])
@login_required
def delete_pod(item_id):
    item = DeliveredGoods.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('delivered.delivered'))

    if item.pod_filename:
        try:
            file_path = os.path.join(current_app.root_path, 'static', 'uploads', item.pod_filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            flash(f'Error deleting file: {e}', 'danger')

    item.pod_filename = None
    db.session.commit()
    log_activity("Delete POD", f"{item.order_number}")
    flash('POD file deleted successfully', 'success')
    return redirect(url_for('delivered.delivered'))
