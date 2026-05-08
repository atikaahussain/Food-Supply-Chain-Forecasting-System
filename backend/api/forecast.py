from flask import Blueprint, request, jsonify
from backend.database.models import db, Forecast, ItemForecast, FoodItem
from backend.services.forecasting_engine import ForecastEngine
from backend.services.item_forecaster import ItemLevelForecaster

from datetime import datetime

forecast_bp = Blueprint('forecast', __name__)

@forecast_bp.route('/generate', methods=['POST'])
def generate_forecast():
    """
    Generate new forecast
    
    POST /api/forecast/generate
    Body: {
        "outlet_id": 1,
        "model_type": "auto",  # or "linear", "xgboost", etc.
        "days_ahead": 7
    }
    """
    try:
        data = request.get_json()
        
        outlet_id = data.get('outlet_id', 1)
        model_type = data.get('model_type', 'auto')
        days_ahead = data.get('days_ahead', 7)
        
        # Validate inputs
        if days_ahead < 1 or days_ahead > 30:
            return jsonify({'error': 'days_ahead must be between 1 and 30'}), 400
        
        # Generate forecast
        engine = ForecastEngine(outlet_id)
        result = engine.generate_forecast(model_type=model_type, days_ahead=days_ahead)
        
        # Generate item-level forecasts
        item_forecaster = ItemLevelForecaster(outlet_id)
        item_results = item_forecaster.forecast_all_items(
            forecast_id=result['forecast_id'],
            days_ahead=days_ahead
        )
        
        # Add item forecasts to result
        result['item_forecasts'] = item_results
        
        return jsonify({
            'success': True,
            'message': 'Forecast generated successfully',
            'data': result
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@forecast_bp.route('/<int:forecast_id>', methods=['GET'])
def get_forecast(forecast_id):
    """
    Retrieve specific forecast
    
    GET /api/forecast/123
    """
    try:
        forecast = db.session.get(Forecast, forecast_id)

        if not forecast:
            return jsonify({'error': 'Forecast not found'}), 404
        
        # Get item forecasts
        item_forecasts = db.session.query(ItemForecast, FoodItem).join(
            FoodItem, ItemForecast.food_item_id == FoodItem.id
        ).filter(ItemForecast.forecast_id == forecast_id).all()
        
        items = {}
        for item_forecast, food_item in item_forecasts:
            items[food_item.name] = {
                'predicted_quantity': item_forecast.predicted_quantity,
                'category': food_item.category
            }
        
        result = {
            'forecast_id': forecast.id,
            'outlet_id': forecast.outlet_id,
            'forecast_date': forecast.forecast_date.isoformat(),
            'predicted_customers': forecast.predicted_customers,
            'confidence_level': forecast.confidence_level,
            'model_used': forecast.model_used,
            'created_at': forecast.created_at.isoformat(),
            'item_forecasts': items
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@forecast_bp.route('/latest/<int:outlet_id>', methods=['GET'])
def get_latest_forecast(outlet_id):
    """
    Get most recent forecast for outlet
    
    GET /api/forecast/latest/1
    """
    try:
        forecast = db.session.query(Forecast).filter(
            Forecast.outlet_id == outlet_id
        ).order_by(Forecast.created_at.desc()).first()
        
        if not forecast:
            return jsonify({'error': 'No forecasts found for this outlet'}), 404
        
        # Get item forecasts
        item_forecasts = db.session.query(ItemForecast, FoodItem).join(
            FoodItem, ItemForecast.food_item_id == FoodItem.id
        ).filter(ItemForecast.forecast_id == forecast.id).all()
        
        items = {}
        for item_forecast, food_item in item_forecasts:
            items[food_item.name] = {
                'predicted_quantity': item_forecast.predicted_quantity,
                'category': food_item.category
            }
        
        result = {
            'forecast_id': forecast.id,
            'forecast_date': forecast.forecast_date.isoformat(),
            'predicted_customers': forecast.predicted_customers,
            'confidence_level': forecast.confidence_level,
            'model_used': forecast.model_used,
            'item_forecasts': items
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@forecast_bp.route('/history/<int:outlet_id>', methods=['GET'])
def get_forecast_history(outlet_id):
    """
    List all past forecasts
    
    GET /api/forecast/history/1?limit=10
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        
        forecasts = db.session.query(Forecast).filter(
            Forecast.outlet_id == outlet_id
        ).order_by(Forecast.created_at.desc()).limit(limit).all()
        
        result = []
        for forecast in forecasts:
            result.append({
                'forecast_id': forecast.id,
                'forecast_date': forecast.forecast_date.isoformat(),
                'predicted_customers': forecast.predicted_customers,
                'confidence_level': forecast.confidence_level,
                'model_used': forecast.model_used,
                'created_at': forecast.created_at.isoformat()
            })
        
        return jsonify({
            'total': len(result),
            'forecasts': result
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@forecast_bp.route('/<int:forecast_id>', methods=['DELETE'])
def delete_forecast(forecast_id):
    """
    Delete old forecast
    
    DELETE /api/forecast/123
    """
    try:
        forecast = db.session.get(Forecast, forecast_id)

        if not forecast:
            return jsonify({'error': 'Forecast not found'}), 404
        
        # Delete associated item forecasts first
        db.session.query(ItemForecast).filter(
            ItemForecast.forecast_id == forecast_id
        ).delete()
        
        # Delete main forecast
        db.session.delete(forecast)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Forecast {forecast_id} deleted'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@forecast_bp.route('/accuracy/<int:forecast_id>', methods=['GET'])
def check_accuracy(forecast_id):
    """Check accuracy of a specific past forecast"""
    try:
        from backend.services.accuracy_tracker import AccuracyTracker
        tracker = AccuracyTracker()
        result = tracker.calculate_accuracy(forecast_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@forecast_bp.route('/performance/<int:outlet_id>', methods=['GET'])
def check_performance(outlet_id):
    """Check overall model performance and see if retraining is needed"""
    try:
        from backend.services.accuracy_tracker import AccuracyTracker
        days_back = request.args.get('days', 30, type=int)
        
        tracker = AccuracyTracker()
        needs_retraining = tracker.check_model_performance(outlet_id, days_back)
        
        return jsonify({
            'outlet_id': outlet_id,
            'needs_retraining': needs_retraining,
            'days_evaluated': days_back
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@forecast_bp.route('/chart-data/<int:outlet_id>', methods=['GET'])
def get_chart_data(outlet_id):
    """
    Get aggregated data for dashboard chart: 
    Past 14 days of actual sales + next 7 days of forecast.
    """
    try:
        from sqlalchemy import func
        from backend.database.models import Sales, Forecast
        from datetime import timedelta

        # 1. Get historical actuals (last 14 days)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=14)
        
        sales_data = db.session.query(
            Sales.date,
            func.sum(Sales.customer_count).label('actual')
        ).filter(
            Sales.outlet_id == outlet_id,
            Sales.date >= start_date,
            Sales.date <= end_date
        ).group_by(Sales.date).order_by(Sales.date).all()

        chart_data = []
        for s in sales_data:
            chart_data.append({
                'date': s.date.isoformat(),
                'actual': int(s.actual or 0),
                'predicted': None
            })

        # 2. Get latest forecast predictions
        latest_forecast = db.session.query(Forecast).filter(
            Forecast.outlet_id == outlet_id
        ).order_by(Forecast.created_at.desc()).first()

        if latest_forecast:
            # For the chart, we'll just show the main prediction for the forecast date
            # In a real app, we might store the full 7-day sequence
            chart_data.append({
                'date': latest_forecast.forecast_date.isoformat(),
                'actual': None,
                'predicted': latest_forecast.predicted_customers
            })

        return jsonify(chart_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500