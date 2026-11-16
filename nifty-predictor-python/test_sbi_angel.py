import os
import sys
from dotenv import load_dotenv

os.chdir(r"e:\onedrive_data\OneDrive - Applied Data Finance LLC\WORKOUT CODE\nifty-predictor-python")
sys.path.append(os.getcwd())
load_dotenv()

from angel_option_chain_optimized import AngelOneOptionChain
import json

# Load credentials
api_key = os.getenv('ANGEL_ONE_API_KEY')
client_code = os.getenv('ANGEL_ONE_CLIENT_ID')
password = os.getenv('ANGEL_ONE_PASSWORD')
totp_secret = os.getenv('ANGEL_ONE_TOTP_SECRET')

fetcher = AngelOneOptionChain(api_key, client_code, password, totp_secret)

if fetcher.login():
    try:
        # Get spot price
        # SBIN token is 3045
        data = fetcher.smart_api.ltpData("NSE", "SBIN-EQ", "3045")
        spot_price = float(data['data']['ltp'])
        print(f"SBIN Spot Price: {spot_price}")
        
        # Calculate ATM strike (usually multiples of 5 for SBIN)
        atm_strike = round(spot_price / 5) * 5
        
        # Get expiry
        # Monthly options typically expire last Thursday. For July 2026, it's 30JUL26.
        expiry = "30JUL26"
        
        # Generate strikes
        num_strikes = 5
        strikes = []
        for i in range(-num_strikes, num_strikes + 1):
            strikes.append(atm_strike + (i * 5))
            
        print(f"Fetching strikes: {strikes}")
        
        option_chain = []
        for strike in strikes:
            # Construct symbols directly
            # Format usually: SBIN30JUL26850CE
            ce_symbol = f"SBIN{expiry}{strike}CE"
            pe_symbol = f"SBIN{expiry}{strike}PE"
            
            option_chain.append({
                'strike': strike,
                'ce_symbol': ce_symbol,
                'pe_symbol': pe_symbol
            })
            
        with open('sbi_angel_oc.json', 'w') as f:
            json.dump({'spot_price': spot_price, 'expiry': expiry, 'chain': option_chain}, f, indent=2)
            
        print("Done. Saved to sbi_angel_oc.json")
    except Exception as e:
        print(f"Error: {e}")
    
    fetcher.logout()
else:
    print("Login failed")
