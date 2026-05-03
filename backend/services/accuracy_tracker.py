from datetime import datetime, timedelta
from backend.database.models import db, Forecast, Sales, ModelMetadata
import numpy as np

class AccuracyTracker:
    """Track and analyze forecast accuracy"""
    
    def __init__(self):
        self.accuracy_threshold = 0.80  # 80% accuracy required
    
    def calculate_accuracy(self, forecast_id):
        """
        Calculate accuracy by comparing prediction vs actual
        
        Returns:
            dict with accuracy metrics
        """
        # Get forecast
        forecast = db.session.query(Forecast).get(forecast_id)
        
        if not forecast:
            raise ValueError(f"Forecast {forecast_id} not found")
        
        # Get actual sales for that date
        actual_sales = db.session.query(Sales).filter(
            Sales.outlet_id == forecast.outlet_id,
            Sales.date == forecast.forecast_date
        ).all()
        
        if not actual_sales:
            return {'status': 'pending', 'message': 'Actual data not yet available'}
        
        # Sum actual customers
        actual_customers = sum(sale.customer_count for sale in actual_sales)
        predicted_customers = forecast.predicted_customers
        
        # Calculate metrics
        error = abs(predicted_customers - actual_customers)
        percentage_error = (error / actual_customers * 100) if actual_customers > 0 else 0
        accuracy = max(0, 100 - percentage_error)
        
        # Determine if within acceptable range
        is_accurate = percentage_error <= 20  # Within 20% is acceptable
        
        result = {
            'forecast_id': forecast_id,
            'forecast_date': forecast.forecast_date.isoformat(),
            'predicted': predicted_customers,
            'actual': actual_customers,
            'error': error,
            'percentage_error': round(percentage_error, 2),
            'accuracy': round(accuracy, 2),
            'is_accurate': is_accurate,
            'model_used': forecast.model_used
        }
        
        print(f"\n📊 Accuracy Report for Forecast #{forecast_id}")
        print(f"   Predicted: {predicted_customers}")
        print(f"   Actual: {actual_customers}")
        print(f"   Error: {error} ({percentage_error:.1f}%)")
        print(f"   Accuracy: {accuracy:.1f}%")
        print(f"   Status: {'✅ Acceptable' if is_accurate else '⚠️ Needs improvement'}\n")
        
        return result
    
    def check_model_performance(self, outlet_id, days_back=30):
        """
        Check overall model performance over last N days
        
        Returns:
            bool: True if retraining needed
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        # Get all forecasts in period
        forecasts = db.session.query(Forecast).filter(
            Forecast.outlet_id == outlet_id,
            Forecast.forecast_date >= start_date,
            Forecast.forecast_date <= end_date
        ).all()
        
        if not forecasts:
            return False
        
        # Calculate accuracy for each
        accuracies = []
        
        for forecast in forecasts:
            try:
                result = self.calculate_accuracy(forecast.id)
                if result.get('accuracy'):
                    accuracies.append(result['accuracy'])
            except:
                pass
        
        if not accuracies:
            return False
        
        # Calculate average accuracy
        avg_accuracy = np.mean(accuracies)
        
        print(f"\n📈 Model Performance (Last {days_back} days)")
        print(f"   Average Accuracy: {avg_accuracy:.1f}%")
        print(f"   Forecasts Evaluated: {len(accuracies)}")
        
        # Check if retraining needed
        needs_retraining = avg_accuracy < (self.accuracy_threshold * 100)
        
        if needs_retraining:
            print(f"   ⚠️  Performance below threshold ({self.accuracy_threshold*100}%)")
            print(f"   🔄 Retraining recommended!")
        else:
            print(f"   ✅ Performance acceptable")
        
        return needs_retraining
    
    def trigger_retraining(self, outlet_id):
        """Trigger model retraining"""
        print(f"\n🔄 Triggering model retraining for outlet {outlet_id}...")
        
        # Import here to avoid circular imports
        from backend.services.model_trainer import ModelTrainer        
        try:
            trainer = ModelTrainer(outlet_id)
            trainer.load_data_from_db()
            models, results = trainer.train_all_models()
            
            print("✅ Retraining completed!")
            return True
            
        except Exception as e:
            print(f"❌ Retraining failed: {str(e)}")
            return False

