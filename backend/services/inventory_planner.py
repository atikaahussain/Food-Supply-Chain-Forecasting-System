import math
from datetime import datetime
from backend.database.models import (db, Ingredient, Recipe, ItemForecast, 
                            FoodItem, InventorySuggestion, Forecast)

class InventoryPlanner:
    """Calculate inventory requirements based on demand forecasts"""
    
    def __init__(self, outlet_id):
        self.outlet_id = outlet_id
        self.safety_buffer = 0.15  # 15% safety stock
    
    def calculate_requirements(self, forecast_id):
        """
        Calculate ingredient requirements based on forecast
        
        Args:
            forecast_id: ID of the forecast to use
        
        Returns:
            dict with ingredient requirements
        """
        print(f"\n{'='*60}")
        print(f"CALCULATING INVENTORY REQUIREMENTS")
        print(f"Forecast ID: {forecast_id}")
        print(f"{'='*60}\n")
        
        # Get item-level forecasts
        item_forecasts = db.session.query(ItemForecast, FoodItem).join(
            FoodItem, ItemForecast.food_item_id == FoodItem.id
        ).filter(ItemForecast.forecast_id == forecast_id).all()
        
        if not item_forecasts:
            raise ValueError(f"No item forecasts found for forecast {forecast_id}")
        
        # Dictionary to store total ingredient needs
        ingredient_requirements = {}
        
        # Calculate for each predicted food item
        for item_forecast, food_item in item_forecasts:
            predicted_quantity = item_forecast.predicted_quantity
            
            print(f"📦 {food_item.name}: {predicted_quantity} units predicted")
            
            # Get recipe for this food item
            recipes = db.session.query(Recipe, Ingredient).join(
                Ingredient, Recipe.ingredient_id == Ingredient.id
            ).filter(Recipe.food_item_id == food_item.id).all()
            
            if not recipes:
                print(f"   ⚠️  No recipe found, skipping...")
                continue
            
            # Calculate ingredients needed
            for recipe, ingredient in recipes:
                quantity_per_unit = recipe.quantity_needed
                total_needed = predicted_quantity * quantity_per_unit
                
                if ingredient.name not in ingredient_requirements:
                    ingredient_requirements[ingredient.name] = {
                        'ingredient_id': ingredient.id,
                        'total_needed': 0,
                        'unit': ingredient.unit,
                        'current_stock': ingredient.current_stock,
                        'unit_cost': ingredient.unit_cost,
                        'breakdown': []
                    }
                
                ingredient_requirements[ingredient.name]['total_needed'] += total_needed
                ingredient_requirements[ingredient.name]['breakdown'].append({
                    'food_item': food_item.name,
                    'quantity': total_needed
                })
                
                print(f"   - {ingredient.name}: {total_needed:.1f} {ingredient.unit}")
        
        # Apply safety buffer and calculate order quantities
        final_requirements = self._apply_safety_buffer_and_round(ingredient_requirements)
        
        # Save to database
        self._save_suggestions(forecast_id, final_requirements)
        
        return final_requirements
    
    def _apply_safety_buffer_and_round(self, requirements):
        """
        Add safety stock buffer and round to practical quantities
        
        Args:
            requirements: dict of ingredient requirements
        
        Returns:
            dict with adjusted requirements
        """
        print(f"\n📊 Applying safety buffer ({self.safety_buffer*100}%) and rounding...")
        
        final_requirements = {}
        
        for ingredient_name, details in requirements.items():
            base_needed = details['total_needed']
            current_stock = details['current_stock']
            
            # Add safety buffer
            with_buffer = base_needed * (1 + self.safety_buffer)
            
            # Subtract current stock
            net_needed = max(0, with_buffer - current_stock)
            
            # Round to practical quantities
            unit = details['unit']
            rounded_quantity = self._round_to_practical_quantity(net_needed, unit)
            
            # Calculate cost
            total_cost = rounded_quantity * details['unit_cost']
            
            final_requirements[ingredient_name] = {
                'ingredient_id': details['ingredient_id'],
                'base_needed': round(base_needed, 2),
                'with_buffer': round(with_buffer, 2),
                'current_stock': round(current_stock, 2),
                'net_to_order': round(net_needed, 2),
                'suggested_order': rounded_quantity,
                'unit': unit,
                'unit_cost': details['unit_cost'],
                'total_cost': round(total_cost, 2),
                'breakdown': details['breakdown']
            }
            
            print(f"\n{ingredient_name}:")
            print(f"  Base needed: {base_needed:.1f} {unit}")
            print(f"  With buffer: {with_buffer:.1f} {unit}")
            print(f"  Current stock: {current_stock:.1f} {unit}")
            print(f"  ✅ Order: {rounded_quantity:.1f} {unit} (${total_cost:.2f})")
        
        return final_requirements
    
    def _round_to_practical_quantity(self, quantity, unit):
        """
        Round to practical ordering quantities
        
        Examples:
            - Grams: round to nearest 500g
            - Pieces: round to nearest 10
            - Liters: round to nearest 1L
        """
        if unit in ['g', 'ml']:
            # Round to nearest 500g/ml (half kg/liter)
            return math.ceil(quantity / 500) * 500
        elif unit in ['kg', 'l']:
            # Round to nearest whole unit
            return math.ceil(quantity)
        elif unit == 'pieces':
            # Round to nearest 10 pieces
            return math.ceil(quantity / 10) * 10
        else:
            return math.ceil(quantity)
    
    def _save_suggestions(self, forecast_id, requirements):
        """Save inventory suggestions to database"""
        
        # Delete old suggestions for this forecast
        db.session.query(InventorySuggestion).filter(
            InventorySuggestion.forecast_id == forecast_id
        ).delete()
        
        # Add new suggestions
        for ingredient_name, details in requirements.items():
            suggestion = InventorySuggestion(
                forecast_id=forecast_id,
                raw_material=ingredient_name,
                suggested_quantity=details['suggested_order'],
                unit=details['unit']
            )
            db.session.add(suggestion)
        
        db.session.commit()
        print(f"\n💾 Inventory suggestions saved to database")
    
    def get_shopping_list(self, forecast_id):
        """
        Generate formatted shopping list
        
        Returns:
            list of dicts with shopping items
        """
        requirements = self.calculate_requirements(forecast_id)
        
        shopping_list = []
        total_cost = 0
        
        for ingredient_name, details in requirements.items():
            if details['net_to_order'] > 0:  # Only items that need ordering
                item = {
                    'ingredient': ingredient_name,
                    'quantity': details['suggested_order'],
                    'unit': details['unit'],
                    'cost': details['total_cost']
                }
                shopping_list.append(item)
                total_cost += details['total_cost']
        
        return {
            'items': shopping_list,
            'total_items': len(shopping_list),
            'total_cost': round(total_cost, 2)
        }
    
    def adjust_safety_buffer(self, new_buffer):
        """
        Adjust safety stock buffer percentage
        
        Args:
            new_buffer: float between 0 and 1 (e.g., 0.15 = 15%)
        """
        if 0 <= new_buffer <= 1:
            self.safety_buffer = new_buffer
            print(f"✅ Safety buffer updated to {new_buffer*100}%")
        else:
            raise ValueError("Buffer must be between 0 and 1")


# Test the planner
if __name__ == '__main__':
    from backend.app import app
    
    with app.app_context():
        # First generate a forecast
        from backend.services.forecasting_engine import ForecastEngine
        from backend.services.item_forecaster import ItemLevelForecaster
        
        print("Generating forecast first...")
        engine = ForecastEngine(outlet_id=1)
        forecast_result = engine.generate_forecast(model_type='auto', days_ahead=7)
        
        item_forecaster = ItemLevelForecaster(outlet_id=1)
        item_forecaster.forecast_all_items(forecast_result['forecast_id'])
        
        # Now calculate inventory
        planner = InventoryPlanner(outlet_id=1)
        requirements = planner.calculate_requirements(forecast_result['forecast_id'])
        
        # Get shopping list
        shopping_list = planner.get_shopping_list(forecast_result['forecast_id'])
        print("\n📝 SHOPPING LIST:")
        print(f"   Total items: {shopping_list['total_items']}")
        print(f"   Total cost: ${shopping_list['total_cost']}")