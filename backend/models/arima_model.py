from statsmodels.tsa.arima.model import ARIMA
from .base_model import BaseModel
import warnings
warnings.filterwarnings('ignore')

class ARIMAForecastModel(BaseModel):
    """ARIMA model for time series forecasting"""
    
    def __init__(self, order=(5, 1, 0)):
        super().__init__('ARIMA')
        self.order = order  # (p, d, q) parameters
        self.fitted_model = None
    
    def train(self, time_series_data):
        """
        Train ARIMA model
        time_series_data: pandas Series with datetime index
        """
        print(f"Training {self.model_name} with order {self.order}...")
        
        self.model = ARIMA(time_series_data, order=self.order)
        self.fitted_model = self.model.fit()
        self.is_trained = True
        
        print(f"✅ {self.model_name} trained successfully")
        print(f"AIC: {self.fitted_model.aic:.2f}")
        print(f"BIC: {self.fitted_model.bic:.2f}")
    
    def predict(self, steps=7):
        """Predict next N steps"""
        if not self.is_trained:
            raise Exception("Model not trained yet!")
        
        forecast = self.fitted_model.forecast(steps=steps)
        # Ensure non-negative
        forecast = forecast.clip(lower=0)
        return forecast.values

    def save_model(self, filepath):
        """Save fitted ARIMA results (pickle)."""
        import pickle
        import os

        if not self.is_trained or self.fitted_model is None:
            raise RuntimeError("ARIMA model is not trained; nothing to save.")

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as f:
            pickle.dump(
                {"order": self.order, "fitted_model": self.fitted_model},
                f,
            )
        print(f"✅ Model saved to {filepath}")

    def load_model(self, filepath):
        """Load fitted ARIMA results (pickle)."""
        import pickle

        with open(filepath, "rb") as f:
            payload = pickle.load(f)
        self.order = payload.get("order", self.order)
        self.fitted_model = payload["fitted_model"]
        self.is_trained = True
        print(f"✅ Model loaded from {filepath}")
    
    def predict_with_confidence(self, steps=7, alpha=0.05):
        """Predict with confidence intervals"""
        forecast_result = self.fitted_model.get_forecast(steps=steps)
        forecast = forecast_result.predicted_mean
        conf_int = forecast_result.conf_int(alpha=alpha)
        
        return {
            'forecast': forecast.values,
            'lower_bound': conf_int.iloc[:, 0].values,
            'upper_bound': conf_int.iloc[:, 1].values
        }