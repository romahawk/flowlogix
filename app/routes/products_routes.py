from flask import Blueprint, jsonify, request
from app.utils.products import load_products, add_product_if_new

products_bp = Blueprint('products', __name__)

@products_bp.route('/api/products', methods=['GET'])
def get_products():
    products = load_products()
    print("📦 Loaded products:", products)  # ✅ For debugging
    return jsonify(products)


@products_bp.route('/api/products/add', methods=['POST'])
def add_product():
    """Add new product if not already in products.txt"""
    data = request.get_json()
    name = data.get('name', '').strip()
    if not name:
        return jsonify({"status": "error", "message": "No name provided"}), 400

    add_product_if_new(name)
    return jsonify({"status": "success", "added": name})
