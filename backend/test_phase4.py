import requests
import json

BASE_URL = 'http://localhost:5000/api'

def test_generate_forecast():
    """Test forecast generation"""
    print("\n1️⃣  Testing Forecast Generation...")
    
    url = f'{BASE_URL}/forecast/generate'
    data = {
        'outlet_id': 24,
        'model_type': 'auto',
        'days_ahead': 7
    }
    
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.json()['data']['forecast_id']


def test_get_forecast(forecast_id):
    """Test retrieving forecast"""
    print(f"\n2️⃣  Testing Get Forecast #{forecast_id}...")
    
    url = f'{BASE_URL}/forecast/{forecast_id}'
    response = requests.get(url)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_latest_forecast():
    """Test getting latest forecast"""
    print("\n3️⃣  Testing Latest Forecast...")
    
    url = f'{BASE_URL}/forecast/latest/24'
    response = requests.get(url)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_forecast_history():
    """Test forecast history"""
    print("\n4️⃣  Testing Forecast History...")
    
    url = f'{BASE_URL}/forecast/history/1?limit=5'
    response = requests.get(url)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


if __name__ == '__main__':
    print("="*60)
    print("TESTING PHASE 4 - FORECASTING SERVICE")
    print("="*60)
    
    # Run tests
    forecast_id = test_generate_forecast()
    test_get_forecast(forecast_id)
    test_latest_forecast()
    test_forecast_history()
    
    print("\n✅ All tests completed!")