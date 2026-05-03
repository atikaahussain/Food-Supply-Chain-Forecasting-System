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
    
    def __init__(self, outlet_id=24):
        self.outlet_id = outlet_id
        self.data = None  # Data is stored here
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
                'customer_count': sale.customer_count or 0,
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
        """Create features for ML models without aggressive dropping"""
        # FIX: Changed self.df.copy() to self.data.copy() to match load_data_from_db
        if self.data is None or self.data.empty:
            raise RuntimeError("No data loaded. Call load_data_from_db() first.")
            
        df = self.data.copy()
        
        # Ensure date is datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Aggregate by date to get daily totals
        df = df.groupby('date').agg({
            'quantity_sold': 'sum',
            'customer_count': 'sum'
        }).reset_index().sort_values('date')
        
        # Date features
        df['month'] = df['date'].dt.month
        df['day_of_week'] = df['date'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Target column
        target_col = "quantity_sold"
        
        # FIX: Only using features we actually create. 
        # lag_7 and lag_30 were causing your "n_samples=0" error because they 
        # turned your rows into NaNs which then got dropped.
        df["lag_1"] = df[target_col].shift(1)
        
        # Use bfill to keep the first row instead of dropna()
        df = df.bfill() 
        
        if len(df) < 2:
            raise ValueError(f"Not enough daily data points ({len(df)}) to split into train/test. Add more dates to Sales.")
            
        print(f"✅ Prepared features for {len(df)} unique days of training.")
        return df
    
    def train_all_models(self):
        """Train all 4 models and compare"""
        print("\n" + "="*70)
        print("TRAINING ALL MODELS")
        print("="*70 + "\n")
        
        # Prepare data
        df = self.prepare_features()
        
        # FIX: Updated feature_cols to only include what we defined in prepare_features
        feature_cols = ['month', 'day_of_week', 'is_weekend', 'lag_1']
        X = df[feature_cols]
        y = df['quantity_sold']
        
        # Train-test split (80-20)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False
        )
        
        # 1. Linear Regression
        print("1️⃣  Training Linear Regression...")
        try:
            linear_model = LinearForecastModel()
            linear_model.train(X_train, y_train)
            linear_metrics = linear_model.evaluate(X_test, y_test)
            linear_model.save_model('data/models/linear_model.pkl')
            self.models['linear'] = linear_model
            self.results['linear'] = linear_metrics
        except Exception as e:
            print(f"⚠️  Skipping Linear: {e}")
        
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
        
        # 3. ARIMA
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
            lstm_model = LSTMForecastModel(sequence_length=1) # Set to 1 because data is small
            lstm_data = df['quantity_sold'].astype(float).values
            lstm_model.train(lstm_data, epochs=10)
            lstm_model.save_model('data/models/lstm_model.keras')
            self.models['lstm'] = lstm_model
        except Exception as e:
            print(f"⚠️  Skipping LSTM: {e}")
        
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
            print(f"{model_name:<20} {metrics.get('MAE', 0):<12.2f} {metrics.get('RMSE', 0):<12.2f} {metrics.get('R2_Score', 0):<12.4f}")
        
        print("="*70 + "\n")

if __name__ == '__main__':
    from backend.app import app
    with app.app_context():
        # Using outlet_id 24 as seen in your database screenshot
        trainer = ModelTrainer(outlet_id=24) 
        trainer.load_data_from_db()
        models, results = trainer.train_all_models()