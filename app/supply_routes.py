from flask import Blueprint, jsonify, request
from app.models import SupplyRequest, Product, User
from app import db
from app.routes import token_required

supply_bp = Blueprint('supply', __name__)

# ✅ Clerk Requests Product Supply
@supply_bp.route('/supply/request', methods=['POST'])
@token_required
def request_supply(current_user):
    if current_user.role != 'clerk':
        return jsonify({'message': 'Permission denied'}), 403

    data = request.get_json()
    product_id = data.get('product_id')
    quantity_requested = data.get('quantity_requested')

    if not product_id or not quantity_requested:
        return jsonify({'message': 'Product ID and quantity are required'}), 400

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404

    new_request = SupplyRequest(product_id=product_id, quantity_requested=quantity_requested, requested_by=current_user.id)
    db.session.add(new_request)
    db.session.commit()

    return jsonify({'message': 'Supply request submitted successfully'}), 201

# ✅ Admin Views All Supply Requests
@supply_bp.route('/supply/requests', methods=['GET'])
@token_required
def view_supply_requests(current_user):
    if current_user.role != 'admin':
        return jsonify({'message': 'Permission denied'}), 403

    requests = SupplyRequest.query.all()

    return jsonify([{
        "id": req.id,
        "product_id": req.product_id,
        "quantity_requested": req.quantity_requested,
        "status": req.status,
        "requested_by": req.requested_by
    } for req in requests]), 200

# ✅ Admin Approves/Declines Supply Request
@supply_bp.route('/supply/request/<int:request_id>', methods=['PUT'])
@token_required
def update_supply_request(current_user, request_id):
    if current_user.role != 'admin':
        return jsonify({'message': 'Permission denied'}), 403

    request_data = request.get_json()
    new_status = request_data.get('status')

    if new_status not in ['approved', 'declined']:
        return jsonify({'message': 'Invalid status value'}), 400

    supply_request = SupplyRequest.query.get(request_id)
    if not supply_request:
        return jsonify({'message': 'Supply request not found'}), 404

    if new_status == 'approved':
        product = Product.query.get(supply_request.product_id)
        if product:
            product.stock_quantity += supply_request.quantity_requested  # Update stock
            db.session.commit()

    supply_request.status = new_status
    db.session.commit()

    return jsonify({'message': f'Supply request {new_status} successfully'}), 200
