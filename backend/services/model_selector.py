from datetime import datetime
from backend.database.models import db, ModelMetadata
from backend.models.linear_model import LinearForecastModel
from backend.models.xgboost_model import XGBoostForecastModel
from backend.models.arima_model import ARIMAForecastModel
from backend.models.lstm_model import LSTMForecastModel
import json

class ModelSelector:
    """Handles model selection, versioning, and performance tracking"""
    
    def __init__(self):
        self.performance_cache = {}
    
    def compare_models(self, outlet_id, test_data, test_labels):
        """
        Compare all available models on test data
        
        Returns:
            dict with model names and their performance metrics
        """
        
        results = {}
        models_to_test = {
            'linear': LinearForecastModel(),
            'xgboost': XGBoostForecastModel(),
            'arima': ARIMAForecastModel(),
            'lstm': LSTMForecastModel()
        }
        
        for name, model in models_to_test.items():
            try:
                # Load trained model
                model.load_model(f'data/models/{name}_model.pkl')
                
                # Evaluate
                metrics = model.evaluate(test_data, test_labels)
                results[name] = metrics
                
                # Save to database
                self.save_model_performance(outlet_id, name, metrics)
                
            except Exception as e:
                print(f"Error testing {name}: {str(e)}")
                results[name] = {'error': str(e)}
        
        return results
    
    def save_model_performance(self, outlet_id, model_name, metrics):
        """Save model performance metrics to database"""
        metadata = ModelMetadata(
            model_name=model_name,
            version='1.0',
            accuracy_score=metrics.get('R2_Score', 0),
            trained_date=datetime.now(),
            is_active=True
        )
        
        db.session.add(metadata)
        db.session.commit()
        
        print(f"✅ Saved {model_name} performance: {metrics}")
    
    def get_best_model(self, outlet_id=None):
        """
        Get the best performing model
        
        Returns:
            model_name (str)
        """
        # Check cache first
        cache_key = f"best_model_{outlet_id}"
        if cache_key in self.performance_cache:
            cached_time, model_name = self.performance_cache[cache_key]
            # Cache valid for 7 days
            if (datetime.now() - cached_time).days < 7:
                return model_name
        
        # Query database for best model
        best_model = db.session.query(ModelMetadata).filter(
            ModelMetadata.is_active == True
        ).order_by(ModelMetadata.accuracy_score.desc()).first()
        
        if best_model:
            model_name = best_model.model_name
            # Update cache
            self.performance_cache[cache_key] = (datetime.now(), model_name)
            return model_name
        
        # Default to xgboost if no metadata
        return 'xgboost'
    
    def set_active_model(self, model_name):
        """Set a specific model as active"""
        # Deactivate all models
        db.session.query(ModelMetadata).update({'is_active': False})
        
        # Activate selected model
        model = db.session.query(ModelMetadata).filter(
            ModelMetadata.model_name == model_name
        ).first()
        
        if model:
            model.is_active = True
            db.session.commit()
            print(f"✅ Set {model_name} as active model")
        else:
            print(f"⚠️  Model {model_name} not found in database")