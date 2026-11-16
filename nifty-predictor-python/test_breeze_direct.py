"""
Breeze test - test_breeze_direct.py (secrets via environment)
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

from breeze_connect import BreezeConnect

print("=" * 60)
print("  BREEZE DIRECT CONNECTION TEST")
print("=" * 60)

print(f"\n[1] API Key: {API_KEY}")
print(f"[2] Secret Key: {SECRET_KEY[:20]}...")
print(f"[3] Session Token: {SESSION_TOKEN}")

print("\n[4] Creating BreezeConnect...")
breeze = BreezeConnect(api_key=API_KEY)

print("\n[5] Generating session...")
try:
    result = breeze.generate_session(api_secret=SECRET_KEY, session_token=SESSION_TOKEN)
    print(f"[SUCCESS] Session generated! Result: {result}")
    
    # Test a simple API call
    print("\n[6] Testing get_customer_details...")
    details = breeze.get_customer_details()
    print(f"Customer: {details}")
    
except Exception as e:
    print(f"[ERROR] Failed: {e}")
    import traceback
    traceback.print_exc()
