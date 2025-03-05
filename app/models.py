from app import db
from datetime import datetime, timedelta
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # merchant, admin, clerk
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    store = db.relationship('Store', back_populates='merchant')
    supply_requests = db.relationship('SupplyRequest', backref='requesting_clerk', lazy=True)

    def __repr__(self):
        return f'<User {self.username} - {self.role}>'

class Store(db.Model):
    __tablename__ = "stores"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    merchant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    merchant = db.relationship('User', back_populates='store', foreign_keys=[merchant_id])
    products = db.relationship('Product', backref='store', lazy=True)
    supply_requests = db.relationship('SupplyRequest', backref='store', lazy=True)

    def __repr__(self):
        return f'<Store {self.name}>'

class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    buying_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    spoiled_quantity = db.Column(db.Integer, default=0)
    payment_status = db.Column(db.String(20), default="not paid")  # paid/not paid
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)
    supply_requests = db.relationship('SupplyRequest', backref='requested_product', lazy=True)

    def __repr__(self):
        return f'<Product {self.name} - Stock: {self.stock_quantity}>'

class SupplyRequest(db.Model):
    __tablename__ = "supply_requests"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity_requested = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, approved, declined
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)

    requested_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)

    def __repr__(self):
        return f'<SupplyRequest {self.id} - {self.status}>'
