"""
Breeze test - test_simple.py (secrets via environment)
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

print("Initializing...")
b = BreezeConnect(api_key=BREEZE_API_KEY)
# b.generate_session(api_secret=BREEZE_SECRET_KEY, session_token=SESSION_TOKEN)
# Use provided session directly if possible? No, generating session is needed.
try:
    b.generate_session(api_secret=BREEZE_SECRET_KEY, session_token=SESSION_TOKEN)
    print("Session OK")
except Exception as e:
    print(f"Session Error: {e}")

print("Testing BANKNIFTY Expiries: Today vs Next Week")

expiries = ["21-JAN-2026", "28-JAN-2026", "22-JAN-2026"]

for exp in expiries:
    print(f"\nQuerying {exp}...")
    try:
        q = b.get_option_chain_quotes(
            stock_code="CNXBAN", 
            exchange_code="nfo", 
            product_type="options", 
            expiry_date=exp, 
            right="call"
        )
        if q.get('Success'):
            print(f"SUCCESS for {exp}!")
            print("Sample:", q['Success'][0])
        else:
            print(f"FAILED for {exp}: {q.get('Error')}")
            if q.get('Status'): print(f"Status: {q.get('Status')}")
            
    except Exception as e:
        print(f"Exception for {exp}: {e}")
