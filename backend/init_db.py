import os
import sys

from app import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.models import db, User, Outlet, FoodItem

def init_database():
    with app.app_context():
        # Drop all tables (use carefully!)
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        # Create default admin user
        admin = User(
            username='admin',
            email='admin@restaurant.com',
            role='admin'
        )
        admin.set_password('admin123')  # Change in production!
        db.session.add(admin)
        
        # Create sample outlet
        outlet = Outlet(
            name='Main Branch',
            location='Downtown'
        )
        db.session.add(outlet)
        
        # Create sample food items
        food_items = [
            FoodItem(name='Burger', category='main', unit_price=8.99),
            FoodItem(name='Pizza', category='main', unit_price=12.99),
            FoodItem(name='Salad', category='appetizer', unit_price=6.99),
            FoodItem(name='Coffee', category='beverage', unit_price=3.99),
        ]
        db.session.add_all(food_items)
        
        db.session.commit()
        print("✅ Database initialized successfully!")

if __name__ == '__main__':
    init_database()