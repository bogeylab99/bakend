from flask import Blueprint, jsonify
from app.models import Product, Store
from app.routes import token_required
from app import db

graph_bp = Blueprint('graph', __name__)

# ✅ Store Performance Graph Data
@graph_bp.route('/graph/store-performance', methods=['GET'])
@token_required
def store_performance_graph(current_user):
    if current_user.role not in ['admin', 'merchant']:
        return jsonify({'message': 'Permission denied'}), 403

    stores = Store.query.all()
    store_data = []

    for store in stores:
        products = Product.query.filter_by(store_id=store.id).all()
        total_revenue = sum(p.selling_price * p.stock_quantity for p in products)
        total_stock = sum(p.stock_quantity for p in products)
        spoiled_stock = sum(p.spoiled_quantity for p in products)

        store_data.append({
            "store_id": store.id,
            "store_name": store.name,
            "total_revenue": total_revenue,
            "total_stock": total_stock,
            "spoiled_stock": spoiled_stock
        })

    return jsonify(store_data), 200

# ✅ Top-Selling Products Graph Data
@graph_bp.route('/graph/top-products', methods=['GET'])
@token_required
def top_selling_products_graph(current_user):
    if current_user.role not in ['admin', 'merchant']:
        return jsonify({'message': 'Permission denied'}), 403

    products = Product.query.all()
    sorted_products = sorted(products, key=lambda p: p.selling_price * p.stock_quantity, reverse=True)[:5]

    return jsonify([
        {"id": p.id, "name": p.name, "revenue": p.selling_price * p.stock_quantity}
        for p in sorted_products
    ]), 200

# ✅ Spoiled Products Graph Data
@graph_bp.route('/graph/spoiled-products', methods=['GET'])
@token_required
def spoiled_products_graph(current_user):
    if current_user.role not in ['admin', 'merchant']:
        return jsonify({'message': 'Permission denied'}), 403

    spoiled_products = sorted(Product.query.all(), key=lambda p: p.spoiled_quantity, reverse=True)[:5]

    return jsonify([
        {"id": p.id, "name": p.name, "spoiled_quantity": p.spoiled_quantity}
        for p in spoiled_products
    ]), 200
