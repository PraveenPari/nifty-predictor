"""
Debug Breeze - Try calling the customer details API directly to see the real response
"""
import requests
import json

# Credentials
API_KEY = "1L999c8849796Y64573a`y553k478445"
SECRET_KEY = "`IDU6723#1382=C6y917c6U72D9K362("
SESSION_TOKEN = "54654969"

print("=" * 60)
print("  BREEZE API DIRECT CUSTOMER DETAILS TEST")
print("=" * 60)

# This is EXACTLY what the SDK does
url = "https://api.icicidirect.com/breezeapi/api/v1/customerdetails"
headers = {
    "Content-Type": "application/json"
}
body = {
    "SessionToken": SESSION_TOKEN,
    "AppKey": API_KEY
}
body_str = json.dumps(body, separators=(',', ':'))

print(f"\n[1] URL: {url}")
print(f"[2] Headers: {headers}")
print(f"[3] Body: {body_str}")

response = requests.get(url=url, data=body_str, headers=headers)
print(f"\n[4] Status Code: {response.status_code}")
print(f"[5] Raw Response: {response.text}")

try:
    json_resp = response.json()
    print(f"\n[6] JSON Response:")
    for key, value in json_resp.items():
        print(f"    {key}: {value}")
except:
    pass
