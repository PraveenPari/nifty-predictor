"""
Breeze test - test_breeze_api.py (secrets via environment)
NOTE: Credentials are loaded ONLY from environment / .env secrets.
Set BREEZE_API_KEY, BREEZE_SECRET_KEY, BREEZE_SESSION_TOKEN first.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from secrets_manager import get_breeze_credentials, is_breeze_configured, mask

_creds = get_breeze_credentials()
API_KEY = _creds["api_key"]
SECRET_KEY = _creds["secret_key"]
SESSION_TOKEN = _creds["session_token"]
BREEZE_API_KEY, BREEZE_SECRET_KEY = API_KEY, SECRET_KEY

if not is_breeze_configured():
    print("[SKIP] Breeze secrets not set. Export BREEZE_API_KEY / "
          "BREEZE_SECRET_KEY / BREEZE_SESSION_TOKEN (or add to .env) and re-run.")
    sys.exit(2)
print("[SECRETS] Using Breeze key " + mask(API_KEY) + " from environment.")

import requests
import json

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
