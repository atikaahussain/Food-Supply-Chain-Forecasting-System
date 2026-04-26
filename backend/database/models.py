from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'manager', 'staff'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Outlet(db.Model):
    __tablename__ = 'outlets'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sales = db.relationship('Sales', backref='outlet', lazy=True)
    forecasts = db.relationship('Forecast', backref='outlet', lazy=True)

class FoodItem(db.Model):
    __tablename__ = 'food_items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))  # appetizer, main, dessert, beverage
    unit_price = db.Column(db.Float)
    
    # Relationships
    sales = db.relationship('Sales', backref='food_item', lazy=True)

class Sales(db.Model):
    __tablename__ = 'sales'
    
    id = db.Column(db.Integer, primary_key=True)
    outlet_id = db.Column(db.Integer, db.ForeignKey('outlets.id'), nullable=False)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_items.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    customer_count = db.Column(db.Integer)
    quantity_sold = db.Column(db.Integer, nullable=False)
    revenue = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Forecast(db.Model):
    __tablename__ = 'forecasts'
    
    id = db.Column(db.Integer, primary_key=True)
    outlet_id = db.Column(db.Integer, db.ForeignKey('outlets.id'), nullable=False)
    forecast_date = db.Column(db.Date, nullable=False)
    predicted_customers = db.Column(db.Integer)
    confidence_level = db.Column(db.Float)  # 0.0 to 1.0
    model_used = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    item_forecasts = db.relationship('ItemForecast', backref='forecast', lazy=True)
    inventory_suggestions = db.relationship('InventorySuggestion', backref='forecast', lazy=True)

class ItemForecast(db.Model):
    __tablename__ = 'item_forecasts'
    
    id = db.Column(db.Integer, primary_key=True)
    forecast_id = db.Column(db.Integer, db.ForeignKey('forecasts.id'), nullable=False)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_items.id'), nullable=False)
    predicted_quantity = db.Column(db.Integer, nullable=False)
    
    food_item = db.relationship('FoodItem')

class InventorySuggestion(db.Model):
    __tablename__ = 'inventory_suggestions'
    
    id = db.Column(db.Integer, primary_key=True)
    forecast_id = db.Column(db.Integer, db.ForeignKey('forecasts.id'), nullable=False)
    raw_material = db.Column(db.String(100), nullable=False)
    suggested_quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20))  # kg, liters, pieces

class ModelMetadata(db.Model):
    __tablename__ = 'model_metadata'
    
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(50), nullable=False)
    version = db.Column(db.String(20))
    accuracy_score = db.Column(db.Float)
    trained_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)