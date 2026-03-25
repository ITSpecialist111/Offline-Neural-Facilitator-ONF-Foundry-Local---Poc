import requests
import json
import sys

def test_chat():
    url = "http://localhost:8000/chat"
    payload = {"query": "Hello, who are you?"}
    
    try:
        print(f"Testing POST {url} with payload: {payload}")
        response = requests.post(url, json=payload, timeout=60)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Response JSON:")
            print(json.dumps(response.json(), indent=2))
            return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Exception: {e}")
        return False

if __name__ == "__main__":
    success = test_chat()
    sys.exit(0 if success else 1)
