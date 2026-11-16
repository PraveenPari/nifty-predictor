"""
Debug Breeze API Response - Check what ICICI returns
"""
import requests

# Credentials
API_KEY = "1L999c8849796Y64573a`y553k478445"
SECRET_KEY = "`IDU6723#1382=C6y917c6U72D9K362("
SESSION_TOKEN = "54653418"

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
