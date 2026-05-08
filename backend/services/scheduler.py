from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from backend.database.models import db, Outlet
from backend.services.forecasting_engine import ForecastEngine
from backend.services.item_forecaster import ItemLevelForecaster
from backend.services.alert_service import AlertService
from email.mime.multipart import MIMEMultipart
from backend.services.report_generator import ReportGenerator
from backend.services.email_service import EmailService
import os

class ForecastScheduler:
    """Automated scheduling for daily forecasts"""
    
    def __init__(self, app):
        self.app = app
        self.scheduler = BackgroundScheduler()
    
    def start(self):
        """Start the scheduler"""
        # Schedule daily forecast at midnight
        self.scheduler.add_job(
            func=self.generate_daily_forecasts,
            trigger=CronTrigger(hour=0, minute=0),  # Run at 00:00
            id='daily_forecast',
            name='Generate daily forecasts',
            replace_existing=True
        )
        
        self.scheduler.start()
        print("✅ Forecast scheduler started")
        print("   📅 Daily forecasts will run at midnight")
    
    def generate_daily_forecasts(self):
        """Generate forecasts for all outlets"""
        print(f"\n{'='*60}")
        print(f"AUTOMATED DAILY FORECAST - {datetime.now()}")
        print(f"{'='*60}\n")
        
        with self.app.app_context():
            # Get all outlets
            outlets = db.session.query(Outlet).all()
            
            for outlet in outlets:
                try:
                    print(f"🏪 Processing outlet: {outlet.name}")
                    
                    # Generate forecast
                    engine = ForecastEngine(outlet.id)
                    result = engine.generate_forecast(model_type='auto', days_ahead=7)
                    
                    # Generate item forecasts
                    item_forecaster = ItemLevelForecaster(outlet.id)
                    item_results = item_forecaster.forecast_all_items(
                        forecast_id=result['forecast_id']
                    )
                    
                    # Generate alerts
                    alert_service = AlertService(outlet.id)
                    alerts_created = alert_service.generate_all_alerts(
                        forecast_id=result['forecast_id']
                    )
                    
                    active_alerts = alert_service.get_active_alerts()
                    
                    # Generate Report
                    report_gen = ReportGenerator(outlet.name)
                    timestamp = datetime.now().strftime('%Y%m%d')
                    report_path = f"data/reports/daily_{outlet.id}_{timestamp}.pdf"
                    os.makedirs(os.path.dirname(report_path), exist_ok=True)
                    
                    # Prepare item forecasts for report
                    report_items = {}
                    for item_name, data in item_results.items():
                        report_items[item_name] = {
                            'next_day': data['next_day'],
                            'next_week': [data['next_day']] * 7
                        }
                    
                    report_gen.generate_forecast_report(result, report_items, report_path)
                    
                    # Send forecast notification with attachment
                    email_service = EmailService()
                    manager_email = os.getenv('MANAGER_EMAIL', 'manager@restaurant.com')
                    
                    email_service.send_forecast_notification(
                        manager_email,
                        result,
                        outlet.name,
                        attachment_path=report_path
                    )
                    
                    # Send alert email if high priority alerts exist
                    high_alerts = [a for a in active_alerts if a.get('severity') == 'high']
                    if high_alerts:
                        email_service.send_alert_notification(
                            manager_email,
                            high_alerts,
                            outlet.name
                        )
                    
                    print(f"✅ Completed forecast for {outlet.name}\n")
                    
                except Exception as e:
                    print(f"❌ Error processing {outlet.name}: {str(e)}\n")
    

    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        print("🛑 Scheduler stopped")


# Update app.py to start scheduler
# Add to create_app() function:
# scheduler = ForecastScheduler(app)
# scheduler.start()