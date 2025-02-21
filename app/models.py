from app import db  # Import db from app/__init__.py

class User(db.Model):
    __tablename__ = "users"  # Explicit table name
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    # Specify foreign_keys to resolve ambiguity
    stores = db.relationship('Store', backref='merchant', lazy=True, foreign_keys='Store.merchant_id')
    supply_requests = db.relationship('SupplyRequest', backref='clerk', lazy=True, foreign_keys='SupplyRequest.requested_by')

    def __repr__(self):
        return f'<User {self.username}>'


class Store(db.Model):
    __tablename__ = "stores"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    # Foreign key to User (Merchant)
    merchant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationships
    products = db.relationship('Product', backref='store', lazy=True)

    def __repr__(self):
        return f'<Store {self.name}>'


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    buying_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False)
    spoiled_quantity = db.Column(db.Integer, default=0)
    payment_status = db.Column(db.String(20), nullable=False, default='not paid')

    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)

    # Relationships
    supply_requests = db.relationship('SupplyRequest', backref='product', lazy=True)

    def __repr__(self):
        return f'<Product {self.name}>'


class SupplyRequest(db.Model):
    __tablename__ = "supply_requests"
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity_requested = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')

    # Correct Foreign Key Reference
    requested_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f'<SupplyRequest {self.id} - {self.status}>'
