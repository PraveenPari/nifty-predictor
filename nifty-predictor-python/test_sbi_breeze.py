import os
import sys
from dotenv import load_dotenv

# Ensure we're in the right directory
os.chdir(r"e:\onedrive_data\OneDrive - Applied Data Finance LLC\WORKOUT CODE\nifty-predictor-python")
sys.path.append(os.getcwd())

load_dotenv()

try:
    from breeze_connect import BreezeConnect
except ImportError:
    print("Breeze SDK not found")
    sys.exit(1)

from pro_config.api_config import BREEZE_API_KEY, BREEZE_SECRET_KEY, BREEZE_SESSION_TOKEN

print(f"Connecting to Breeze with token: {BREEZE_SESSION_TOKEN[:10]}...")
breeze = BreezeConnect(api_key=BREEZE_API_KEY)
breeze.generate_session(api_secret=BREEZE_SECRET_KEY, session_token=BREEZE_SESSION_TOKEN)

print("Fetching SBI Option Chain...")
# Let's try 30-Jul-2026
expiry_str = "30-Jul-2026"

oc_calls = breeze.get_option_chain_quotes(
    stock_code="SBIN",
    exchange_code="NFO",
    product_type="options",
    expiry_date=expiry_str,
    right="call"
)

oc_puts = breeze.get_option_chain_quotes(
    stock_code="SBIN",
    exchange_code="NFO",
    product_type="options",
    expiry_date=expiry_str,
    right="put"
)

# Also get spot price
quote = breeze.get_quotes(stock_code="SBIN", exchange_code="NSE", product_type="cash")
spot = 0
if quote and 'Success' in quote and quote['Success']:
    spot = float(quote['Success'][0].get('ltp', 0))

print(f"SBI Spot Price: {spot}")

import json
with open("sbi_oc.json", "w") as f:
    json.dump({"calls": oc_calls, "puts": oc_puts}, f, indent=2)

print("Done. Saved to sbi_oc.json")
