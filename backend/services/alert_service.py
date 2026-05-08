from datetime import datetime, timedelta
from backend.database.models import (db, InventoryAlert, Forecast, Sales, 
                            Ingredient, WasteLog, ModelMetadata, Recipe, ItemForecast)
import numpy as np

class AlertService:
    """Comprehensive alert generation and management system"""
    
    def __init__(self, outlet_id):
        self.outlet_id = outlet_id
        self.alert_thresholds = {
            'demand_spike': 0.20,      # 20% above average
            'demand_drop': 0.20,       # 20% below average
            'low_accuracy': 0.75,      # Below 75% accuracy
            'high_waste': 50.0,        # $50+ waste per week
            'stock_critical': 1.0      # Days of stock remaining
        }
    
    def generate_all_alerts(self, forecast_id=None):
        """
        Generate all types of alerts
        
        Returns:
            dict with counts per alert type
        """
        print(f"\n{'='*60}")
        print(f"GENERATING ALERTS FOR OUTLET {self.outlet_id}")
        print(f"{'='*60}\n")
        
        alerts_created = {
            'demand_spike': 0,
            'demand_drop': 0,
            'low_stock': 0,
            'high_waste': 0,
            'low_accuracy': 0,
            'data_quality': 0,
            'reorder_needed': 0
        }
        
        # 1. Check for demand spikes/drops
        if forecast_id:
            spike_alerts = self._check_demand_anomalies(forecast_id)
            alerts_created['demand_spike'] = len([a for a in spike_alerts if 'spike' in a.alert_type])
            alerts_created['demand_drop'] = len([a for a in spike_alerts if 'drop' in a.alert_type])
        
        # 2. Check inventory levels
        stock_alerts = self._check_inventory_levels()
        alerts_created['low_stock'] = len(stock_alerts)
        
        # 3. Check waste levels
        waste_alerts = self._check_waste_levels()
        alerts_created['high_waste'] = len(waste_alerts)
        
        # 4. Check model accuracy
        accuracy_alerts = self._check_model_accuracy()
        alerts_created['low_accuracy'] = len(accuracy_alerts)
        
        # 5. Check data quality
        quality_alerts = self._check_data_quality()
        alerts_created['data_quality'] = len(quality_alerts)
        
        # 6. Check stock vs upcoming demand
        if forecast_id:
            reorder_alerts = self._check_upcoming_demand(forecast_id)
            alerts_created['reorder_needed'] = len(reorder_alerts)
        
        print(f"\n✅ Alert Generation Complete")
        print(f"   Total alerts created: {sum(alerts_created.values())}")
        for alert_type, count in alerts_created.items():
            if count > 0:
                print(f"   - {alert_type}: {count}")
        
        return alerts_created

    def _check_upcoming_demand(self, forecast_id):
        """Check if current stock can meet upcoming demand from forecast"""
        print(f"   🔮 Checking stock vs upcoming demand for forecast {forecast_id}...")
        alerts = []
        
        item_forecasts = db.session.query(ItemForecast).filter_by(
            forecast_id=forecast_id
        ).all()
        
        for item_forecast in item_forecasts:
            recipes = db.session.query(Recipe, Ingredient).join(
                Ingredient, Recipe.ingredient_id == Ingredient.id
            ).filter(Recipe.food_item_id == item_forecast.food_item_id).all()
            
            for recipe, ingredient in recipes:
                needed = item_forecast.predicted_quantity * recipe.quantity_needed
                
                if ingredient.current_stock < needed:
                    shortage = needed - ingredient.current_stock
                    alert = self._create_alert(
                        ingredient_id=ingredient.id,
                        alert_type='reorder',
                        message=f"Upcoming demand requires {needed:.1f} {ingredient.unit} of {ingredient.name}, but only {ingredient.current_stock:.1f} is in stock. Order {shortage:.1f} more!",
                        severity='high'
                    )
                    alerts.append(alert)
                    print(f"      ⚠️  SHORTAGE PREDICTED: {ingredient.name}")
        
        return alerts
    
    def _check_demand_anomalies(self, forecast_id):
        """Check for unusual demand predictions"""
        alerts = []
        
        # Get forecast
        forecast = db.session.query(Forecast).get(forecast_id)
        if not forecast:
            return alerts
        
        # Get historical average
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        historical_sales = db.session.query(Sales).filter(
            Sales.outlet_id == self.outlet_id,
            Sales.date >= thirty_days_ago
        ).all()
        
        if not historical_sales:
            return alerts
        
        # Calculate average
        daily_customers = {}
        for sale in historical_sales:
            date_key = sale.date
            daily_customers[date_key] = daily_customers.get(date_key, 0) + sale.customer_count
        
        avg_customers = np.mean(list(daily_customers.values()))
        std_customers = np.std(list(daily_customers.values()))
        
        predicted = forecast.predicted_customers
        
        # Check for spike
        spike_threshold = avg_customers * (1 + self.alert_thresholds['demand_spike'])
        if predicted > spike_threshold:
            alert = self._create_alert(
                ingredient_id=None,
                alert_type='demand_spike',
                message=f"High demand predicted: {predicted} customers (avg: {int(avg_customers)}). Prepare extra inventory!",
                severity='high'
            )
            alerts.append(alert)
            print(f"   🔥 DEMAND SPIKE ALERT: {predicted} vs avg {int(avg_customers)}")
        
        # Check for drop
        drop_threshold = avg_customers * (1 - self.alert_thresholds['demand_drop'])
        if predicted < drop_threshold:
            alert = self._create_alert(
                ingredient_id=None,
                alert_type='demand_drop',
                message=f"Low demand predicted: {predicted} customers (avg: {int(avg_customers)}). Reduce ordering to avoid waste.",
                severity='medium'
            )
            alerts.append(alert)
            print(f"   📉 DEMAND DROP ALERT: {predicted} vs avg {int(avg_customers)}")
        
        return alerts
    
    def _check_inventory_levels(self):
        """Check if any ingredients are below reorder level"""
        alerts = []
        
        ingredients = db.session.query(Ingredient).all()
        
        for ingredient in ingredients:
            if ingredient.current_stock <= ingredient.reorder_level:
                # Calculate days of stock remaining
                # Simple estimation: current_stock / daily_usage
                days_remaining = self._estimate_days_remaining(ingredient)
                
                severity = 'high' if days_remaining < 2 else 'medium'
                
                alert = self._create_alert(
                    ingredient_id=ingredient.id,
                    alert_type='low_stock',
                    message=f"{ingredient.name} is low: {ingredient.current_stock:.1f} {ingredient.unit} remaining (~{days_remaining:.1f} days). Reorder level: {ingredient.reorder_level}",
                    severity=severity
                )
                alerts.append(alert)
                print(f"   ⚠️  LOW STOCK: {ingredient.name} - {days_remaining:.1f} days left")
        
        return alerts
    
    def _estimate_days_remaining(self, ingredient):
        """Estimate how many days of stock remain"""
        # Get recent usage
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        recent_sales = db.session.query(Sales).filter(
            Sales.outlet_id == self.outlet_id,
            Sales.date >= thirty_days_ago
        ).all()
        
        # Estimate daily usage (simplified)
        if not recent_sales:
            return 0
        
        total_days = 30
        # Assuming 10% of current stock is used daily (rough estimate)
        daily_usage = ingredient.reorder_level / 7  # Reorder level = 1 week supply
        
        if daily_usage <= 0:
            return 999
        
        return ingredient.current_stock / daily_usage
    
    def _check_waste_levels(self):
        """Check for high waste levels"""
        alerts = []
        
        seven_days_ago = datetime.now().date() - timedelta(days=7)
        
        # Get waste logs from last 7 days
        waste_logs = db.session.query(WasteLog).filter(
            WasteLog.outlet_id == self.outlet_id,
            WasteLog.date >= seven_days_ago
        ).all()
        
        # Group by ingredient
        waste_by_ingredient = {}
        for log in waste_logs:
            ing_id = log.ingredient_id
            waste_by_ingredient[ing_id] = waste_by_ingredient.get(ing_id, 0) + log.cost_impact
        
        # Check if any ingredient has high waste
        for ingredient_id, total_waste in waste_by_ingredient.items():
            if total_waste > self.alert_thresholds['high_waste']:
                ingredient = db.session.query(Ingredient).get(ingredient_id)
                
                alert = self._create_alert(
                    ingredient_id=ingredient_id,
                    alert_type='high_waste',
                    message=f"High waste detected for {ingredient.name}: ${total_waste:.2f} wasted in last 7 days. Consider reducing order quantities.",
                    severity='high'
                )
                alerts.append(alert)
                print(f"   🗑️  HIGH WASTE: {ingredient.name} - ${total_waste:.2f}")
        
        return alerts
    
    def _check_model_accuracy(self):
        """Check if forecast accuracy is below threshold"""
        alerts = []
        
        # Get recent forecasts with actual data
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        
        forecasts = db.session.query(Forecast).filter(
            Forecast.outlet_id == self.outlet_id,
            Forecast.forecast_date >= thirty_days_ago
        ).all()
        
        if not forecasts:
            return alerts
        
        # Calculate accuracy for each forecast
        accuracies = []
        for forecast in forecasts:
            # Get actual sales for that date
            actual_sales = db.session.query(Sales).filter(
                Sales.outlet_id == self.outlet_id,
                Sales.date == forecast.forecast_date
            ).all()
            
            if actual_sales:
                actual_customers = sum(sale.customer_count for sale in actual_sales)
                predicted_customers = forecast.predicted_customers
                
                if actual_customers > 0:
                    error_pct = abs(predicted_customers - actual_customers) / actual_customers
                    accuracy = 1 - error_pct
                    accuracies.append(accuracy)
        
        if accuracies:
            avg_accuracy = np.mean(accuracies)
            
            if avg_accuracy < self.alert_thresholds['low_accuracy']:
                alert = self._create_alert(
                    ingredient_id=None,
                    alert_type='low_accuracy',
                    message=f"Model accuracy is low: {avg_accuracy*100:.1f}% (threshold: {self.alert_thresholds['low_accuracy']*100}%). Model retraining recommended.",
                    severity='high'
                )
                alerts.append(alert)
                print(f"   📊 LOW ACCURACY: {avg_accuracy*100:.1f}%")
        
        return alerts
    
    def _check_data_quality(self):
        """Check for data quality issues"""
        alerts = []
        
        # Get recent sales data
        seven_days_ago = datetime.now().date() - timedelta(days=7)
        recent_sales = db.session.query(Sales).filter(
            Sales.outlet_id == self.outlet_id,
            Sales.date >= seven_days_ago
        ).all()
        
        if len(recent_sales) < 5:
            alert = self._create_alert(
                ingredient_id=None,
                alert_type='data_quality',
                message=f"Insufficient recent data: only {len(recent_sales)} records in last 7 days. Upload more data for accurate forecasts.",
                severity='medium'
            )
            alerts.append(alert)
            print(f"   📝 DATA QUALITY: Only {len(recent_sales)} recent records")
        
        return alerts
    
    def _create_alert(self, ingredient_id, alert_type, message, severity):
        """Create and save alert to database"""
        
        # Check for duplicate unresolved alerts
        existing = db.session.query(InventoryAlert).filter_by(
            outlet_id=self.outlet_id,
            ingredient_id=ingredient_id,
            alert_type=alert_type,
            is_resolved=False
        ).first()
        
        if existing:
            # Update existing alert
            existing.message = message
            existing.severity = severity
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
    
    def get_active_alerts(self, severity=None):
        """Get all unresolved alerts, optionally filtered by severity"""
        query = db.session.query(InventoryAlert).filter(
            InventoryAlert.outlet_id == self.outlet_id,
            InventoryAlert.is_resolved == False
        )
        
        if severity:
            query = query.filter(InventoryAlert.severity == severity)
        
        alerts = query.order_by(InventoryAlert.created_at.desc()).all()
        
        result = []
        for alert in alerts:
            ingredient_name = None
            if alert.ingredient_id:
                ingredient = db.session.query(Ingredient).get(alert.ingredient_id)
                ingredient_name = ingredient.name if ingredient else None
            
            result.append({
                'id': alert.id,
                'type': alert.alert_type,
                'message': alert.message,
                'severity': alert.severity,
                'ingredient': ingredient_name,
                'created_at': alert.created_at.isoformat()
            })
        
        return result
    
    def resolve_alert(self, alert_id):
        """Mark alert as resolved"""
        alert = db.session.query(InventoryAlert).get(alert_id)
        
        if alert:
            alert.is_resolved = True
            alert.resolved_at = datetime.now()
            db.session.commit()
            return True
        
        return False
    
    def configure_thresholds(self, thresholds):
        """Update alert thresholds"""
        self.alert_thresholds.update(thresholds)
        print(f"✅ Alert thresholds updated: {self.alert_thresholds}")
