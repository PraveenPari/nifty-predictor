"""
Breeze test - test_breeze_raw.py (secrets via environment)
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

print("=" * 60)
print("  BREEZE API RAW REQUEST TEST")
print("=" * 60)

# This is what Breeze SDK calls internally
url = "https://api.icicidirect.com/breezeapi/api/v1/customerdetails"
headers = {
    "Content-Type": "application/json",
}
payload = {
    "SessionToken": SESSION_TOKEN,
    "AppKey": API_KEY
}

print(f"\n[1] Calling: {url}")
print(f"[2] Payload: {payload}")

try:
    response = requests.get(
        f"https://api.icicidirect.com/breezeapi/api/v1/customerdetails?SessionToken={SESSION_TOKEN}&AppKey={API_KEY}",
        timeout=10
    )
    print(f"\n[3] Status: {response.status_code}")
    print(f"[4] Response: {response.text}")
except Exception as e:
    print(f"[ERROR] {e}")

# Also try the auth endpoint
print("\n" + "=" * 60)
print("  Testing Auth Endpoint")
print("=" * 60)

auth_url = f"https://api.icicidirect.com/breezeapi/api/v1/apisession/validate?SessionToken={SESSION_TOKEN}&AppKey={API_KEY}"
try:
    response = requests.get(auth_url, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"[ERROR] {e}")
