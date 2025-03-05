import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash
from app import db
from app.models import User, Store  # ✅ Added Store import
from app.auth import auth_blueprint, token_required  
from app.store_routes import store_bp

# Load Environment Variables
load_dotenv()

# Initialize Flask App
app = Flask(__name__)

# Load Configurations
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "mysecretkey")

# Fix DATABASE_URL for PostgreSQL compatibility
db_url = os.getenv("DATABASE_URL", "sqlite:///myduka.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize Extensions
db.init_app(app)

# Enable CORS with proper preflight support
CORS(app, resources={
    r"/api/*": {
        "origins": "http://localhost:3000",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Authorization", "Content-Type", "x-access-token"]
    }
}, supports_credentials=True)

# Register Blueprints
app.register_blueprint(auth_blueprint, url_prefix="/api/auth")
app.register_blueprint(store_bp, url_prefix="/api/store")

# Initialize Database & Seed Default Data
def initialize_database():
    with app.app_context():
        db.create_all()

        # Check and create default merchant
        if not User.query.filter_by(role="merchant").first():
            hashed_password = generate_password_hash("defaultpassword", method="pbkdf2:sha256")
            merchant = User(
                username="defaultmerchant",
                email="merchant@example.com",
                password_hash=hashed_password,
                role="merchant",
                is_active=True
            )
            db.session.add(merchant)
            db.session.commit()
            print("✅ Default merchant created: merchant@example.com (password: defaultpassword)")

        # Seed a default store for testing
        if not Store.query.first():
            merchant = User.query.filter_by(role="merchant").first()
            store = Store(name="Default Store", merchant_id=merchant.id)
            db.session.add(store)
            db.session.commit()
            print("✅ Default store created: Default Store")

        # Seed a clerk tied to the store
        if not User.query.filter_by(role="clerk").first():
            store = Store.query.first()
            hashed_password = generate_password_hash("clerkpassword", method="pbkdf2:sha256")
            clerk = User(
                username="johnclerk",
                email="john@clerk.com",
                password_hash=hashed_password,
                role="clerk",
                store_id=store.id,
                is_active=True
            )
            db.session.add(clerk)
            db.session.commit()
            print("✅ Default clerk created: john@clerk.com (password: clerkpassword)")

# Protected Route (Test API)
@app.route("/api/protected-endpoint", methods=["GET"])
@token_required  # Assuming token_required is defined in auth.py
def protected(current_user):
    return jsonify({"message": f"Protected data for {current_user.email}!"})

# Handle 404 Errors
@app.errorhandler(404)
def not_found(error):
    return jsonify({"message": "Resource not found"}), 404

# Handle 500 Errors
@app.errorhandler(500)
def server_error(error):
    return jsonify({"message": "Internal server error"}), 500

# Run Server
if __name__ == "__main__":
    initialize_database()  # Run initialization
    port = int(os.getenv("PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "True").lower() in ["true", "1"]
    app.run(host="0.0.0.0", port=port, debug=debug_mode)