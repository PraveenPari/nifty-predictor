import requests
import json

base_url = "http://127.0.0.1:5000"

def test_endpoint(endpoint):
    print(f"Testing {endpoint}...")
    try:
        response = requests.get(f"{base_url}{endpoint}", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Success")
            # print(str(response.json())[:100])
        else:
            print(f"Failed: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

test_endpoint("/api/status")
test_endpoint("/api/analysis")
test_endpoint("/api/option-chain")
