from flask import Blueprint, jsonify, request
from app.models import Product, User
from app import db
from app.routes import token_required

payment_stock_bp = Blueprint('payment_stock', __name__)

# ✅ View Paid & Unpaid Products (Admins & Merchants)
@payment_stock_bp.route('/payments', methods=['GET'])
@token_required
def get_payment_status(current_user):
    if current_user.role not in ['admin', 'merchant']:
        return jsonify({'message': 'Permission denied'}), 403

    store_id = request.args.get('store_id')  # Optional store filter

    query = Product.query
    if store_id:
        query = query.filter_by(store_id=store_id)

    paid_products = query.filter_by(payment_status='paid').all()
    unpaid_products = query.filter_by(payment_status='not paid').all()

    return jsonify({
        "paid_products": [
            {"id": p.id, "name": p.name, "price": p.selling_price, "stock": p.stock_quantity}
            for p in paid_products
        ],
        "unpaid_products": [
            {"id": p.id, "name": p.name, "price": p.selling_price, "stock": p.stock_quantity}
            for p in unpaid_products
        ]
    }), 200

# ✅ Mark Product as Paid (Admins Only)
@payment_stock_bp.route('/payments/<int:product_id>', methods=['PUT'])
@token_required
def mark_as_paid(current_user, product_id):
    if current_user.role != 'admin':
        return jsonify({'message': 'Permission denied'}), 403

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404

    if product.payment_status == 'paid':
        return jsonify({'message': 'Product is already marked as paid'}), 400

    product.payment_status = 'paid'
    db.session.commit()
    
    return jsonify({'message': 'Payment status updated to paid'}), 200

# ✅ Update Stock Details (Clerks Only)
@payment_stock_bp.route('/stock/<int:product_id>', methods=['PUT'])
@token_required
def update_stock(current_user, product_id):
    if current_user.role != 'clerk':
        return jsonify({'message': 'Permission denied'}), 403

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404

    data = request.get_json()
    stock_quantity = data.get('stock_quantity')
    spoiled_quantity = data.get('spoiled_quantity')

    if stock_quantity is not None:
        product.stock_quantity = stock_quantity
    if spoiled_quantity is not None:
        product.spoiled_quantity = spoiled_quantity

    db.session.commit()
    return jsonify({'message': 'Stock details updated successfully'}), 200
