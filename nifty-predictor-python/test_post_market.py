"""
Breeze test - test_post_market.py (secrets via environment)
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
from datetime import datetime

print(f"Testing Post-Market Data Access at {datetime.now()}")
print("Token: " + mask(SESSION_TOKEN))

b = BreezeConnect(api_key=BREEZE_API_KEY)
try:
    b.generate_session(api_secret=BREEZE_SECRET_KEY, session_token=SESSION_TOKEN)
    print("Session generation: Attempted")
except Exception as e:
    print(f"Session generation failed: {e}")
    sys.exit(1)

print("\n1. Testing get_quotes (LTP)...")
try:
    # NIFTY
    q = b.get_quotes(stock_code="NIFTY", exchange_code="NSE", product_type="cash")
    print(f"NIFTY Quote RAW: {q}")
except Exception as e:
    print(f"NIFTY Quote Error: {e}")

print("\n2. Testing get_historical_data_v2 (Today's Data)...")
try:
    # NIFTY
    # Use today's date
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%dT09:15:00.000Z")
    # For to_date, use now or end of market
    end_str = now.strftime("%Y-%m-%dT15:30:00.000Z")
    
    h = b.get_historical_data_v2(
        interval="1day",
        from_date=today_str,
        to_date=end_str,
        stock_code="NIFTY",
        exchange_code="NSE",
        product_type="cash"
    )
    print(f"NIFTY Historical RAW: {str(h)[:200]}...") # Truncate for readability
except Exception as e:
    print(f"NIFTY Historical Error: {e}")
