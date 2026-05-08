import requests
import json

BASE_URL = 'http://localhost:5000/api'

def test_complete_flow():
    """Test complete inventory planning flow"""
    
    print("\n" + "="*70)
    print("PHASE 5 COMPLETE TEST")
    print("="*70)
    
    # Step 1: Generate forecast
    print("\n1️⃣  Generating forecast...")
    response = requests.post(f'{BASE_URL}/forecast/generate', json={
        'outlet_id': 10,
        'model_type': 'auto',
        'days_ahead': 7
    })

    if response.status_code != 200:
        print(f"   ❌ Forecast generation failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return

    result = response.json()
    forecast_id = result.get('data', {}).get('forecast_id')
    if not forecast_id:
        print(f"   ❌ Unexpected response format: {result}")
        return

    print(f"   ✅ Forecast ID: {forecast_id}")
    
    # Step 2: Get inventory suggestions
    print("\n2️⃣  Getting inventory suggestions...")
    response = requests.get(f'{BASE_URL}/inventory/suggestions/{forecast_id}')
    inventory_data = response.json()
    print(f"   Shopping list items: {inventory_data['shopping_list']['total_items']}")
    print(f"   Total cost: ${inventory_data['shopping_list']['total_cost']}")
    
    # Step 3: View recipe
    print("\n3️⃣  Viewing recipe for item 10...")
    response = requests.get(f'{BASE_URL}/inventory/recipes/10')
    recipe = response.json()
    print(f"   Recipe for: {recipe.get('food_item', 'N/A')}")
    
    # Step 4: Check alerts
    print("\n4️⃣  Checking inventory alerts...")
    response = requests.post(f'{BASE_URL}/inventory/alerts/check/10', json={
        'forecast_id': forecast_id
    })
    alert_data = response.json()
    print(f"   Alerts generated: {alert_data['alerts_generated']}")
    
    # Step 5: Get active alerts
    print("\n5️⃣  Getting active alerts...")
    response = requests.get(f'{BASE_URL}/inventory/alerts/1')
    alerts = response.json()
    print(f"   Active alerts: {alerts['alert_count']}")
    
    print("\n✅ All Phase 5 tests completed!")


if __name__ == '__main__':
    test_complete_flow()