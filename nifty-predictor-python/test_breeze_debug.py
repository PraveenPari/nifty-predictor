"""
Direct Breeze API Test - Debug Option Chain
Tests directly calling the Breeze API to see exact error response
"""
from breeze_connect import BreezeConnect
from datetime import datetime, timedelta
from pro_config.api_config import BREEZE_API_KEY, BREEZE_SECRET_KEY, BREEZE_SESSION_TOKEN
import json

print("="*60)
print("  DIRECT BREEZE OPTION CHAIN TEST")
print("="*60)

# Initialize
breeze = BreezeConnect(api_key=BREEZE_API_KEY)

# Use the session token provided by user
SESSION_TOKEN = BREEZE_SESSION_TOKEN or ""
if not SESSION_TOKEN:
    print("Set BREEZE_SESSION_TOKEN in server secrets first.")
    raise SystemExit(1)

print("\n[1] Authenticating with session token...")
try:
    breeze.generate_session(api_secret=BREEZE_SECRET_KEY, session_token=SESSION_TOKEN)
    print("✅ Session authenticated!")
except Exception as e:
    print(f"❌ Auth failed: {e}")
    exit(1)

# Today is Wednesday January 22, 2026
today = datetime.now()
print(f"\n[2] Today is: {today.strftime('%A, %d-%b-%Y')}")

# Calculate expiries
# BANKNIFTY expires Wednesday (today), NIFTY expires Thursday (tomorrow)
banknifty_expiry = today.strftime("%d-%b-%Y")  # Today
nifty_expiry = (today + timedelta(days=1)).strftime("%d-%b-%Y")  # Tomorrow

print(f"  NIFTY expiry: {nifty_expiry}")
print(f"  BANKNIFTY expiry: {banknifty_expiry}")

# Test NIFTY using "NIFTY" stock code
print(f"\n[3] Testing NIFTY option chain...")
print(f"  Stock Code: NIFTY")
print(f"  Exchange: NFO")
print(f"  Expiry: {nifty_expiry}")

try:
    result = breeze.get_option_chain_quotes(
        stock_code="NIFTY",
        exchange_code="NFO",
        product_type="options",
        expiry_date=nifty_expiry,
        right="call",
        strike_price=""
    )
    
    print(f"\n  Raw Response Type: {type(result)}")
    print(f"  Raw Response: {json.dumps(result, indent=2, default=str)[:1000]}")
    
    if result and result.get('Success'):
        print(f"\n  ✅ SUCCESS! Got {len(result['Success'])} options")
    elif result and result.get('Error'):
        print(f"\n  ❌ Error: {result.get('Error')}")
    else:
        print(f"\n  ⚠️ Unexpected response")
        
except Exception as e:
    print(f"  ❌ Exception: {e}")
    import traceback
    traceback.print_exc()

# Test with different expiry format (ISO)
print(f"\n[4] Testing with ISO format expiry...")
iso_expiry = (today + timedelta(days=1)).strftime("%Y-%m-%d")  # 2026-01-23
print(f"  ISO Expiry: {iso_expiry}")

try:
    result2 = breeze.get_option_chain_quotes(
        stock_code="NIFTY",
        exchange_code="NFO",
        product_type="options",
        expiry_date=iso_expiry,
        right="call",
        strike_price=""
    )
    print(f"  Response: {json.dumps(result2, indent=2, default=str)[:500]}")
except Exception as e:
    print(f"  ❌ Exception: {e}")

# Test BANKNIFTY with CNXBAN code  
print(f"\n[5] Testing BANKNIFTY (code: CNXBAN)...")
try:
    result3 = breeze.get_option_chain_quotes(
        stock_code="CNXBAN",
        exchange_code="NFO",
        product_type="options",
        expiry_date=banknifty_expiry,
        right="call",
        strike_price=""
    )
    print(f"  Response: {json.dumps(result3, indent=2, default=str)[:500]}")
except Exception as e:
    print(f"  ❌ Exception: {e}")

# Test with BANKNIFTY code instead
print(f"\n[6] Testing BANKNIFTY (code: BANKNIFTY)...")
try:
    result4 = breeze.get_option_chain_quotes(
        stock_code="BANKNIFTY",
        exchange_code="NFO",
        product_type="options",
        expiry_date=banknifty_expiry,
        right="call",
        strike_price=""
    )
    print(f"  Response: {json.dumps(result4, indent=2, default=str)[:500]}")
except Exception as e:
    print(f"  ❌ Exception: {e}")

print("\n" + "="*60)
print("  TEST COMPLETE")
print("="*60)
