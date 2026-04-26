import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from backend.models.linear_model import LinearForecastModel
from backend.models.arima_model import ARIMAForecastModel
from backend.models.xgboost_model import XGBoostForecastModel
from backend.models.lstm_model import LSTMForecastModel
from backend.database.models import db, Sales

class ModelTrainer:
    """Train and compare different forecasting models"""
    
    def __init__(self, outlet_id=1):
        self.outlet_id = outlet_id
        self.data = None
        self.models = {}
        self.results = {}
    
    def load_data_from_db(self):
        """Load sales data from database"""
        query = db.session.query(Sales).filter_by(outlet_id=self.outlet_id)
        sales_records = query.all()
        
        data = []
        for sale in sales_records:
            data.append({
                'date': sale.date,
                'customer_count': sale.customer_count,
                'quantity_sold': sale.quantity_sold,
                'revenue': sale.revenue
            })
        
        self.data = pd.DataFrame(data)
        if not self.data.empty:
            self.data["date"] = pd.to_datetime(self.data["date"])
            self.data = self.data.sort_values('date')
        
        print(f"✅ Loaded {len(self.data)} records from database")
        return self.data
    
    def prepare_features(self):
        """Create features for ML models"""
        df = self.data.copy()
        if df.empty:
            raise RuntimeError("No data loaded. Call load_data_from_db() first.")
        
        # Date features
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day'] = df['date'].dt.day
        df['day_of_week'] = df['date'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        df['week_of_year'] = df['date'].dt.isocalendar().week.astype(int)
        
        # Lag features (previous days)
        # Forecast target: quantity_sold (customer_count is often null in current schema)
        target_col = "quantity_sold"
        df["lag_1"] = df[target_col].shift(1)
        df["lag_7"] = df[target_col].shift(7)
        df["lag_30"] = df[target_col].shift(30)
        
        # Rolling statistics
        df["rolling_mean_7"] = df[target_col].rolling(window=7, min_periods=1).mean()
        df["rolling_std_7"] = df[target_col].rolling(window=7, min_periods=1).std().fillna(0.0)
        
        # Drop NaN from lags
        df = df.dropna()
        
        return df
    
    def train_all_models(self):
        """Train all 4 models and compare"""
        print("\n" + "="*70)
        print("TRAINING ALL MODELS")
        print("="*70 + "\n")
        
        # Prepare data
        df = self.prepare_features()
        
        # Features and target
        feature_cols = ['month', 'day_of_week', 'is_weekend', 'week_of_year',
                       'lag_1', 'lag_7', 'lag_30', 'rolling_mean_7', 'rolling_std_7']
        X = df[feature_cols]
        y = df['quantity_sold']
        
        # Train-test split (80-20)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False
        )
        
        # 1. Linear Regression
        print("1️⃣  Training Linear Regression...")
        linear_model = LinearForecastModel()
        linear_model.train(X_train, y_train)
        linear_metrics = linear_model.evaluate(X_test, y_test)
        linear_model.save_model('data/models/linear_model.pkl')
        self.models['linear'] = linear_model
        self.results['linear'] = linear_metrics
        
        # 2. XGBoost
        print("\n2️⃣  Training XGBoost...")
        try:
            xgb_model = XGBoostForecastModel()
            xgb_model.train(X_train, y_train)
            xgb_metrics = xgb_model.evaluate(X_test, y_test)
            xgb_model.save_model('data/models/xgboost_model.pkl')
            self.models['xgboost'] = xgb_model
            self.results['xgboost'] = xgb_metrics
        except Exception as e:
            print(f"⚠️  Skipping XGBoost: {e}")
        
        # 3. ARIMA (uses time series directly)
        print("\n3️⃣  Training ARIMA...")
        try:
            time_series = df.set_index('date')['quantity_sold']
            arima_model = ARIMAForecastModel()
            arima_model.train(time_series)
            arima_model.save_model('data/models/arima_model.pkl')
            self.models['arima'] = arima_model
        except Exception as e:
            print(f"⚠️  Skipping ARIMA: {e}")
        
        # 4. LSTM
        print("\n4️⃣  Training LSTM...")
        try:
            lstm_model = LSTMForecastModel(sequence_length=7)
            lstm_data = df['quantity_sold'].astype(float).values
            lstm_model.train(lstm_data, epochs=20)
            lstm_model.save_model('data/models/lstm_model.keras')
            self.models['lstm'] = lstm_model
        except Exception as e:
            print(f"⚠️  Skipping LSTM: {e}")
        
        # Compare results
        self.print_comparison()
        
        return self.models, self.results
    
    def print_comparison(self):
        """Print model comparison table"""
        print("\n" + "="*70)
        print("MODEL COMPARISON RESULTS")
        print("="*70)
        print(f"{'Model':<20} {'MAE':<12} {'RMSE':<12} {'R2 Score':<12}")
        print("-"*70)
        
        for model_name, metrics in self.results.items():
            if all(k in metrics for k in ['MAE', 'RMSE', 'R2_Score']):
                print(f"{model_name:<20} {metrics['MAE']:<12.2f} {metrics['RMSE']:<12.2f} {metrics['R2_Score']:<12.4f}")
        
        print("="*70 + "\n")
        
        # Recommend best model
        if self.results:
            best_model = min(self.results.items(), key=lambda x: x[1].get('MAE', float('inf')))
            print(f"🏆 Best Model (Lowest MAE): {best_model[0].upper()}")
            print(f"   MAE: {best_model[1]['MAE']:.2f}\n")

# Test script
if __name__ == '__main__':
    from backend.app import app
    
    with app.app_context():
        trainer = ModelTrainer(outlet_id=1)
        trainer.load_data_from_db()
        models, results = trainer.train_all_models()