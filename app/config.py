import os
from dotenv import load_dotenv

# ✅ Ensure .env file is loaded
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print("⚠️ Warning: .env file not found!")

class Config:
    """Base configuration with default settings."""
    
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback_secret_key')  
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///default.db')

    # ✅ Fix PostgreSQL URL format
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL

    BCRYPT_LOG_ROUNDS = int(os.getenv('BCRYPT_LOG_ROUNDS', 12))  # Password hashing rounds
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)  # Use same SECRET_KEY for JWT if not set

    DEBUG = False  

class DevelopmentConfig(Config):
    """Configuration for development environment."""
    
    DEBUG = True
    SQLALCHEMY_ECHO = True  

class ProductionConfig(Config):
    """Configuration for production environment."""
    
    DEBUG = False
    SQLALCHEMY_ECHO = False 

class TestingConfig(Config):
    """Configuration for testing environment."""
    
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  
    BCRYPT_LOG_ROUNDS = 4  

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
