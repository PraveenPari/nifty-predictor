from breeze_connect import BreezeConnect
from datetime import datetime
import sys
import os

# Hardcoded credentials from config for standalone test
try:
    from pro_config.api_config import BREEZE_API_KEY, BREEZE_SECRET_KEY
except:
    # Fallback if import fails
    BREEZE_API_KEY = "1L999c8849796Y64573a`y553k478445"
    BREEZE_SECRET_KEY = "`IDU6723#1382=C6y917c6U72D9K362("

SESSION_TOKEN = "54440984"

print(f"Testing Post-Market Data Access at {datetime.now()}")
print(f"Token: {SESSION_TOKEN}")

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
