from flask import Blueprint, jsonify, request, current_app
from app.models import Product, User, Store, SupplyRequest
from app import db  
from functools import wraps
import jwt

bp = Blueprint('main', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({'message': 'Token is missing!'}), 401

        token = auth_header.split("Bearer ")[1]

        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])

            if not current_user:
                return jsonify({'message': 'Invalid token!'}), 401

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

@bp.route('/report/store', methods=['GET'])
@token_required
def store_report(current_user):
    if current_user.role != 'admin':
        return jsonify({'message': 'Permission denied'}), 403

    stores = Store.query.all()
    report_data = []

    for store in stores:
        products = Product.query.filter_by(store_id=store.id).all()

        total_revenue = sum(p.selling_price * p.stock_quantity for p in products)
        total_stock = sum(p.stock_quantity for p in products)
        spoiled_stock = sum(p.spoiled_quantity for p in products)
        paid_count = sum(1 for p in products if p.payment_status == 'paid')
        unpaid_count = sum(1 for p in products if p.payment_status == 'not paid')

        report_data.append({
            "store_id": store.id,
            "store_name": store.name,
            "total_revenue": total_revenue,
            "total_stock": total_stock,
            "spoiled_stock": spoiled_stock,
            "payment_status": {
                "paid": paid_count,
                "unpaid": unpaid_count
            }
        })

    return jsonify({"store_performance": report_data}), 200

@bp.route('/report/products', methods=['GET'])
@token_required
def product_report(current_user):
    if current_user.role not in ['admin', 'merchant']:
        return jsonify({'message': 'Permission denied'}), 403

    products = Product.query.all()

    top_selling = sorted(products, key=lambda p: p.selling_price * p.stock_quantity, reverse=True)[:5]
    low_stock = sorted(products, key=lambda p: p.stock_quantity)[:5]
    spoiled = sorted(products, key=lambda p: p.spoiled_quantity, reverse=True)[:5]

    report_data = {
        "top_selling": [{"id": p.id, "name": p.name, "revenue": p.selling_price * p.stock_quantity} for p in top_selling],
        "low_stock": [{"id": p.id, "name": p.name, "stock_quantity": p.stock_quantity} for p in low_stock],
        "spoiled_products": [{"id": p.id, "name": p.name, "spoiled_quantity": p.spoiled_quantity} for p in spoiled]
    }

    return jsonify(report_data), 200
