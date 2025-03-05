from flask import Blueprint, jsonify, request, current_app, make_response
from functools import wraps
import jwt
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from flask_cors import CORS, cross_origin
from app import db, mail
from app.models import User

# Define authentication Blueprint
auth_blueprint = Blueprint("auth", __name__)

# Enable CORS for all routes
CORS(auth_blueprint, resources={r"/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)

# Handle OPTIONS preflight requests
@auth_blueprint.route("/<path:path>", methods=["OPTIONS"])
def handle_options(path):
    response = make_response()
    response.status_code = 200
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, x-access-token"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

# Token authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == "OPTIONS":
            return make_response(), 200
        
        token = request.headers.get("x-access-token") or request.headers.get("Authorization")
        if not token:
            return jsonify({"message": "Token is missing!"}), 401

        if token.startswith("Bearer "):
            token = token.split(" ")[1]

        try:
            data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            current_user = User.query.get(data["user_id"])
            if not current_user:
                return jsonify({"message": "User not found!"}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token!"}), 401

        return f(current_user, *args, **kwargs)
    return decorated

# Fetch all Clerks (Only Admins & Merchants)
@auth_blueprint.route('/clerks', methods=['GET'])
@token_required
@cross_origin(origin="http://localhost:3000", supports_credentials=True)
def get_clerks(current_user):
    if current_user.role not in ['admin', 'merchant']:
        return jsonify({'message': 'Permission denied'}), 403

    clerks = User.query.filter_by(role='clerk').all()
    clerk_data = [{"id": c.id, "email": c.email, "store_id": c.store_id} for c in clerks]
    return jsonify(clerk_data), 200

# Register an Admin
@auth_blueprint.route("/register-admin", methods=["POST"])
@token_required
@cross_origin(origin="http://localhost:3000", supports_credentials=True)
def register_admin(current_user):
    if current_user.role not in ["merchant", "admin"]:
        return jsonify({"message": "Permission denied!"}), 403

    data = request.get_json()
    required_fields = ["username", "email", "password"]
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields!"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"message": "Email already exists!"}), 400

    hashed_password = generate_password_hash(data["password"], method="pbkdf2:sha256")
    new_admin = User(
        username=data["username"],
        email=data["email"],
        password_hash=hashed_password,
        role="admin",
        is_active=True,
    )
    db.session.add(new_admin)
    db.session.commit()
    return jsonify({"message": "Admin registered successfully!"}), 201

# Register a Clerk
@auth_blueprint.route("/register-clerk", methods=["POST"])
@token_required
@cross_origin(origin="http://localhost:3000", supports_credentials=True)
def register_clerk(current_user):
    if current_user.role != "admin":
        return jsonify({"message": "Permission denied!"}), 403

    data = request.get_json()
    required_fields = ["username", "email", "password", "store_id"]
    if not all(field in data for field in required_fields):
        print("❌ Missing required fields:", required_fields)
        return jsonify({"message": "Missing required fields!"}), 400

    if User.query.filter_by(email=data["email"]).first():
        print("❌ Email already exists!")
        return jsonify({"message": "Email already exists!"}), 400

    hashed_password = generate_password_hash(data["password"], method="pbkdf2:sha256")
    try:
        new_clerk = User(
            username=data["username"],
            email=data["email"],
            password_hash=hashed_password,
            role="clerk",
            store_id=data["store_id"],  # ✅ Added store_id support
            is_active=True,
        )
        db.session.add(new_clerk)
        db.session.commit()
        print("✅ Clerk registered successfully!")
        return jsonify({"message": "Clerk registered successfully!", "clerk_id": new_clerk.id}), 201
    except Exception as e:
        print("❌ Error registering clerk:", str(e))
        db.session.rollback()
        return jsonify({"message": "Internal server error", "error": str(e)}), 500

# User Login Route
@auth_blueprint.route('/login', methods=['POST'])
@cross_origin(origin="http://localhost:3000", supports_credentials=True)
def login():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'message': 'Missing email or password'}), 400

    user = User.query.filter_by(email=data['email']).first()
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'message': 'Invalid email or password'}), 401

    if not user.is_active:
        return jsonify({'message': 'Please verify your email before logging in!'}), 403

    token = jwt.encode(
        {'user_id': user.id, 'exp': datetime.utcnow() + timedelta(hours=1)},
        current_app.config['SECRET_KEY'],
        algorithm="HS256"
    )
    return jsonify({
        "access_token": token,
        "message": "Login successful",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "store_id": user.store_id if user.store_id else None
        }
    }), 200

# Logout Route (Optional, client-side token removal is sufficient in JWT)
@auth_blueprint.route('/logout', methods=['POST'])
@token_required
@cross_origin(origin="http://localhost:3000", supports_credentials=True)
def logout(current_user):
    # In a JWT system, logout is typically handled client-side by removing the token
    return jsonify({"message": "Logged out successfully (remove token client-side)"}), 200