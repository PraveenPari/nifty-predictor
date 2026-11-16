"""
Breeze test - test_breeze_oc.py (secrets via environment)
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
from datetime import datetime, timedelta

print("=" * 60)
print("  BREEZE OPTION CHAIN TEST")
print("=" * 60)

# Connect
breeze = BreezeConnect(api_key=API_KEY)
breeze.generate_session(api_secret=SECRET_KEY, session_token=SESSION_TOKEN)
print("[OK] Breeze connected!")

# Try different expiry formats
today = datetime.now()
# NIFTY expires Thursday
days_to_thursday = (3 - today.weekday()) % 7
if days_to_thursday == 0 and today.hour >= 15:  # After 3:30 PM on Thursday
    days_to_thursday = 7
next_expiry = today + timedelta(days=days_to_thursday)

# Different date formats to try
formats_to_try = [
    next_expiry.strftime("%d-%b-%Y"),  # 13-Feb-2026
    next_expiry.strftime("%Y-%m-%d"),  # 2026-02-13
    next_expiry.strftime("%d-%m-%Y"),  # 13-02-2026
    next_expiry.strftime("%d%b%Y"),    # 13Feb2026
]

print(f"\n[INFO] Trying expiry date formats around {next_expiry.date()}")

for expiry_format in formats_to_try:
    print(f"\n[TEST] Expiry format: {expiry_format}")
    try:
        result = breeze.get_option_chain_quotes(
            stock_code="NIFTY",
            exchange_code="NFO",
            product_type="options",
            expiry_date=expiry_format,
            right="call"
        )
        if result.get('Success'):
            print(f"  [SUCCESS] Found {len(result['Success'])} options!")
            # Show first option
            if result['Success']:
                print(f"  Sample: Strike={result['Success'][0].get('strike_price')}, LTP={result['Success'][0].get('ltp')}")
            break
        else:
            print(f"  [FAIL] {result.get('Error', 'No success data')}")
    except Exception as e:
        print(f"  [ERROR] {e}")
