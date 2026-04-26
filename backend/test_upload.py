import requests
import os

FILE_PATH = 'data/raw/train.csv'

if not os.path.exists(FILE_PATH):
    print(f"❌ Cannot find {FILE_PATH}")
else:
    with open(FILE_PATH, 'rb') as f:
        files = {'file': f}
        try:
            print("🚀 Sending request...")
            response = requests.post('http://127.0.0.1:5000/api/data/upload', files=files)
            
            print(f"📡 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Success:", response.json())
            else:
                # This prints the HTML error so we can see why it failed
                print("❌ Server Error Content:")
                print(response.text[:500]) 
        except Exception as e:
            print(f"💥 Connection Error: {e}")