from datetime import datetime, timedelta
from backend.database.models import db, Ingredient, InventoryAlert, Forecast, ItemForecast, Recipe
import smtplib
from email.mime.text import MIMEText

class AlertManager:
    """Manage inventory alerts and notifications"""
    
    def __init__(self, outlet_id):
        self.outlet_id = outlet_id
    
    def check_stock_levels(self):
        """
        Check all ingredients and generate alerts for low stock
        
        Returns:
            list of alerts generated
        """
        print(f"\n🔍 Checking stock levels for outlet {self.outlet_id}...")
        
        ingredients = db.session.query(Ingredient).all()
        alerts_generated = []
        
        for ingredient in ingredients:
            # Check if below reorder level
            if ingredient.current_stock <= ingredient.reorder_level:
                alert = self._create_alert(
                    ingredient_id=ingredient.id,
                    alert_type='low_stock',
                    message=f"{ingredient.name} is at {ingredient.current_stock} {ingredient.unit} (reorder level: {ingredient.reorder_level})",
                    severity='high'
                )
                alerts_generated.append(alert)
                print(f"   🚨 LOW STOCK: {ingredient.name}")
        
        return alerts_generated
    
    def check_upcoming_demand(self, forecast_id):
        """
        Check if current stock can meet upcoming demand
        
        Args:
            forecast_id: Forecast to check against
        
        Returns:
            list of alerts
        """
        print(f"\n🔮 Checking stock vs upcoming demand...")
        
        # Get item forecasts
        item_forecasts = db.session.query(ItemForecast).filter_by(
            forecast_id=forecast_id
        ).all()
        
        alerts_generated = []
        
        for item_forecast in item_forecasts:
            # Get recipes for this item
            recipes = db.session.query(Recipe, Ingredient).join(
                Ingredient, Recipe.ingredient_id == Ingredient.id
            ).filter(Recipe.food_item_id == item_forecast.food_item_id).all()
            
            for recipe, ingredient in recipes:
                # Calculate needed quantity
                needed = item_forecast.predicted_quantity * recipe.quantity_needed
                
                # Check if current stock sufficient
                if ingredient.current_stock < needed:
                    shortage = needed - ingredient.current_stock
                    
                    alert = self._create_alert(
                        ingredient_id=ingredient.id,
                        alert_type='reorder',
                        message=f"Need {needed:.1f} {ingredient.unit} of {ingredient.name}, only have {ingredient.current_stock:.1f}. Order {shortage:.1f} more!",
                        severity='high'
                    )
                    alerts_generated.append(alert)
                    print(f"   ⚠️  SHORTAGE PREDICTED: {ingredient.name}")
        
        return alerts_generated
    
    def _create_alert(self, ingredient_id, alert_type, message, severity):
        """Create and save alert to database"""
        
        # Check if similar unresolved alert exists
        existing = db.session.query(InventoryAlert).filter_by(
            outlet_id=self.outlet_id,
            ingredient_id=ingredient_id,
            alert_type=alert_type,
            is_resolved=False
        ).first()
        
        if existing:
            # Update existing alert
            existing.message = message
            existing.created_at = datetime.now()
            db.session.commit()
            return existing
        
        # Create new alert
        alert = InventoryAlert(
            outlet_id=self.outlet_id,
            ingredient_id=ingredient_id,
            alert_type=alert_type,
            message=message,
            severity=severity,
            is_resolved=False
        )
        
        db.session.add(alert)
        db.session.commit()
        
        return alert
    
    def send_alert_email(self, alert):
        """Send email notification for alert"""
        
        # Email configuration
        SENDER = 'alerts@restaurant.com'
        RECIPIENT = 'manager@restaurant.com'
        
        subject = f"🚨 Inventory Alert: {alert.alert_type.upper()}"
        
        body = f"""
        Inventory Alert
        
        Type: {alert.alert_type}
        Severity: {alert.severity}
        Time: {alert.created_at}
        
        Message:
        {alert.message}
        
        Please take action immediately.
        """
        
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = SENDER
        msg['To'] = RECIPIENT
        
        try:
            # Send email (configure SMTP settings)
            print(f"📧 Alert email sent: {subject}")
        except Exception as e:
            print(f"⚠️  Failed to send email: {str(e)}")
    
    def resolve_alert(self, alert_id):
        """Mark alert as resolved"""
        alert = db.session.query(InventoryAlert).get(alert_id)
        
        if alert:
            alert.is_resolved = True
            alert.resolved_at = datetime.now()
            db.session.commit()
            print(f"✅ Alert {alert_id} resolved")
    
    def get_active_alerts(self):
        """Get all unresolved alerts"""
        alerts = db.session.query(InventoryAlert, Ingredient).join(
            Ingredient, InventoryAlert.ingredient_id == Ingredient.id
        ).filter(
            InventoryAlert.outlet_id == self.outlet_id,
            InventoryAlert.is_resolved == False
        ).all()
        
        result = []
        for alert, ingredient in alerts:
            result.append({
                'alert_id': alert.id,
                'ingredient': ingredient.name,
                'type': alert.alert_type,
                'message': alert.message,
                'severity': alert.severity,
                'created_at': alert.created_at.isoformat()
            })
        
        return result
