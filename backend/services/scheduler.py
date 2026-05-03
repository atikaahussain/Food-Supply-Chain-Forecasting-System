from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from backend.database.models import db, Outlet
from backend.services.forecasting_engine import ForecastEngine
from backend.services.item_forecaster import ItemLevelForecaster
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
                    
                    # Send email notification
                    self.send_forecast_email(outlet, result, item_results)
                    
                    print(f"✅ Completed forecast for {outlet.name}\n")
                    
                except Exception as e:
                    print(f"❌ Error processing {outlet.name}: {str(e)}\n")
    
    def send_forecast_email(self, outlet, forecast_result, item_results):
        """Send email notification with forecast"""
        # Email configuration (update with your SMTP settings)
        SMTP_SERVER = 'smtp.gmail.com'
        SMTP_PORT = 587
        SENDER_EMAIL = 'your-email@gmail.com'
        SENDER_PASSWORD = 'your-app-password'
        RECIPIENT_EMAIL = 'manager@restaurant.com'
        
        # Create email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Daily Forecast - {outlet.name} - {datetime.now().date()}"
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        
        # Email body
        html = f"""
        <html>
          <body>
            <h2>📊 Daily Forecast for {outlet.name}</h2>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            
            <h3>Tomorrow's Prediction</h3>
            <p><strong>Expected Customers:</strong> {forecast_result['next_day_prediction']}</p>
            <p><strong>Confidence Level:</strong> {forecast_result['confidence_level']*100}%</p>
            <p><strong>Model Used:</strong> {forecast_result['model_used'].upper()}</p>
            
            <h3>Next Week Outlook</h3>
            <table border="1" cellpadding="5">
              <tr>
                <th>Date</th>
                <th>Predicted Customers</th>
              </tr>
        """
        
        for i, (date, customers) in enumerate(zip(forecast_result['forecast_dates'], 
                                                   forecast_result['next_week_predictions'])):
            html += f"<tr><td>{date}</td><td>{customers}</td></tr>"
        
        html += """
            </table>
            
            <h3>Top Items to Prepare</h3>
            <ul>
        """
        
        # Add top 5 items
        sorted_items = sorted(item_results.items(), 
                            key=lambda x: x[1]['next_day'], 
                            reverse=True)[:5]
        
        for item_name, predictions in sorted_items:
            html += f"<li><strong>{item_name}:</strong> {predictions['next_day']} units</li>"
        
        html += """
            </ul>
            
            <p>Access the full dashboard for detailed insights.</p>
          </body>
        </html>
        """
        
        part = MIMEText(html, 'html')
        msg.attach(part)
        
        # Send email
        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)
            print(f"📧 Email sent to {RECIPIENT_EMAIL}")
        except Exception as e:
            print(f"⚠️  Failed to send email: {str(e)}")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        print("🛑 Scheduler stopped")


# Update app.py to start scheduler
# Add to create_app() function:
# scheduler = ForecastScheduler(app)
# scheduler.start()