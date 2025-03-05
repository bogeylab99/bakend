from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from dotenv import load_dotenv
import os


# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()

def create_app():
    app = Flask(__name__)

    # 🔹 Ensure environment variables are loaded
    database_url = os.getenv('DATABASE_URL')
    secret_key = os.getenv('SECRET_KEY')
    mail_username = os.getenv('MAIL_USERNAME')
    mail_password = os.getenv('MAIL_PASSWORD')

    if not all([database_url, secret_key, mail_username, mail_password]):
        raise ValueError("Missing required environment variables! Check your .env file.")

    # 🔹 Fix PostgreSQL database URL if needed
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    # Configurations
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = secret_key
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = mail_username
    app.config['MAIL_PASSWORD'] = mail_password

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # ✅ Register Blueprints (API Routes)
    from app.auth import auth_blueprint  
    app.register_blueprint(auth_blueprint, url_prefix='/api/auth')

    from app.routes import bp  
    app.register_blueprint(bp, url_prefix='/api')

    from app.graph_routes import graph_bp  
    app.register_blueprint(graph_bp, url_prefix='/api/graph')

    from app.store_routes import store_bp  # ✅ Removed stock_bp
    app.register_blueprint(store_bp, url_prefix='/api/store')

    return app
