import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backend.database.models import Forecast, ItemForecast, FoodItem, ModelMetadata, db, Sales
from backend.models.linear_model import LinearForecastModel
from backend.models.arima_model import ARIMAForecastModel
from backend.models.xgboost_model import XGBoostForecastModel
from backend.models.lstm_model import LSTMForecastModel
import pickle
import os

class ForecastEngine:
    """Main forecasting engine that orchestrates model selection and prediction"""
    
    def __init__(self, outlet_id):
        self.outlet_id = outlet_id
        self.models = {}
        self.model_paths = {
            'linear': 'data/models/linear_model.pkl',
            'arima': 'data/models/arima_model.pkl',
            'xgboost': 'data/models/xgboost_model.pkl',
            'lstm': 'data/models/lstm_model.keras' # Updated extension for LSTM
        }
        # ALIGNED FEATURES: Only use what the models were trained on
        self.feature_cols = ['month', 'day_of_week', 'is_weekend', 'lag_1']
    
    def load_model(self, model_type):
        """Load a trained model from disk"""
        if model_type in self.models:
            return self.models[model_type]
        
        model_path = self.model_paths.get(model_type)
        if not model_path or not os.path.exists(model_path):
            raise FileNotFoundError(f"Model {model_type} not found at {model_path}")
        
        if model_type == 'linear':
            model = LinearForecastModel()
        elif model_type == 'arima':
            model = ARIMAForecastModel()
        elif model_type == 'xgboost':
            model = XGBoostForecastModel()
        elif model_type == 'lstm':
            model = LSTMForecastModel(sequence_length=1) # Match trainer sequence
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        model.load_model(model_path)
        self.models[model_type] = model
        print(f"✅ Loaded {model_type} model")
        return model
    
    def fetch_historical_data(self, days_back=365):
        """Fetch historical sales data from database"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        sales_query = db.session.query(Sales).filter(
            Sales.outlet_id == self.outlet_id,
            Sales.date >= start_date,
            Sales.date <= end_date
        ).order_by(Sales.date)
        
        sales_data = []
        for sale in sales_query.all():
            sales_data.append({
                'date': sale.date,
                'customer_count': sale.customer_count or 0,
                'quantity_sold': sale.quantity_sold
            })
        
        if not sales_data:
            raise ValueError(f"No historical data found for outlet {self.outlet_id}")
        
        df = pd.DataFrame(sales_data)
        print(f"✅ Fetched {len(df)} records from database")
        return df
    
    def prepare_features(self, df):
        """Prepare features matching the ModelTrainer logic"""
        daily_df = df.groupby('date').agg({
            'quantity_sold': 'sum',
            'customer_count': 'sum'
        }).reset_index().sort_values('date')
        
        daily_df['date'] = pd.to_datetime(daily_df['date'])
        
        # ALIGNED FEATURES: Match the 4 features used in Trainer
        daily_df['month'] = daily_df['date'].dt.month
        daily_df['day_of_week'] = daily_df['date'].dt.dayofweek
        daily_df['is_weekend'] = daily_df['day_of_week'].isin([5, 6]).astype(int)
        
        # Target for lag (using quantity_sold to match trainer)
        target_col = "quantity_sold"
        daily_df['lag_1'] = daily_df[target_col].shift(1)
        
        # Use bfill to avoid NaNs dropping rows
        daily_df = daily_df.bfill().fillna(0)
        
        print(f"✅ Prepared features for {len(daily_df)} days")
        return daily_df
    
    def generate_forecast(self, model_type='auto', days_ahead=7):
        """Orchestrate the forecasting process"""
        historical_df = self.fetch_historical_data()
        feature_df = self.prepare_features(historical_df)
        
        if model_type == 'auto':
            # Defaulting to XGBoost if data is too small for full auto-select logic
            model_type = 'xgboost' if len(feature_df) < 30 else self.auto_select_model(feature_df)
        
        model = self.load_model(model_type)
        
        if model_type in ['linear', 'xgboost']:
            predictions = self._predict_with_ml_model(model, feature_df, days_ahead)
        elif model_type == 'arima':
            predictions = self._predict_with_arima(model, feature_df, days_ahead)
        elif model_type == 'lstm':
            predictions = self._predict_with_lstm(model, feature_df, days_ahead)
        
        # Save and return
        forecast_id = self.save_forecast_to_db(predictions, model_type, 0.85)
        
        return {
            'forecast_id': forecast_id,
            'outlet_id': self.outlet_id,
            'model_used': model_type,
            'next_day_prediction': int(predictions[0]),
            'forecast_dates': [(datetime.now().date() + timedelta(days=i+1)).isoformat() 
                              for i in range(len(predictions))]
        }

    def _predict_with_ml_model(self, model, feature_df, days_ahead):
        """Predict with ML models using the 4-feature shape"""
        predictions = []
        last_row = feature_df.iloc[-1].copy()
        
        for day in range(days_ahead):
            # FIXED: Prepare exactly 4 features
            next_features = last_row[self.feature_cols].values.reshape(1, -1)
            
            pred = model.predict(next_features)[0]
            pred = max(0, int(pred))
            predictions.append(pred)
            
            # Recursive update for next day
            last_row['lag_1'] = pred
            last_row['day_of_week'] = (last_row['day_of_week'] + 1) % 7
            last_row['is_weekend'] = 1 if last_row['day_of_week'] in [5, 6] else 0
            # Note: month would only update at month-end, omitted for simplicity here
        
        return predictions

    def _predict_with_arima(self, model, feature_df, days_ahead):
        forecast = model.predict(steps=days_ahead)
        return [max(0, int(p)) for p in forecast]

    def _predict_with_lstm(self, model, feature_df, days_ahead):
        # Match the trainer's use of quantity_sold
        last_sequence = feature_df['quantity_sold'].tail(model.sequence_length).values.tolist()
        return model.predict_next_days(last_sequence, days=days_ahead)

    def save_forecast_to_db(self, predictions, model_type, confidence):
        forecast = Forecast(
            outlet_id=self.outlet_id,
            forecast_date=datetime.now().date() + timedelta(days=1),
            predicted_customers=int(predictions[0]),
            confidence_level=confidence,
            model_used=model_type,
            created_at=datetime.now()
        )
        db.session.add(forecast)
        db.session.commit()
        return forecast.id