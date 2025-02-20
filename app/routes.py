from flask import Blueprint, jsonify, request, current_app
from .models import Product, SupplyRequest, User
from app import db  
from functools import wraps
import jwt  

bp = Blueprint('main', __name__)

# Token authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['id']).first()
            
            if not current_user:
                return jsonify({'message': 'Invalid token!'}), 401

            print("Decoded Token:", data)  

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401

        return f(current_user, *args, **kwargs)
    
    return decorated

# Add Product (Clerk & Admin)
@bp.route('/product', methods=['POST'])
@token_required
def add_product(current_user):
    if current_user.role not in ['clerk', 'admin']:  
        return jsonify({'message': 'Permission denied'}), 403
    data = request.get_json()
    new_product = Product(
        name=data['name'],
        buying_price=data['buying_price'],
        selling_price=data['selling_price'],
        stock_quantity=data['stock_quantity'],
        payment_status=data.get('payment_status', 'not paid'),
        spoiled_quantity=data.get('spoiled_quantity', 0),
        store_id=data['store_id']
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message': 'Product added!'}), 201

# Update Product (Clerk & Admin)
@bp.route('/product/<int:id>', methods=['PUT'])
@token_required
def update_product(current_user, id):
    if current_user.role not in ['clerk', 'admin']:
        return jsonify({'message': 'Permission denied'}), 403
    product = Product.query.get_or_404(id)
    data = request.get_json()
    product.name = data.get('name', product.name)
    product.buying_price = data.get('buying_price', product.buying_price)
    product.selling_price = data.get('selling_price', product.selling_price)
    product.stock_quantity = data.get('stock_quantity', product.stock_quantity)
    product.payment_status = data.get('payment_status', product.payment_status)
    product.spoiled_quantity = data.get('spoiled_quantity', product.spoiled_quantity)
    db.session.commit()
    return jsonify({'message': 'Product updated!'}), 200

# Request Supply (Clerk Only)
@bp.route('/request_supply', methods=['POST'])
@token_required
def request_supply(current_user):
    if current_user.role != 'clerk':
        return jsonify({'message': 'Permission denied'}), 403
    data = request.get_json()
    new_request = SupplyRequest(
        product_id=data['product_id'],
        quantity_requested=data['quantity'],
        status='pending',
        requested_by=current_user.id
    )
    db.session.add(new_request)
    db.session.commit()
    return jsonify({'message': 'Supply request created!'}), 201

# Manage Supply Request (Admin Only)
@bp.route('/supply_request/<int:id>', methods=['PUT'])
@token_required
def manage_supply_request(current_user, id):
    if current_user.role != 'admin':
        return jsonify({'message': 'Permission denied'}), 403
    supply_request = SupplyRequest.query.get_or_404(id)
    data = request.get_json()
    action = data.get('action')
    if action == 'approve':
        supply_request.status = 'approved'
        product = Product.query.get(supply_request.product_id)
        product.stock_quantity += supply_request.quantity_requested
    elif action == 'decline':
        supply_request.status = 'declined'
    else:
        return jsonify({'message': 'Invalid action'}), 400
    db.session.commit()
    return jsonify({'message': f'Supply request {supply_request.status}!'}), 200

# Generate Reports (Admin & Merchant)
@bp.route('/report', methods=['GET'])
@token_required
def generate_report(current_user):
    if current_user.role not in ['admin', 'merchant']:
        return jsonify({'message': 'Permission denied'}), 403
    period = request.args.get('period', 'monthly')
    if period == 'weekly':
        products = Product.query.all()
        report = {
            'total_products': len(products),
            'total_stock': sum(p.stock_quantity for p in products),
            'total_spoiled': sum(p.spoiled_quantity for p in products),
            'paid': sum(1 for p in products if p.payment_status == 'paid'),
            'unpaid': sum(1 for p in products if p.payment_status == 'not paid')
        }
    elif period == 'monthly':
        report = {'message': 'Monthly report placeholder'}
    elif period == 'annual':
        report = {'message': 'Annual report placeholder'}
    else:
        return jsonify({'message': 'Invalid period'}), 400
    return jsonify(report), 200

# Update Payment Status (Admin Only)
@bp.route('/product/<int:id>/payment', methods=['PUT'])
@token_required
def update_payment_status(current_user, id):
    if current_user.role != 'admin':
        return jsonify({'message': 'Permission denied'}), 403
    product = Product.query.get_or_404(id)
    data = request.get_json()
    product.payment_status = data.get('payment_status', product.payment_status)
    db.session.commit()
    return jsonify({'message': 'Payment status updated!'}), 200
# Get All Products (Admin & Clerk)
@bp.route('/products', methods=['GET'])
@token_required
def get_products(current_user):
    if current_user.role not in ['clerk', 'admin']:  # ✅ Ensure only authorized users can access
        return jsonify({'message': 'Permission denied'}), 403
    
    products = Product.query.all()
    product_list = [{
        "id": product.id,
        "name": product.name,
        "buying_price": product.buying_price,
        "selling_price": product.selling_price,
        "stock_quantity": product.stock_quantity,
        "spoiled_quantity": product.spoiled_quantity,
        "payment_status": product.payment_status,
        "store_id": product.store_id
    } for product in products]

    return jsonify(product_list), 200
@bp.route('/', methods=['GET'])
def home():
    return jsonify({'message': 'API is running!'}), 200

