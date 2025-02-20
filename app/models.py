from app import db  # Import db from app/__init__.py

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    
    stores = db.relationship('Store', backref='merchant', lazy=True)
    supply_requests = db.relationship('SupplyRequest', backref='clerk', foreign_keys='SupplyRequest.requested_by')

    def __repr__(self):
        return f'<User {self.username}>'


class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    merchant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationships
    products = db.relationship('Product', backref='store', lazy=True)

    def __repr__(self):
        return f'<Store {self.name}>'


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    buying_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False)
    spoiled_quantity = db.Column(db.Integer, default=0)
    payment_status = db.Column(db.String(20), nullable=False, default='not paid')
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)

    # Relationships
    supply_requests = db.relationship('SupplyRequest', backref='product', lazy=True)

    def __repr__(self):
        return f'<Product {self.name}>'


class SupplyRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity_requested = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    requested_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<SupplyRequest {self.id} - {self.status}>'
