from flask import Blueprint, jsonify, request, current_app
from functools import wraps
import jwt
from app.models import User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from datetime import datetime, timedelta
from app import db, mail  # Import mail and db correctly


auth_blueprint = Blueprint('auth', __name__)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['id']).first()
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated


def send_verification_email(user):
    token = jwt.encode(
        {'id': user.id, 'exp': datetime.utcnow() + timedelta(hours=24)},
        current_app.config['SECRET_KEY'], 
        algorithm="HS256"
    )
    msg = Message('Confirm your Email', sender=current_app.config['MAIL_USERNAME'], recipients=[user.email])
    link = f'http://localhost:5000/api/auth/confirm-email/{token}'
    msg.body = f'Please click on this link to confirm your email: {link}'
    mail.send(msg)


@auth_blueprint.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or 'email' not in data:
        return jsonify({'message': 'Email is required'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists'}), 400

    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    new_user = User(username=data['username'], email=data['email'], password_hash=hashed_password, role='user')
    

    db.session.add(new_user)
    db.session.commit()
    
    
    send_verification_email(new_user)
    
    return jsonify({'message': 'User registered successfully! Please check your email to verify your account.'}), 201

