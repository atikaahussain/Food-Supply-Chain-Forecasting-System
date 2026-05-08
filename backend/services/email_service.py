import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import os

class EmailService:
    """Handle email notifications"""
    
    def __init__(self):
        # Email configuration from environment variables
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.sender_email = os.getenv('SENDER_EMAIL', 'noreply@restaurant.com')
        self.sender_password = os.getenv('SENDER_PASSWORD', '')
        self.enabled = bool(self.sender_password)  # Only enable if password is set
        
        if not self.enabled:
            print("⚠️  Email service disabled: No SMTP credentials configured")
    
    def send_forecast_notification(self, recipient_email, forecast_data, outlet_name, attachment_path=None):
        """
        Send forecast notification email
        
        Args:
            recipient_email: Email address to send to
            forecast_data: Dict with forecast information
            outlet_name: Name of the outlet
            attachment_path: Path to PDF/Excel report to attach
        """
        if not self.enabled:
            print("📧 Email notification skipped (no SMTP config)")
            return False
        
        subject = f"Daily Forecast - {outlet_name} - {datetime.now().strftime('%Y-%m-%d')}"
        
        # HTML email body
        html_body = f"""
        <html>
          <head>
            <style>
              body {{ font-family: Arial, sans-serif; }}
              .header {{ background-color: #1976d2; color: white; padding: 20px; }}
              .content {{ padding: 20px; }}
              .metric {{ background-color: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }}
              .metric-value {{ font-size: 32px; font-weight: bold; color: #1976d2; }}
              .metric-label {{ color: #666; }}
              table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
              th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
              th {{ background-color: #1976d2; color: white; }}
              .alert {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 10px 0; }}
            </style>
          </head>
          <body>
            <div class="header">
              <h1>🍽️ Daily Forecast Report</h1>
              <p>{outlet_name} - {datetime.now().strftime('%B %d, %Y')}</p>
            </div>
            
            <div class="content">
              <h2>Tomorrow's Prediction</h2>
              <div class="metric">
                <div class="metric-label">Expected Customers</div>
                <div class="metric-value">{forecast_data.get('next_day_prediction', 'N/A')}</div>
              </div>
              
              <div class="metric">
                <div class="metric-label">Confidence Level</div>
                <div class="metric-value">{int(forecast_data.get('confidence_level', 0) * 100)}%</div>
              </div>
              
              <div class="metric">
                <div class="metric-label">Model Used</div>
                <div class="metric-value" style="font-size: 18px;">{forecast_data.get('model_used', 'N/A').upper()}</div>
              </div>
              
              <h2>Next Week Outlook</h2>
              <table>
                <tr>
                  <th>Date</th>
                  <th>Predicted Customers</th>
                </tr>
        """
        
        # Add weekly predictions
        for i, (date, customers) in enumerate(zip(
            forecast_data.get('forecast_dates', []),
            forecast_data.get('next_week_predictions', [])
        )):
            html_body += f"""
                <tr>
                  <td>{date}</td>
                  <td>{customers}</td>
                </tr>
            """
        
        html_body += """
              </table>
              
              <h2>Top Items to Prepare</h2>
              <ul>
        """
        
        # Add item forecasts
        item_forecasts = forecast_data.get('item_forecasts', {})
        sorted_items = sorted(
            item_forecasts.items(),
            key=lambda x: x[1].get('next_day', 0) if isinstance(x[1], dict) else x[1],
            reverse=True
        )[:5]
        
        for item_name, data in sorted_items:
            quantity = data.get('next_day', data) if isinstance(data, dict) else data
            html_body += f"<li><strong>{item_name}:</strong> {quantity} units</li>"
        
        html_body += """
              </ul>
              
              <div class="alert">
                <strong>💡 Tip:</strong> Access the full dashboard for detailed insights and inventory recommendations.
              </div>
              
              <p style="color: #666; font-size: 12px; margin-top: 40px;">
                This is an automated email from the Food Forecasting System.
              </p>
            </div>
          </body>
        </html>
        """
        
        return self._send_email(recipient_email, subject, html_body, attachment_path)
    
    def send_alert_notification(self, recipient_email, alerts, outlet_name):
        """
        Send alert notification email
        
        Args:
            recipient_email: Email address
            alerts: List of alert dicts
            outlet_name: Outlet name
        """
        if not self.enabled:
            print("📧 Alert email skipped (no SMTP config)")
            return False
        
        high_severity_count = len([a for a in alerts if a.get('severity') == 'high'])
        
        subject = f"⚠️ Inventory Alerts - {outlet_name} ({high_severity_count} High Priority)"
        
        html_body = f"""
        <html>
          <head>
            <style>
              body {{ font-family: Arial, sans-serif; }}
              .header {{ background-color: #d32f2f; color: white; padding: 20px; }}
              .content {{ padding: 20px; }}
              .alert-high {{ background-color: #ffebee; border-left: 4px solid #d32f2f; padding: 15px; margin: 10px 0; }}
              .alert-medium {{ background-color: #fff3e0; border-left: 4px solid #ff9800; padding: 15px; margin: 10px 0; }}
              .alert-low {{ background-color: #e3f2fd; border-left: 4px solid #2196f3; padding: 15px; margin: 10px 0; }}
            </style>
          </head>
          <body>
            <div class="header">
              <h1>⚠️ Inventory Alerts</h1>
              <p>{outlet_name} - {datetime.now().strftime('%B %d, %Y %I:%M %p')}</p>
            </div>
            
            <div class="content">
              <h2>Active Alerts: {len(alerts)}</h2>
              <p><strong>High Priority:</strong> {high_severity_count}</p>
        """
        
        # Group alerts by severity
        for severity in ['high', 'medium', 'low']:
            severity_alerts = [a for a in alerts if a.get('severity') == severity]
            
            if severity_alerts:
                html_body += f"<h3>{severity.upper()} Priority Alerts</h3>"
                
                for alert in severity_alerts:
                    html_body += f"""
                    <div class="alert-{severity}">
                      <strong>{alert.get('type', 'Alert').replace('_', ' ').title()}</strong>
                      <p>{alert.get('message', '')}</p>
                      <small>Created: {alert.get('created_at', '')}</small>
                    </div>
                    """
        
        html_body += """
              <p style="margin-top: 30px;">
                <strong>Action Required:</strong> Please review these alerts in the dashboard and take appropriate action.
              </p>
            </div>
          </body>
        </html>
        """
        
        return self._send_email(recipient_email, subject, html_body)
    
    def send_weekly_summary(self, recipient_email, summary_data, outlet_name):
        """
        Send weekly performance summary
        
        Args:
            recipient_email: Email address
            summary_data: Dict with weekly metrics
            outlet_name: Outlet name
        """
        if not self.enabled:
            print("📧 Weekly summary email skipped (no SMTP config)")
            return False
        
        subject = f"Weekly Summary - {outlet_name} - Week of {datetime.now().strftime('%B %d, %Y')}"
        
        html_body = f"""
        <html>
          <head>
            <style>
              body {{ font-family: Arial, sans-serif; }}
              .header {{ background-color: #4caf50; color: white; padding: 20px; }}
              .content {{ padding: 20px; }}
              .metric-card {{ background-color: #f5f5f5; padding: 20px; margin: 15px 0; border-radius: 5px; display:inline-block; width: 45%; }}
              .metric-value {{ font-size: 36px; font-weight: bold; color: #4caf50; }}
              .metric-label {{ color: #666; font-size: 14px; }}
              .positive {{ color: #4caf50; }}
              .negative {{ color: #f44336; }}
            </style>
          </head>
          <body>
            <div class="header">
              <h1>📊 Weekly Performance Summary</h1>
              <p>{outlet_name} - {datetime.now().strftime('%B %d, %Y')}</p>
            </div>
            
            <div class="content">
              <h2>This Week's Metrics</h2>
              
              <div class="metric-card">
                <div class="metric-label">Total Customers</div>
                <div class="metric-value">{summary_data.get('total_customers', 0)}</div>
                <div class="positive">+{summary_data.get('customer_change', 0)}% vs last week</div>
              </div>
              
              <div class="metric-card">
                <div class="metric-label">Total Revenue</div>
                <div class="metric-value">${summary_data.get('total_revenue', 0):,.2f}</div>
                <div class="positive">+{summary_data.get('revenue_change', 0)}% vs last week</div>
              </div>
              
              <div class="metric-card">
                <div class="metric-label">Forecast Accuracy</div>
                <div class="metric-value">{summary_data.get('accuracy', 0)}%</div>
                <div class="positive">+{summary_data.get('accuracy_change', 0)}% improvement</div>
              </div>
              
              <div class="metric-card">
                <div class="metric-label">Food Waste</div>
                <div class="metric-value">${summary_data.get('waste_cost', 0):.2f}</div>
                <div class="negative">-{summary_data.get('waste_reduction', 0)}% vs last week</div>
              </div>
              
              <h2>Key Highlights</h2>
              <ul>
                <li>Busiest Day: {summary_data.get('busiest_day', 'N/A')}</li>
                <li>Top Selling Item: {summary_data.get('top_item', 'N/A')}</li>
                <li>Cost Savings: ${summary_data.get('cost_savings', 0):.2f}</li>
              </ul>
              
              <p style="margin-top: 30px;">
                Keep up the great work! Continue using data-driven insights to optimize your operations.
              </p>
            </div>
          </body>
        </html>
        """
        
        return self._send_email(recipient_email, subject, html_body)
    
    def _send_email(self, recipient, subject, html_body, attachment_path=None):
        """
        Internal method to send email via SMTP
        
        Args:
            recipient: Email address
            subject: Email subject
            html_body: HTML content
            attachment_path: Optional path to file attachment
        
        Returns:
            bool: Success status
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = recipient
            
            # Attach HTML body
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Attach file if provided
            if attachment_path and os.path.exists(attachment_path):
                filename = os.path.basename(attachment_path)
                with open(attachment_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename={filename}'
                    )
                    msg.attach(part)
            
            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            print(f"✅ Email sent to {recipient}: {subject}")
            return True
            
        except Exception as e:
            print(f"❌ Email failed: {str(e)}")
            return False


# For testing without SMTP credentials
if __name__ == '__main__':
    email_service = EmailService()
    
    # Test forecast notification
    test_forecast = {
        'next_day_prediction': 95,
        'confidence_level': 0.88,
        'model_used': 'xgboost',
        'forecast_dates': ['2024-01-08', '2024-01-09', '2024-01-10'],
        'next_week_predictions': [95, 102, 88],
        'item_forecasts': {
            'Burger': {'next_day': 45},
            'Pizza': {'next_day': 30},
            'Coffee': {'next_day': 70}
        }
    }
    
    # This will just print a message if SMTP is not configured
    email_service.send_forecast_notification(
        'manager@restaurant.com',
        test_forecast,
        'Main Branch'
    )
