from flask import Blueprint, jsonify, request
from app.models import User, InviteToken
from app import db
from app.routes import token_required
from datetime import datetime, timedelta
import jwt
import os
import secrets

user_bp = Blueprint('user', __name__)

# ✅ Merchant Invites Admins (Tokenized)
@user_bp.route('/invite/admin', methods=['POST'])
@token_required
def invite_admin(current_user):
    if current_user.role != 'merchant':
        return jsonify({'message': 'Permission denied'}), 403

    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'message': 'Email is required'}), 400

    token = secrets.token_hex(16)
    expires_at = datetime.utcnow() + timedelta(days=2)

    invite = InviteToken(token=token, email=email, role='admin', expires_at=expires_at)
    db.session.add(invite)
    db.session.commit()

    return jsonify({'message': 'Admin invite sent!', 'token': token}), 200

# ✅ Admin Adds Clerks
@user_bp.route('/user/clerk', methods=['POST'])
@token_required
def add_clerk(current_user):
    if current_user.role != 'admin':
        return jsonify({'message': 'Permission denied'}), 403

    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password_hash = data.get('password_hash')

    if not all([username, email, password_hash]):
        return jsonify({'message': 'Missing required fields'}), 400

    new_clerk = User(username=username, email=email, password_hash=password_hash, role='clerk')
    db.session.add(new_clerk)
    db.session.commit()

    return jsonify({'message': 'Clerk added successfully'}), 201

# ✅ View Users Based on Role
@user_bp.route('/users', methods=['GET'])
@token_required
def get_users(current_user):
    role_filter = request.args.get('role', None)

    if current_user.role not in ['merchant', 'admin']:
        return jsonify({'message': 'Permission denied'}), 403

    query = User.query
    if role_filter:
        query = query.filter_by(role=role_filter)

    users = query.all()

    return jsonify([{
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active
    } for user in users]), 200

# ✅ Activate/Deactivate User (Admin)
@user_bp.route('/user/<int:user_id>/status', methods=['PUT'])
@token_required
def update_user_status(current_user, user_id):
    if current_user.role != 'admin':
        return jsonify({'message': 'Permission denied'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    data = request.get_json()
    new_status = data.get('is_active')

    if new_status is None:
        return jsonify({'message': 'Invalid status value'}), 400

    user.is_active = new_status
    db.session.commit()

    return jsonify({'message': f'User status updated to {"active" if new_status else "inactive"}'}), 200

# ✅ Delete User (Merchant/Admin)
@user_bp.route('/user/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(current_user, user_id):
    if current_user.role not in ['merchant', 'admin']:
        return jsonify({'message': 'Permission denied'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'User deleted successfully'}), 200
