from datetime import datetime, timedelta
from backend.database.models import db, WasteLog, Ingredient, InventorySuggestion, Sales
import pandas as pd

class WasteTracker:
    """Track and analyze food waste to improve inventory planning"""
    
    def __init__(self, outlet_id):
        self.outlet_id = outlet_id
    
    def log_waste(self, ingredient_id, quantity, reason=''):
        """
        Log wasted ingredient
        
        Args:
            ingredient_id: ID of ingredient wasted
            quantity: Amount wasted
            reason: Reason for waste
        """
        ingredient = db.session.query(Ingredient).get(ingredient_id)
        
        if not ingredient:
            raise ValueError(f"Ingredient {ingredient_id} not found")
        
        cost_impact = quantity * ingredient.unit_cost
        
        waste_log = WasteLog(
            outlet_id=self.outlet_id,
            ingredient_id=ingredient_id,
            date=datetime.now().date(),
            quantity_wasted=quantity,
            reason=reason,
            cost_impact=cost_impact
        )
        
        db.session.add(waste_log)
        db.session.commit()
        
        print(f"📝 Waste logged: {quantity} {ingredient.unit} of {ingredient.name}")
        print(f"   Cost impact: ${cost_impact:.2f}")
        print(f"   Reason: {reason}")
        
        return waste_log.id
    
    def analyze_waste_patterns(self, days_back=30):
        """
        Analyze waste patterns over time
        
        Returns:
            dict with waste analysis
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        # Get all waste logs
        waste_logs = db.session.query(WasteLog, Ingredient).join(
            Ingredient, WasteLog.ingredient_id == Ingredient.id
        ).filter(
            WasteLog.outlet_id == self.outlet_id,
            WasteLog.date >= start_date,
            WasteLog.date <= end_date
        ).all()
        
        if not waste_logs:
            return {'message': 'No waste data available'}
        
        # Convert to DataFrame for analysis
        data = []
        for waste_log, ingredient in waste_logs:
            data.append({
                'date': waste_log.date,
                'ingredient': ingredient.name,
                'quantity': waste_log.quantity_wasted,
                'cost': waste_log.cost_impact,
                'reason': waste_log.reason
            })
        
        df = pd.DataFrame(data)
        
        # Calculate metrics
        total_waste_cost = df['cost'].sum()
        avg_daily_waste = total_waste_cost / days_back
        
        # Most wasted ingredients
        top_wasted = df.groupby('ingredient').agg({
            'quantity': 'sum',
            'cost': 'sum'
        }).sort_values('cost', ascending=False)
        
        # Waste by reason
        waste_by_reason = df.groupby('reason')['cost'].sum().to_dict()
        
        result = {
            'period_days': days_back,
            'total_waste_cost': round(total_waste_cost, 2),
            'avg_daily_waste': round(avg_daily_waste, 2),
            'top_wasted_items': top_wasted.head(5).to_dict('index'),
            'waste_by_reason': waste_by_reason
        }
        
        print(f"\n📊 WASTE ANALYSIS (Last {days_back} days)")
        print(f"   Total waste cost: ${total_waste_cost:.2f}")
        print(f"   Average daily: ${avg_daily_waste:.2f}")
        print(f"\n   Top wasted items:")
        for item, values in list(result['top_wasted_items'].items())[:3]:
            print(f"   - {item}: ${values['cost']:.2f}")
        
        return result
    
    def get_waste_reduction_recommendations(self):
        """
        Generate recommendations to reduce waste
        
        Returns:
            list of recommendations
        """
        waste_analysis = self.analyze_waste_patterns(days_back=30)
        
        recommendations = []
        
        if waste_analysis.get('total_waste_cost', 0) > 100:
            recommendations.append({
                'priority': 'high',
                'action': 'Review ordering quantities',
                'reason': f"High waste cost: ${waste_analysis['total_waste_cost']:.2f}"
            })
        
        # Check for specific high-waste items
        top_wasted = waste_analysis.get('top_wasted_items', {})
        for item, values in list(top_wasted.items())[:2]:
            if values['cost'] > 30:
                recommendations.append({
                    'priority': 'medium',
                    'action': f"Reduce {item} order quantity",
                    'reason': f"${values['cost']:.2f} wasted in last 30 days"
                })
        
        # Check waste reasons
        waste_reasons = waste_analysis.get('waste_by_reason', {})
        if waste_reasons.get('expired', 0) > 50:
            recommendations.append({
                'priority': 'high',
                'action': 'Improve FIFO (First In First Out) practice',
                'reason': 'High expiration waste detected'
            })
        
        if waste_reasons.get('over-prepared', 0) > 40:
            recommendations.append({
                'priority': 'medium',
                'action': 'Reduce safety stock buffer',
                'reason': 'Frequently over-preparing ingredients'
            })
        
        return recommendations
    
    def adjust_buffer_based_on_waste(self, current_buffer):
        """
        Suggest buffer adjustment based on waste patterns
        
        Returns:
            float: recommended buffer percentage
        """
        waste_analysis = self.analyze_waste_patterns(days_back=30)
        avg_daily_waste = waste_analysis.get('avg_daily_waste', 0)
        
        # If high waste, reduce buffer
        if avg_daily_waste > 20:
            new_buffer = max(0.05, current_buffer - 0.05)
            print(f"💡 High waste detected. Reduce buffer from {current_buffer*100}% to {new_buffer*100}%")
            return new_buffer
        
        # If low waste, might increase buffer slightly
        elif avg_daily_waste < 5:
            new_buffer = min(0.25, current_buffer + 0.02)
            print(f"💡 Low waste. Can increase buffer from {current_buffer*100}% to {new_buffer*100}%")
            return new_buffer
        
        return current_buffer