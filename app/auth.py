from flask import Blueprint, jsonify, request, current_app
from functools import wraps
import jwt
from app.models import User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from datetime import datetime, timedelta
from app import db, mail  # Import mail and db correctly

auth_blueprint = Blueprint('auth', __name__)

# Middleware to protect routes
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
            if not current_user:
                return jsonify({'message': 'User not found!'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# Send verification email
def send_verification_email(user):
    token = jwt.encode(
        {'user_id': user.id, 'exp': datetime.utcnow() + timedelta(hours=24)},
        current_app.config['SECRET_KEY'], 
        algorithm="HS256"
    )
    link = f'http://localhost:5000/api/auth/confirm-email/{token}'
    msg = Message('Confirm your Email', sender=current_app.config['MAIL_USERNAME'], recipients=[user.email])
    msg.body = f'Please click this link to verify your email: {link}'
    
    try:
        mail.send(msg)
    except Exception as e:
        print("Email sending failed:", e)

# User Registration Route
@auth_blueprint.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # Validate request payload
    required_fields = ['username', 'email', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields!'}), 400

    # Check if email exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists'}), 400

    # Hash password
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')

    # Create new user (default role = "user")
    new_user = User(
        username=data['username'],
        email=data['email'],
        password_hash=hashed_password,
        role=data.get('role', 'user'),  # Default role is "user"
        is_active=False  # Mark inactive until email is verified
    )

    db.session.add(new_user)
    db.session.commit()

    # Send verification email
    send_verification_email(new_user)

    return jsonify({'message': 'User registered successfully! Please check your email to verify your account.'}), 201

# Email Verification Route
@auth_blueprint.route('/confirm-email/<token>', methods=['GET'])
def confirm_email(token):
    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        user = User.query.get(data['user_id'])

        if not user:
            return jsonify({'message': 'User not found!'}), 404

        user.is_active = True
        db.session.commit()

        return jsonify({'message': 'Email verified successfully!'}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Verification link expired!'}), 400
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token!'}), 400

# User Login Route
@auth_blueprint.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'message': 'Missing email or password'}), 400

    user = User.query.filter_by(email=data['email']).first()

    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'message': 'Invalid email or password'}), 401

    if not user.is_active:
        return jsonify({'message': 'Please verify your email before logging in!'}), 403

    # Generate JWT token
    token = jwt.encode(
        {'user_id': user.id, 'exp': datetime.utcnow() + timedelta(hours=1)},
        current_app.config['SECRET_KEY'],
        algorithm="HS256"
    )

    return jsonify({'access_token': token, 'message': 'Login successful'}), 200
