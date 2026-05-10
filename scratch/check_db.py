from backend.app import app
from backend.database.models import db, FoodItem, Ingredient, Recipe

with app.app_context():
    print("--- Food Items ---")
    items = FoodItem.query.all()
    for item in items:
        print(f"ID: {item.id}, Name: {item.name}")
    
    print("\n--- Ingredients ---")
    ings = Ingredient.query.all()
    for ing in ings:
        print(f"ID: {ing.id}, Name: {ing.name}")

    print("\n--- Recipes ---")
    recipes = db.session.query(Recipe, FoodItem, Ingredient).join(FoodItem).join(Ingredient).all()
    for r, f, i in recipes:
        print(f"Food: {f.name}, Ingredient: {i.name}, Qty: {r.quantity_needed}")
