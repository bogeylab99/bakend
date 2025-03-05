from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from app.models import Product, User, Store, SupplyRequest
from app import db
from app.routes import token_required  # Assuming token_required is defined here or in auth.py

store_bp = Blueprint('store', __name__)

# Handle CORS for all responses
@store_bp.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, x-access-token"
    return response

# Handle Preflight Requests Globally
@store_bp.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight OK"}), 200

# Get All Clerks (Admin/Merchant Only) - Move to auth.py if appropriate
@store_bp.route('/auth/clerks', methods=['GET'])
@token_required
@cross_origin(origin="http://localhost:3000", supports_credentials=True)
def get_clerks(current_user):
    if current_user.role not in ['admin', 'merchant']:
        return jsonify({'message': 'Permission denied'}), 403

    clerks = User.query.filter_by(role='clerk').all()
    return jsonify([{"id": c.id, "email": c.email} for c in clerks]), 200

# Clerk Views Stock Details by Store ID
@store_bp.route('/stock/<int:store_id>', methods=['GET'])
@token_required
@cross_origin(origin="http://localhost:3000", supports_credentials=True)
def view_stock_by_store(current_user, store_id):
    if current_user.role not in ['clerk', 'admin']:
        return jsonify({'message': 'Permission denied'}), 403

    if current_user.role == 'clerk' and current_user.store_id != store_id:
        return jsonify({'message': 'Unauthorized to view this store’s stock'}), 403

    products = Product.query.filter_by(store_id=store_id).all()
    stock_data = [
        {
            "id": p.id,
            "name": p.name,
            "buying_price": float(p.buying_price),
            "selling_price": float(p.selling_price),
            "quantity": p.stock_quantity,  # Match ClerkDashboard.js field
            "spoiled_quantity": p.spoiled_quantity,
            "payment_status": p.payment_status
        } for p in products
    ]
    return jsonify({'stock': stock_data}), 200

# Clerk/Admin Adds New Stock
@store_bp.route('/stock', methods=['POST'])
@token_required
@cross_origin(origin="http://localhost:3000", supports_credentials=True)
def add_stock(current_user):
    if current_user.role not in ['admin', 'clerk']:
        return jsonify({'message': 'Permission denied'}), 403

    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400

        required_fields = ['item', 'quantity', 'buying_price', 'selling_price', 'store_id']  # Match frontend
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'Missing field: {field}'}), 400

        store = Store.query.get(data['store_id'])
        if not store:
            return jsonify({'message': 'Store not found'}), 404

        if current_user.role == 'clerk' and current_user.store_id != store.id:
            return jsonify({'message': 'Unauthorized to add stock to this store'}), 403

        # Check if product exists, update or create
        product = Product.query.filter_by(name=data['item'], store_id=data['store_id']).first()
        if product:
            product.stock_quantity += int(data['quantity'])
            product.buying_price = float(data['buying_price'])
            product.selling_price = float(data['selling_price'])
        else:
            product = Product(
                name=data['item'],
                buying_price=float(data['buying_price']),
                selling_price=float(data['selling_price']),
                stock_quantity=int(data['quantity']),
                spoiled_quantity=0,
                payment_status='not paid',
                store_id=store.id
            )
            db.session.add(product)

        db.session.commit()
        return jsonify({'message': 'Stock item added successfully', 'product_id': product.id}), 201

    except Exception as e:
        print("🔥 Error adding stock:", str(e))
        db.session.rollback()
        return jsonify({'message': 'Internal Server Error', 'error': str(e)}), 500

# Admin Updates Stock Quantity
@store_bp.route('/stock/<int:product_id>', methods=['PUT'])
@token_required
@cross_origin(origin="http://localhost:3000", supports_credentials=True)
def update_stock(current_user, product_id):
    if current_user.role != 'admin':
        return jsonify({'message': 'Permission denied'}), 403

    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    stock_change = data.get('stock_quantity')
    if stock_change is None:
        return jsonify({'message': 'Stock quantity required'}), 400

    product.stock_quantity = int(stock_change)  # Replace, not increment
    db.session.commit()

    return jsonify({'message': 'Stock quantity updated successfully'}), 200

# Admin Updates Payment Status
@store_bp.route('/stock/payment/<int:product_id>', methods=['PUT'])
@token_required
@cross_origin(origin="http://localhost:3000", supports_credentials=True)
def update_payment_status(current_user, product_id):
    if current_user.role != 'admin':
        return jsonify({'message': 'Permission denied'}), 403

    product = Product.query.get_or_404(product_id)
    data = request.get_json()

    payment_status = data.get('payment_status')
    if payment_status not in ['paid', 'not paid']:
        return jsonify({'message': 'Invalid payment status'}), 400

    product.payment_status = payment_status
    db.session.commit()

    return jsonify({'message': f'Payment status updated to {payment_status}'}), 200

# Admin Deletes Stock
@store_bp.route('/stock/<int:product_id>', methods=['DELETE'])
@token_required
@cross_origin(origin="http://localhost:3000", supports_credentials=True)
def delete_stock(current_user, product_id):
    if current_user.role != 'admin':
        return jsonify({'message': 'Permission denied'}), 403

    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()

    return jsonify({'message': 'Stock item deleted successfully'}), 200

# Admin Creates Store
@store_bp.route('/create', methods=['POST'])
@token_required
@cross_origin(origin="http://localhost:3000", supports_credentials=True)
def create_store(current_user):
    if current_user.role != 'admin':
        return jsonify({"message": "Permission denied"}), 403

    data = request.get_json()
    if not data or 'name' not in data or 'merchant_id' not in data:
        return jsonify({"message": "Missing name or merchant_id"}), 400

    merchant = User.query.get(data['merchant_id'])
    if not merchant or merchant.role != 'merchant':
        return jsonify({"message": "Invalid merchant ID"}), 400

    new_store = Store(name=data['name'], merchant_id=merchant.id)
    db.session.add(new_store)
    db.session.commit()

    return jsonify({"message": "Store created successfully", "store_id": new_store.id}), 201

# Clerk Requests Stock
@store_bp.route('/request', methods=['POST'])
@token_required
@cross_origin(origin="http://localhost:3000", supports_credentials=True)
def request_stock(current_user):
    if current_user.role != 'clerk':
        return jsonify({'message': 'Permission denied'}), 403

    data = request.get_json()
    required_fields = ['product_name', 'store_id']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing field: {field}'}), 400

    if current_user.store_id != data['store_id']:
        return jsonify({'message': 'Unauthorized to request stock for this store'}), 403

    product = Product.query.filter_by(name=data['product_name'], store_id=data['store_id']).first()
    if not product:
        product = Product(
            name=data['product_name'],
            buying_price=0,  # Placeholder until updated
            selling_price=0,
            stock_quantity=0,
            store_id=data['store_id']
        )
        db.session.add(product)
        db.session.commit()

    supply_request = SupplyRequest(
        product_id=product.id,
        quantity_requested=10,  # Default, adjust via frontend if needed
        requested_by=current_user.id
    )
    db.session.add(supply_request)
    db.session.commit()

    return jsonify({'message': 'Stock request submitted successfully', 'request_id': supply_request.id}), 201