from flask import Blueprint, request, jsonify
from backend.database.models import db, Recipe, Ingredient, FoodItem, Forecast
from backend.services.inventory_planner import InventoryPlanner
from backend.services.supplier_manager import SupplierManager
from backend.services.waste_tracker import WasteTracker
from backend.services.alert_manager import AlertManager

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/suggestions/<int:forecast_id>', methods=['GET'])
def get_inventory_suggestions(forecast_id):
    try:
        # 1. Fetch the forecast metadata
        forecast = db.session.query(Forecast).get(forecast_id)
        if not forecast:
            return jsonify({'error': 'Forecast not found'}), 404
        
        # 2. Initialize the Planner service
        planner = InventoryPlanner(forecast.outlet_id)
        
        # 3. Calculate requirements and get shopping list
        # get_shopping_list() calls calculate_requirements() internally
        shopping_list = planner.get_shopping_list(forecast_id)
        
        # 5. Get supplier recommendations
        supplier_manager = SupplierManager()
        purchase_orders = supplier_manager.generate_purchase_order(
            shopping_list['items']
        )
        
        # 6. Return the JSON response
        return jsonify({
            'success': True,
            'forecast_id': forecast_id,
            'outlet_id': forecast.outlet_id,
            'shopping_list': shopping_list,
            'purchase_orders': purchase_orders,
            'total_ingredients_monitored': len(shopping_list['items'])
        }), 200
        
    except Exception as e:
        print(f"❌ API Error: {str(e)}") 
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/recipes', methods=['POST'])
def add_recipe():
    """
    Add or update recipe
    
    POST /api/inventory/recipes
    Body: {
        "food_item_id": 1,
        "ingredients": [
            {"ingredient_id": 1, "quantity": 150},
            {"ingredient_id": 2, "quantity": 1}
        ]
    }
    """
    try:
        data = request.get_json()
        food_item_id = data.get('food_item_id')
        ingredients = data.get('ingredients', [])
        
        if not food_item_id or not ingredients:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Verify food item exists
        food_item = db.session.query(FoodItem).get(food_item_id)
        if not food_item:
            return jsonify({'error': 'Food item not found'}), 404
        
        # Delete existing recipes
        db.session.query(Recipe).filter_by(food_item_id=food_item_id).delete()
        
        # Add new recipes
        for ing in ingredients:
            recipe = Recipe(
                food_item_id=food_item_id,
                ingredient_id=ing['ingredient_id'],
                quantity_needed=ing['quantity']
            )
            db.session.add(recipe)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Recipe updated for {food_item.name}',
            'ingredients_count': len(ingredients)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@inventory_bp.route('/recipes/<int:item_id>', methods=['GET'])
def get_recipe(item_id):
    """
    Get recipe for food item
    
    GET /api/inventory/recipes/1
    """
    try:
        # Get food item
        food_item = db.session.query(FoodItem).get(item_id)
        if not food_item:
            return jsonify({'error': 'Food item not found'}), 404
        
        # Get recipe
        recipes = db.session.query(Recipe, Ingredient).join(
            Ingredient, Recipe.ingredient_id == Ingredient.id
        ).filter(Recipe.food_item_id == item_id).all()
        
        if not recipes:
            return jsonify({
                'food_item': food_item.name,
                'recipe': []
            }), 200
        
        recipe_data = []
        for recipe, ingredient in recipes:
            recipe_data.append({
                'ingredient_id': ingredient.id,
                'ingredient_name': ingredient.name,
                'quantity': recipe.quantity_needed,
                'unit': ingredient.unit
            })
        
        return jsonify({
            'food_item_id': food_item.id,
            'food_item': food_item.name,
            'recipe': recipe_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@inventory_bp.route('/adjust', methods=['POST'])
def adjust_quantity():
    """
    Manually adjust suggested quantities
    
    POST /api/inventory/adjust
    Body: {
        "forecast_id": 123,
        "adjustments": [
            {"ingredient": "Beef Patty", "new_quantity": 6000}
        ]
    }
    """
    try:
        data = request.get_json()
        forecast_id = data.get('forecast_id')
        adjustments = data.get('adjustments', [])
        
        # This would update the suggestions in the database
        # For now, just return the adjusted values
        
        return jsonify({
            'success': True,
            'message': 'Quantities adjusted',
            'adjustments_count': len(adjustments)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@inventory_bp.route('/waste/log', methods=['POST'])
def log_waste():
    """
    Log waste
    
    POST /api/inventory/waste/log
    Body: {
        "outlet_id": 1,
        "ingredient_id": 1,
        "quantity": 500,
        "reason": "expired"
    }
    """
    try:
        data = request.get_json()
        
        tracker = WasteTracker(data['outlet_id'])
        waste_id = tracker.log_waste(
            ingredient_id=data['ingredient_id'],
            quantity=data['quantity'],
            reason=data.get('reason', '')
        )
        
        return jsonify({
            'success': True,
            'waste_id': waste_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@inventory_bp.route('/waste/analysis/<int:outlet_id>', methods=['GET'])
def get_waste_analysis(outlet_id):
    """
    Get waste analysis
    
    GET /api/inventory/waste/analysis/1?days=30
    """
    try:
        days = request.args.get('days', 30, type=int)
        
        tracker = WasteTracker(outlet_id)
        analysis = tracker.analyze_waste_patterns(days_back=days)
        recommendations = tracker.get_waste_reduction_recommendations()
        
        return jsonify({
            'analysis': analysis,
            'recommendations': recommendations
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@inventory_bp.route('/alerts/<int:outlet_id>', methods=['GET'])
def get_alerts(outlet_id):
    """Get active alerts"""
    try:
        manager = AlertManager(outlet_id)
        alerts = manager.get_active_alerts()
        
        return jsonify({
            'outlet_id': outlet_id,
            'alert_count': len(alerts),
            'alerts': alerts
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@inventory_bp.route('/alerts/check/<int:outlet_id>', methods=['POST'])
def check_and_generate_alerts(outlet_id):
    """Check stock and generate alerts"""
    try:
        manager = AlertManager(outlet_id)
        
        # Check stock levels
        stock_alerts = manager.check_stock_levels()
        
        # Check vs forecast if provided
        forecast_id = request.get_json().get('forecast_id')
        demand_alerts = []
        
        if forecast_id:
            demand_alerts = manager.check_upcoming_demand(forecast_id)
        
        total_alerts = stock_alerts + demand_alerts
        
        return jsonify({
            'success': True,
            'alerts_generated': len(total_alerts),
            'stock_alerts': len(stock_alerts),
            'demand_alerts': len(demand_alerts)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@inventory_bp.route('/ingredients', methods=['GET'])
def get_all_ingredients():
    """
    Get all ingredients
    
    GET /api/inventory/ingredients
    """
    try:
        ingredients = db.session.query(Ingredient).all()
        
        result = []
        for ing in ingredients:
            result.append({
                'id': ing.id,
                'name': ing.name,
                'unit': ing.unit,
                'current_stock': ing.current_stock,
                'reorder_level': ing.reorder_level,
                'unit_cost': ing.unit_cost
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500