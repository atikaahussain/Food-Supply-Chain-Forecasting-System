import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
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
        self.scaler = None
        self.scaler_path = 'data/models/scaler.pkl'
        self.model_paths = {
            'linear': 'data/models/linear_model.pkl',
            'arima': 'data/models/arima_model.pkl',
            'xgboost': 'data/models/xgboost_model.pkl',
            'lstm': 'data/models/lstm_model.keras' # Updated extension for LSTM
        }
        # ALIGNED FEATURES: Only use what the models were trained on
        self.feature_cols = ['month', 'day_of_week', 'is_weekend', 'lag_1', 'lag_7', 'rolling_mean_7']
    
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

    def load_scaler(self):
        """Load the saved feature scaler for model inference"""
        if self.scaler is not None:
            return self.scaler
        if not os.path.exists(self.scaler_path):
            raise FileNotFoundError(f"Scaler not found at {self.scaler_path}")
        with open(self.scaler_path, 'rb') as scaler_file:
            self.scaler = pickle.load(scaler_file)
        print(f"✅ Loaded scaler from {self.scaler_path}")
        return self.scaler

    def scale_features(self, feature_array):
        """Scale feature rows using the saved StandardScaler."""
        scaler = self.load_scaler()
        return scaler.transform(feature_array)
    
    def fetch_historical_data(self, days_back=1500):
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
    
    def auto_select_model(self, feature_df):
        """Simple logic to pick the best model based on data size"""
        # If we have very little data, use Linear Regression
        if len(feature_df) < 100:
            return 'linear'
        # If we have a decent amount of data, use XGBoost
        return 'xgboost'
    
    
    def prepare_features(self, df):
        """Prepare features matching the ModelTrainer logic"""
        daily_df = df.copy()
        if 'customer_count' not in daily_df.columns:
            daily_df['customer_count'] = 0

        daily_df = daily_df.groupby('date').agg({
            'quantity_sold': 'sum',
            'customer_count': 'sum'
        }).reset_index().sort_values('date')
        
        daily_df['date'] = pd.to_datetime(daily_df['date'])
        
        daily_df['month'] = daily_df['date'].dt.month
        daily_df['day_of_week'] = daily_df['date'].dt.dayofweek
        daily_df['is_weekend'] = daily_df['day_of_week'].isin([5, 6]).astype(int)
        
        target_col = "quantity_sold"
        daily_df['lag_1'] = daily_df[target_col].shift(1)
        daily_df['lag_7'] = daily_df[target_col].shift(7)
        daily_df['rolling_mean_7'] = daily_df[target_col].shift(1).rolling(window=7, min_periods=1).mean()
        
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
                              for i in range(len(predictions))],
            'next_week_predictions': predictions
        }

    def _predict_with_ml_model(self, model, feature_df, days_ahead, scaler=None):
        """Predict with ML models using the trained feature set."""
        predictions = []
        history = feature_df['quantity_sold'].tolist()
        last_date = pd.to_datetime(feature_df['date'].iloc[-1])

        for day in range(days_ahead):
            next_date = last_date + timedelta(days=day + 1)
            next_features = np.array([
                next_date.month,
                next_date.dayofweek,
                1 if next_date.dayofweek in [5, 6] else 0,
                history[-1] if len(history) >= 1 else 0,
                history[-7] if len(history) >= 7 else 0,
                float(np.mean(history[-7:])) if len(history) >= 1 else 0.0
            ]).reshape(1, -1)

            if scaler is None:
                scaled_features = self.scale_features(next_features)
            else:
                scaled_features = scaler.transform(next_features)

            pred = model.predict(scaled_features)[0]
            pred = max(0, int(pred))
            predictions.append(pred)
            history.append(pred)

        return predictions

    def _predict_with_arima(self, model, feature_df, days_ahead):
        forecast = model.predict(steps=days_ahead)
        return [max(0, int(p)) for p in forecast]

    def forecast_item_by_id(self, food_item_id, model_type='auto', days_ahead=7):
        """Generate an item-specific forecast using per-item historical sales."""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=1500)

        sales_query = db.session.query(Sales).filter(
            Sales.outlet_id == self.outlet_id,
            Sales.food_item_id == food_item_id,
            Sales.date >= start_date,
            Sales.date <= end_date
        ).order_by(Sales.date)

        item_sales = []
        for sale in sales_query.all():
            item_sales.append({
                'date': sale.date,
                'quantity_sold': sale.quantity_sold,
                'customer_count': sale.customer_count or 0
            })

        if not item_sales:
            return [0] * days_ahead

        item_df = pd.DataFrame(item_sales)
        item_df['date'] = pd.to_datetime(item_df['date'])
        feature_df = self.prepare_features(item_df)

        if model_type == 'auto':
            model_type = 'linear' if len(feature_df) < 100 else self.auto_select_model(feature_df)

        feature_cols = self.feature_cols
        X = feature_df[feature_cols]
        y = feature_df['quantity_sold']

        # Train an item-specific model on the item's own historical data
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        X_scaled = pd.DataFrame(X_scaled, columns=feature_cols, index=X.index)

        if model_type == 'linear':
            model = LinearForecastModel()
            model.train(X_scaled, y)
        elif model_type == 'xgboost':
            model = XGBoostForecastModel()
            model.train(X_scaled, y)
        else:
            model = self.load_model(model_type)

        if model_type in ['linear', 'xgboost']:
            return self._predict_with_ml_model(model, feature_df, days_ahead, scaler=scaler)
        if model_type == 'arima':
            return self._predict_with_arima(model, feature_df, days_ahead)
        if model_type == 'lstm':
            return self._predict_with_lstm(model, feature_df, days_ahead)

        raise ValueError(f"Unsupported item-level model type: {model_type}")

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