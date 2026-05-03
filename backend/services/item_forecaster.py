import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backend.database.models import db, Sales, FoodItem, ItemForecast, Forecast
from backend.models.linear_model import LinearForecastModel

class ItemLevelForecaster:
    """Forecast demand for individual food items"""
    
    def __init__(self, outlet_id):
        self.outlet_id = outlet_id
    
    def fetch_item_sales_history(self, food_item_id, days_back=180):
        """Fetch sales history for specific item"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        sales_query = db.session.query(Sales).filter(
            Sales.outlet_id == self.outlet_id,
            Sales.food_item_id == food_item_id,
            Sales.date >= start_date,
            Sales.date <= end_date
        ).order_by(Sales.date)
        
        data = []
        for sale in sales_query.all():
            data.append({
                'date': sale.date,
                'quantity_sold': sale.quantity_sold
            })
        
        return pd.DataFrame(data)
    
    def predict_item_demand(self, food_item_id, days_ahead=7):
        """Predict demand for specific food item"""
        # Fetch historical data
        df = self.fetch_item_sales_history(food_item_id)
        
        if len(df) < 30:  # Not enough data
            return self.use_category_average(food_item_id, days_ahead)
        
        # Aggregate by date
        daily_df = df.groupby('date').agg({'quantity_sold': 'sum'}).reset_index()
        daily_df['date'] = pd.to_datetime(daily_df['date'])
        daily_df = daily_df.sort_values('date')
        
        # Create features
        daily_df['day_of_week'] = daily_df['date'].dt.dayofweek
        daily_df['is_weekend'] = daily_df['day_of_week'].isin([5, 6]).astype(int)
        daily_df['lag_1'] = daily_df['quantity_sold'].shift(1)
        daily_df['lag_7'] = daily_df['quantity_sold'].shift(7)
        daily_df['rolling_mean_7'] = daily_df['quantity_sold'].rolling(7, min_periods=1).mean()
        
        daily_df = daily_df.bfill().fillna(0)     
           
        # Train simple model
        feature_cols = ['day_of_week', 'is_weekend', 'lag_1', 'lag_7', 'rolling_mean_7']
        X = daily_df[feature_cols]
        y = daily_df['quantity_sold']
        
        model = LinearForecastModel()
        model.train(X, y)
        
        # Predict next days
        predictions = []
        last_row = daily_df.iloc[-1].copy()
        
        for day in range(days_ahead):
            next_features = last_row[feature_cols].values.reshape(1, -1)
            pred = model.predict(next_features)[0]
            pred = max(0, int(pred))
            predictions.append(pred)
            
            # Update for next iteration
            last_row['lag_1'] = pred
            last_row['day_of_week'] = (last_row['day_of_week'] + 1) % 7
            last_row['is_weekend'] = 1 if last_row['day_of_week'] in [5, 6] else 0
        
        return predictions
    
    def use_category_average(self, food_item_id, days_ahead=7):
        """Use category average for new items with no history"""
        # Get item's category
        food_item = db.session.query(FoodItem).get(food_item_id)
        
        if not food_item:
            return [0] * days_ahead
        
        category = food_item.category
        
        # Get average sales for this category
        similar_items = db.session.query(FoodItem).filter(
            FoodItem.category == category
        ).all()
        
        if not similar_items:
            return [10] * days_ahead  # Default fallback
        
        # Calculate average from similar items
        total_sales = 0
        count = 0
        
        for item in similar_items:
            recent_sales = db.session.query(Sales).filter(
                Sales.food_item_id == item.id,
                Sales.outlet_id == self.outlet_id
            ).limit(30).all()
            
            for sale in recent_sales:
                total_sales += sale.quantity_sold
                count += 1
        
        avg_daily = int(total_sales / max(count, 1))
        
        return [avg_daily] * days_ahead
    
    def forecast_all_items(self, forecast_id, days_ahead=7):
        """Generate forecasts for all menu items"""
        print(f"\n🍽️  Generating item-level forecasts...")
        
        # Get all food items
        food_items = db.session.query(FoodItem).all()
        
        results = {}
        
        for item in food_items:
            predictions = self.predict_item_demand(item.id, days_ahead)
            
            # Save to database
            item_forecast = ItemForecast(
                forecast_id=forecast_id,
                food_item_id=item.id,
                predicted_quantity=predictions[0]  # Next day prediction
            )
            db.session.add(item_forecast)
            
            results[item.name] = {
                'next_day': predictions[0],
                'next_week': predictions
            }
            
            print(f"   {item.name}: {predictions[0]} units tomorrow")
        
        db.session.commit()
        print(f"✅ Item forecasts saved to database\n")
        
        return results


# Test
if __name__ == '__main__':
    from app import app
    
    with app.app_context():
        forecaster = ItemLevelForecaster(outlet_id=1)
        
        # Create a dummy forecast first
        from backend.services.forecasting_engine import ForecastEngine
        engine = ForecastEngine(1)
        result = engine.generate_forecast()
        
        # Forecast items
        item_results = forecaster.forecast_all_items(
            forecast_id=result['forecast_id']
        )
        print(item_results)
        
        
        
        
        
        
        
        
        
        
        
        
        
        