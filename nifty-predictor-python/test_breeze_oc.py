"""
Test Breeze Option Chain - Find correct expiry
"""
from breeze_connect import BreezeConnect
from datetime import datetime, timedelta

# Credentials
API_KEY = "1L999c8849796Y64573a`y553k478445"
SECRET_KEY = "`IDU6723#1382=C6y917c6U72D9K362("
SESSION_TOKEN = "54654969"

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
