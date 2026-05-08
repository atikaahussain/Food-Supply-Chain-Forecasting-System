import sys
from pathlib import Path
import pandas as pd

# Ensure repo root is on sys.path when running as a script
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.app import app
from backend.database.models import db, Ingredient, Recipe, FoodItem, Supplier
from datetime import datetime

def add_phase5_tables():
    """Add Phase 5 tables and map recipes using meal_info.csv"""
    
    with app.app_context():
        # 1. Create the new tables in Neon
        db.create_all()
        print("✅ Phase 5 tables created/verified")

        # 2. Define a comprehensive list of Ingredients
        ingredients_data = [
            {'name': 'Beef Patty', 'unit': 'pieces', 'unit_cost': 1.50, 'current_stock': 500, 'reorder_level': 100},
            {'name': 'Burger Bun', 'unit': 'pieces', 'unit_cost': 0.50, 'current_stock': 600, 'reorder_level': 100},
            {'name': 'Rice', 'unit': 'g', 'unit_cost': 0.002, 'current_stock': 50000, 'reorder_level': 10000},
            {'name': 'Chicken Breast', 'unit': 'g', 'unit_cost': 0.01, 'current_stock': 20000, 'reorder_level': 5000},
            {'name': 'Pasta Noodles', 'unit': 'g', 'unit_cost': 0.003, 'current_stock': 15000, 'reorder_level': 3000},
            {'name': 'Mozzarella Cheese', 'unit': 'g', 'unit_cost': 0.012, 'current_stock': 10000, 'reorder_level': 2000},
            {'name': 'Tomato Sauce', 'unit': 'ml', 'unit_cost': 0.008, 'current_stock': 10000, 'reorder_level': 2000},
            {'name': 'Pizza Dough', 'unit': 'g', 'unit_cost': 0.005, 'current_stock': 20000, 'reorder_level': 5000},
            {'name': 'Coffee Beans', 'unit': 'g', 'unit_cost': 0.02, 'current_stock': 5000, 'reorder_level': 1000},
            {'name': 'Milk', 'unit': 'ml', 'unit_cost': 0.002, 'current_stock': 20000, 'reorder_level': 5000},
            {'name': 'Lettuce', 'unit': 'g', 'unit_cost': 0.005, 'current_stock': 5000, 'reorder_level': 1000},
            {'name': 'Cheese Slice', 'unit': 'pieces', 'unit_cost': 0.20, 'current_stock': 1000, 'reorder_level': 200},
            {'name': 'Spices Mix', 'unit': 'g', 'unit_cost': 0.05, 'current_stock': 2000, 'reorder_level': 500},
            {'name': 'Soy Sauce', 'unit': 'ml', 'unit_cost': 0.01, 'current_stock': 5000, 'reorder_level': 1000}
        ]

        # Save Ingredients to DB
        for ing_data in ingredients_data:
            if not Ingredient.query.filter_by(name=ing_data['name']).first():
                db.session.add(Ingredient(**ing_data))
        db.session.commit()
        print("✅ Ingredients catalog populated")

        # 3. Define Recipe Blueprints based on Category
        category_recipes = {
            'Pizza': [('Pizza Dough', 250), ('Tomato Sauce', 80), ('Mozzarella Cheese', 120)],
            'Rice Bowl': [('Rice', 200), ('Chicken Breast', 150), ('Soy Sauce', 15)],
            'Pasta': [('Pasta Noodles', 150), ('Tomato Sauce', 100), ('Cheese Slice', 1)],
            'Beverages': [('Coffee Beans', 15), ('Milk', 150)],
            'Biryani': [('Rice', 250), ('Chicken Breast', 200), ('Spices Mix', 10)],
            'Sandwich': [('Burger Bun', 2), ('Cheese Slice', 1), ('Lettuce', 20)],
            'Starters': [('Chicken Breast', 100), ('Spices Mix', 5)],
            'Salad': [('Lettuce', 150), ('Cheese Slice', 1)]
        }

        # 4. Load CSV and Map Recipes
        csv_path = 'data/raw/meal_info.csv'
        try:
            meal_df = pd.read_csv(csv_path)
            for _, row in meal_df.iterrows():
                m_id = int(row['meal_id'])
                cat = row['category']
                
                food_item = FoodItem.query.get(m_id)
                if food_item and cat in category_recipes:
                    # Rename for professional look
                    food_item.name = f"{cat} ({m_id})"
                    
                    for ing_name, qty in category_recipes[cat]:
                        ing = Ingredient.query.filter_by(name=ing_name).first()
                        if ing:
                            # Check if recipe link already exists
                            exists = Recipe.query.filter_by(food_item_id=m_id, ingredient_id=ing.id).first()
                            if not exists:
                                db.session.add(Recipe(food_item_id=m_id, ingredient_id=ing.id, quantity_needed=qty))
            
            db.session.commit()
            print(f"✅ Automated recipe mapping complete for {len(meal_df)} items")
        except Exception as e:
            print(f"⚠️ CSV Mapping failed: {e}. Check if data/raw/meal_info.csv exists.")

        # 5. Add Sample Suppliers
        suppliers = [
            {'name': 'Global Food Logistics', 'contact_person': 'Atika', 'email': 'atika@supply.com', 'delivery_days': 2},
            {'name': 'Fresh Farms Lahore', 'contact_person': 'Hussain', 'email': 'hussain@farm.com', 'delivery_days': 1}
        ]
        for s_data in suppliers:
            if not Supplier.query.filter_by(name=s_data['name']).first():
                db.session.add(Supplier(**s_data))
        
        db.session.commit()
        print("🎉 Phase 5 Database Initialization Finished!")

if __name__ == '__main__':
    add_phase5_tables()