import os
import sys
import json
from dotenv import load_dotenv
from pprint import pprint

os.chdir(r"e:\onedrive_data\OneDrive - Applied Data Finance LLC\WORKOUT CODE\nifty-predictor-python")
sys.path.append(os.getcwd())
load_dotenv()

from pro_config.api_config import BREEZE_API_KEY, BREEZE_SECRET_KEY, BREEZE_SESSION_TOKEN

try:
    from breeze_connect import BreezeConnect
except ImportError:
    print("Error: breeze_connect package not found in virtual environment.")
    sys.exit(1)

print(f"Authenticating with token: {BREEZE_SESSION_TOKEN[:8]}...")
breeze = BreezeConnect(api_key=BREEZE_API_KEY)
breeze.generate_session(api_secret=BREEZE_SECRET_KEY, session_token=BREEZE_SESSION_TOKEN)

print("Fetching LIVE quotes for SBI (STABAN)...")
quote = breeze.get_quotes(stock_code="STABAN", exchange_code="NSE", product_type="cash")

print("\n--- LIVE BREEZE DATA ---")
pprint(quote)
print("------------------------")
