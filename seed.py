import os
from app import create_app, db
from app.models import User, Store, Product
from werkzeug.security import generate_password_hash

# Initialize the Flask app
app = create_app()

# Seed Data
def seed_database():
    with app.app_context():
        # Ensure the database tables exist
        db.create_all()

        # Check if an admin already exists
        if not User.query.filter_by(role="admin").first():
            admin = User(
                username="admin",
                email="admin@example.com",
                password_hash=generate_password_hash("Admin@123"),  # Change as needed
                role="admin",
                is_active=True
            )
            db.session.add(admin)

        # Add sample stores
        store1 = Store(name="Store A", merchant_id=1)
        store2 = Store(name="Store B", merchant_id=1)
        db.session.add_all([store1, store2])

        # Add sample products
        product1 = Product(name="Laptop", buying_price=500, selling_price=700, stock_quantity=10, store_id=1)
        product2 = Product(name="Phone", buying_price=200, selling_price=300, stock_quantity=15, store_id=2)
        db.session.add_all([product1, product2])

        # Commit changes
        db.session.commit()
        print("✅ Database seeded successfully!")

# Run the seeding function
if __name__ == "__main__":
    seed_database()
