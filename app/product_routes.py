from flask import Blueprint, jsonify, request
from app.models import Product, Store
from app import db
from app.routes import token_required

product_bp = Blueprint('product', __name__)

# ✅ Add Product (Merchant Only)
@product_bp.route('/products', methods=['POST'])
@token_required
def add_product(current_user):
    if current_user.role != 'merchant':
        return jsonify({'message': 'Permission denied'}), 403

    data = request.get_json()
    name = data.get('name')
    buying_price = data.get('buying_price')
    selling_price = data.get('selling_price')
    stock_quantity = data.get('stock_quantity')
    store_id = data.get('store_id')

    if not all([name, buying_price, selling_price, stock_quantity, store_id]):
        return jsonify({'message': 'Missing required fields'}), 400

    store = Store.query.get(store_id)
    if not store or store.merchant_id != current_user.id:
        return jsonify({'message': 'Invalid store or unauthorized access'}), 403

    product = Product(
        name=name,
        buying_price=buying_price,
        selling_price=selling_price,
        stock_quantity=stock_quantity,
        store_id=store_id
    )

    db.session.add(product)
    db.session.commit()
    return jsonify({'message': 'Product added successfully'}), 201

# ✅ Get All Products (Merchant & Admin)
@product_bp.route('/products', methods=['GET'])
@token_required
def get_products(current_user):
    if current_user.role == 'admin':
        products = Product.query.all()
    elif current_user.role == 'merchant':
        products = Product.query.join(Store).filter(Store.merchant_id == current_user.id).all()
    else:
        return jsonify({'message': 'Permission denied'}), 403

    return jsonify([
        {
            "id": product.id,
            "name": product.name,
            "buying_price": product.buying_price,
            "selling_price": product.selling_price,
            "stock_quantity": product.stock_quantity,
            "store_id": product.store_id
        }
        for product in products
    ]), 200

# ✅ Update Product (Merchant Only)
@product_bp.route('/products/<int:product_id>', methods=['PUT'])
@token_required
def update_product(current_user, product_id):
    if current_user.role != 'merchant':
        return jsonify({'message': 'Permission denied'}), 403

    product = Product.query.get(product_id)
    if not product or product.store.merchant_id != current_user.id:
        return jsonify({'message': 'Product not found or unauthorized access'}), 403

    data = request.get_json()
    for key in ['name', 'buying_price', 'selling_price', 'stock_quantity']:
        if key in data:
            setattr(product, key, data[key])

    db.session.commit()
    return jsonify({'message': 'Product updated successfully'}), 200

# ✅ Delete Product (Merchant Only)
@product_bp.route('/products/<int:product_id>', methods=['DELETE'])
@token_required
def delete_product(current_user, product_id):
    if current_user.role != 'merchant':
        return jsonify({'message': 'Permission denied'}), 403

    product = Product.query.get(product_id)
    if not product or product.store.merchant_id != current_user.id:
        return jsonify({'message': 'Product not found or unauthorized access'}), 403

    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted successfully'}), 200
