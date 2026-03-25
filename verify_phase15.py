import requests
import time
import os

BASE_URL = "http://localhost:8000"

def test_verification():
    print("1. Simulating conversation data...")
    events = [
        {"type": "transcript", "text": "This is a test message for export verification."},
        {"type": "transcript", "text": "Action item: Deploy to production."}
    ]
    try:
        requests.post(f"{BASE_URL}/debug/simulate", json=events, timeout=5)
    except Exception as e:
        print(f"Simulation warning: {e}")
    
    time.sleep(2)
    
    print("\n2. Testing /session/save...")
    res = requests.post(f"{BASE_URL}/session/save")
    if res.status_code == 200:
        print(f"✅ Success: {res.json()}")
    else:
        print(f"❌ Failed: {res.text}")
        
    print("\n3. Testing /export/json...")
    res = requests.post(f"{BASE_URL}/export/json")
    if res.status_code == 200:
        print(f"✅ Success: {res.json()}")
    else:
        print(f"❌ Failed: {res.text}")

    print("\n4. Testing /export/csv...")
    res = requests.post(f"{BASE_URL}/export/csv")
    if res.status_code == 200:
        print(f"✅ Success: {res.json()}")
    else:
        print(f"❌ Failed: {res.text}")

if __name__ == "__main__":
    try:
        test_verification()
    except Exception as e:
        print(f"Test failed failed: {e}")
