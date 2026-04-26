import xgboost as xgb
from .base_model import BaseModel
import numpy as np

class XGBoostForecastModel(BaseModel):
    """XGBoost Gradient Boosting for forecasting"""
    
    def __init__(self):
        super().__init__('XGBoost')
        self.model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        )
    
    def train(self, X_train, y_train):
        """Train XGBoost model"""
        print(f"Training {self.model_name}...")
        
        self.model.fit(
            X_train, 
            y_train,
            eval_set=[(X_train, y_train)],
            verbose=False
        )
        
        self.is_trained = True
        print(f"✅ {self.model_name} trained successfully")
        
        # Show feature importance
        if hasattr(X_train, 'columns'):
            importance = dict(zip(X_train.columns, self.model.feature_importances_))
            print("\nFeature Importance:")
            for feature, imp in sorted(importance.items(), key=lambda x: x[1], reverse=True):
                print(f"  {feature}: {imp:.4f}")
    
    def predict(self, X_test):
        """Make predictions"""
        if not self.is_trained:
            raise Exception("Model not trained yet!")
        
        predictions = self.model.predict(X_test)
        predictions = np.maximum(predictions, 0)
        return predictions