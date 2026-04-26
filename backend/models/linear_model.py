from sklearn.linear_model import LinearRegression
from .base_model import BaseModel
import numpy as np

class LinearForecastModel(BaseModel):
    """Simple Linear Regression for forecasting"""
    
    def __init__(self):
        super().__init__('Linear Regression')
        self.model = LinearRegression()
    
    def train(self, X_train, y_train):
        """Train linear regression model"""
        print(f"Training {self.model_name}...")
        self.model.fit(X_train, y_train)
        self.is_trained = True
        print(f"✅ {self.model_name} trained successfully")
        
        # Show feature importance (coefficients)
        if hasattr(X_train, 'columns'):
            feature_importance = dict(zip(X_train.columns, self.model.coef_))
            print("\nFeature Coefficients:")
            for feature, coef in sorted(feature_importance.items(), key=lambda x: abs(x[1]), reverse=True):
                print(f"  {feature}: {coef:.4f}")
    
    def predict(self, X_test):
        """Make predictions"""
        if not self.is_trained:
            raise Exception("Model not trained yet!")
        
        predictions = self.model.predict(X_test)
        # Ensure predictions are non-negative
        predictions = np.maximum(predictions, 0)
        return predictions
    
    def predict_next_days(self, last_features, days=7):
        """Predict next N days"""
        predictions = []
        current_features = last_features.copy()
        
        for day in range(days):
            pred = self.predict(current_features.reshape(1, -1))[0]
            predictions.append(max(0, int(pred)))
            
            # Update features for next iteration
            # This is simplified - you'd update based on your features
            current_features[0] += 1  # Increment day
        
        return predictions