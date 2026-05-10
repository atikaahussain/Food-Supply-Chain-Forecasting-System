from flask import Blueprint, request, jsonify, send_file
from backend.services.report_generator import ReportGenerator
from backend.services.email_service import EmailService
from backend.services.inventory_planner import InventoryPlanner
from backend.services.supplier_manager import SupplierManager
from backend.database.models import db, Forecast, ItemForecast
from backend.services.forecasting_engine import ForecastEngine
from datetime import datetime
import os

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/forecast/<int:forecast_id>', methods=['GET'])
def generate_forecast_report(forecast_id):
    """
    Generate report (PDF or Excel) for a forecast
    
    GET /api/reports/forecast/123?format=pdf&email=optional@email.com
    GET /api/reports/forecast/123?format=excel
    """
    try:
        forecast = db.session.query(Forecast).get(forecast_id)
        if not forecast:
            return jsonify({'error': 'Forecast not found'}), 404
        
        item_forecasts = {}
        if hasattr(forecast, 'item_forecasts') and forecast.item_forecasts:
            for item in forecast.item_forecasts:
                item_forecasts[item.food_item.name if item.food_item else f'Item {item.id}'] = {
                    'next_day': item.predicted_quantity,
                    'next_week': [item.predicted_quantity] * 7
                }
        
        forecast_data = {
            'forecast_id': forecast.id,
            'next_day_prediction': forecast.predicted_customers,
            'confidence_level': forecast.confidence_level,
            'model_used': forecast.model_used,
            'forecast_dates': [forecast.forecast_date.isoformat()],
            'next_week_predictions': [forecast.predicted_customers],
            'item_forecasts': item_forecasts
        }
        
        generator = ReportGenerator("Restaurant Outlet")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_format = request.args.get('format', 'pdf').lower()
        
        # Ensure absolute path for data/reports
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        reports_dir = os.path.join(base_dir, 'data', 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        if file_format == 'excel':
            filename = f"forecast_report_{forecast_id}_{timestamp}.xlsx"
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            output_path = os.path.join(reports_dir, filename)
            report_path = generator.generate_excel_report(forecast_data, item_forecasts, output_path)
        else:
            filename = f"forecast_report_{forecast_id}_{timestamp}.pdf"
            mimetype = 'application/pdf'
            output_path = os.path.join(reports_dir, filename)
            report_path = generator.generate_forecast_report(forecast_data, item_forecasts, output_path)
        
        email = request.args.get('email')
        if email:
            email_service = EmailService()
            email_service.send_forecast_notification(email, forecast_data, "Restaurant Outlet", report_path)
        
        return send_file(
            os.path.abspath(report_path),
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
        
    except Exception as e:
        print(f"❌ Error in generate_forecast_report: {str(e)}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/inventory/<int:forecast_id>', methods=['GET'])
def generate_inventory_report(forecast_id):
    """
    Generate PDF report for inventory
    
    GET /api/reports/inventory/123
    """
    try:
        forecast = db.session.query(Forecast).get(forecast_id)
        if not forecast:
            return jsonify({'error': 'Forecast not found'}), 404
        
        planner = InventoryPlanner(forecast.outlet_id)
        shopping_list = planner.get_shopping_list(forecast_id)
        supplier_manager = SupplierManager()
        purchase_orders = supplier_manager.generate_purchase_order(shopping_list.get('items', []))
        
        inventory_data = {
            'shopping_list': shopping_list,
            'purchase_orders': purchase_orders
        }
        
        generator = ReportGenerator("Restaurant Outlet")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"inventory_report_{forecast_id}_{timestamp}.pdf"
        
        # Ensure absolute path for data/reports
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        reports_dir = os.path.join(base_dir, 'data', 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        output_path = os.path.join(reports_dir, filename)
        
        report_path = generator.generate_inventory_report(
            inventory_data,
            output_path
        )
        
        return send_file(
            os.path.abspath(report_path),
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/send-email', methods=['POST'])
def send_report_email():
    """
    Send report via email
    
    POST /api/reports/send-email
    Body: {
        "forecast_id": 123,
        "recipient": "manager@restaurant.com",
        "type": "forecast"  # or "inventory"
    }
    """
    try:
        data = request.get_json()
        forecast_id = data.get('forecast_id')
        recipient = data.get('recipient')
        report_type = data.get('type', 'forecast')
        
        if not forecast_id or not recipient:
            return jsonify({'error': 'Missing required fields'}), 400
        
        forecast = db.session.query(Forecast).get(forecast_id)
        if not forecast:
            return jsonify({'error': 'Forecast not found'}), 404
        
        email_service = EmailService()
        generator = ReportGenerator("Restaurant Outlet")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if report_type == 'forecast':
            item_forecasts = {}
            if hasattr(forecast, 'item_forecasts') and forecast.item_forecasts:
                for item in forecast.item_forecasts:
                    item_forecasts[item.food_item.name if item.food_item else f'Item {item.id}'] = {
                        'next_day': item.predicted_quantity,
                        'next_week': [item.predicted_quantity] * 7
                    }
            
            forecast_data = {
                'forecast_id': forecast.id,
                'next_day_prediction': forecast.predicted_customers,
                'confidence_level': forecast.confidence_level,
                'model_used': forecast.model_used,
                'forecast_date': forecast.forecast_date.isoformat(),
                'forecast_dates': [forecast.forecast_date.isoformat()],
                'next_week_predictions': [forecast.predicted_customers],
                'item_forecasts': item_forecasts
            }
            
            # Generate PDF to attach
            filename = f"forecast_report_{forecast_id}_{timestamp}.pdf"
            output_path = os.path.join('data', 'reports', filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            report_path = generator.generate_forecast_report(forecast_data, item_forecasts, output_path)
            
            success = email_service.send_forecast_notification(
                recipient,
                forecast_data,
                "Restaurant Outlet",
                report_path
            )
        else:
            return jsonify({'error': 'Invalid report type'}), 400
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Email sent with report to {recipient}'
            }), 200
        else:
            return jsonify({'error': 'Failed to send email'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
