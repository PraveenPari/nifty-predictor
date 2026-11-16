"""
Breeze API Full Debug - Try Multiple Methods
"""
from breeze_connect import BreezeConnect
from datetime import datetime, timedelta
from pro_config.api_config import BREEZE_API_KEY, BREEZE_SECRET_KEY
import json

print("="*60)
print("  BREEZE API FULL DEBUG TEST")
print("="*60)

# Initialize
breeze = BreezeConnect(api_key=BREEZE_API_KEY)
SESSION_TOKEN = "54455470"

print(f"\n[1] Authenticating...")
try:
    breeze.generate_session(api_secret=BREEZE_SECRET_KEY, session_token=SESSION_TOKEN)
    print("✅ Authenticated!")
except Exception as e:
    print(f"❌ Auth failed: {e}")
    exit(1)

# Test 1: Get simple quotes first (should work if authenticated)
print("\n[2] Testing get_quotes (basic quote - should always work)...")
try:
    quote = breeze.get_quotes(
        stock_code="NIFTY",
        exchange_code="NSE",
        product_type="cash"
    )
    print(f"Quote Response: {json.dumps(quote, indent=2, default=str)[:500]}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Get customer details
print("\n[3] Testing get_customer_details (check account info)...")
try:
    details = breeze.get_customer_details()
    print(f"Customer Details: {json.dumps(details, indent=2, default=str)[:500]}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Get demat holdings
print("\n[4] Testing get_demat_holdings...")
try:
    holdings = breeze.get_demat_holdings()
    print(f"Holdings: {json.dumps(holdings, indent=2, default=str)[:300]}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: Calculate proper expiry dates
print("\n[5] Calculating expiry dates...")
today = datetime.now()
print(f"Current datetime: {today}")
print(f"Day of week: {today.strftime('%A')} (weekday={today.weekday()})")

# Try multiple expiry formats
expiries_to_test = [
    "23-Jan-2026",
    "30-Jan-2026", 
    "29-Jan-2026",
    "2026-01-23",
]

print("\n[6] Testing option chain with different expiries...")
for exp in expiries_to_test:
    print(f"\n  Trying expiry: {exp}")
    try:
        result = breeze.get_option_chain_quotes(
            stock_code="NIFTY",
            exchange_code="NFO",
            product_type="options",
            expiry_date=exp,
            right="call",
            strike_price=""
        )
        
        if result and result.get('Success'):
            print(f"  ✅ SUCCESS with {exp}! Got {len(result['Success'])} options")
            break
        elif result and result.get('Error'):
            print(f"  ⚠️ Error: {result.get('Error')}")
        else:
            print(f"  ⚠️ No data: {str(result)[:100]}")
    except Exception as e:
        print(f"  ❌ Exception: {str(e)[:100]}")

# Test 5: Try quotes API for options (not option_chain_quotes)
print("\n[7] Testing get_quotes for F&O...")
try:
    fno_quote = breeze.get_quotes(
        stock_code="NIFTY",
        exchange_code="NFO",
        product_type="options",
        expiry_date="23-Jan-2026",
        right="call",
        strike_price="25400"
    )
    print(f"F&O Quote Response: {json.dumps(fno_quote, indent=2, default=str)[:500]}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)
print("  DEBUG COMPLETE")
print("="*60)
print("\nIf basic quotes work but option chain fails:")
print("  - Your account may not have F&O enabled")
print("  - Contact ICICI Direct to enable F&O segment")
