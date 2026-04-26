from abc import ABC, abstractmethod
import pickle
import os

class BaseModel(ABC):
    """Base class for all forecasting models"""
    
    def __init__(self, model_name):
        self.model_name = model_name
        self.model = None
        self.is_trained = False
    
    @abstractmethod
    def train(self, *args, **kwargs):
        """Train the model (signature depends on model type)."""
        raise NotImplementedError
    
    @abstractmethod
    def predict(self, *args, **kwargs):
        """Make predictions (signature depends on model type)."""
        raise NotImplementedError
    
    def save_model(self, filepath):
        """Save trained model to disk"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(self.model, f)
        print(f"✅ Model saved to {filepath}")
    
    def load_model(self, filepath):
        """Load trained model from disk"""
        with open(filepath, 'rb') as f:
            self.model = pickle.load(f)
        self.is_trained = True
        print(f"✅ Model loaded from {filepath}")
    
    def evaluate(self, X_test, y_test):
        """Evaluate model performance"""
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        import numpy as np
        
        predictions = self.predict(X_test)
        
        mae = mean_absolute_error(y_test, predictions)
        mse = mean_squared_error(y_test, predictions)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_test, predictions)
        
        metrics = {
            'MAE': round(mae, 2),
            'MSE': round(mse, 2),
            'RMSE': round(rmse, 2),
            'R2_Score': round(r2, 4)
        }
        
        print("\n" + "="*50)
        print(f"MODEL EVALUATION: {self.model_name}")
        print("="*50)
        for metric, value in metrics.items():
            print(f"{metric}: {value}")
        print("="*50 + "\n")
        
        return metrics