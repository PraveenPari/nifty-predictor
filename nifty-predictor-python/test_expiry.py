from breeze_connect import BreezeConnect
import sys
import os
sys.path.append(os.getcwd())
from pro_config.api_config import BREEZE_API_KEY, BREEZE_SECRET_KEY
from datetime import datetime, timedelta

print("Initializing Breeze...")
breeze = BreezeConnect(api_key=BREEZE_API_KEY)
try:
    breeze.generate_session(api_secret=BREEZE_SECRET_KEY, session_token='54440984')
    print("Session generated.")
except Exception as e:
    print(f"Session failed: {e}")
    sys.exit(1)


print("Fetching NIFTY Contract List to find Expiry format...")

try:
    # Try get_names functionality if SDK has it. Or 'get_scrip_details' is probably not collection.
    # Breeze SDK usually has 'get_names' to fetch script list.
    contracts = breeze.get_names(exchange_code="nfo", stock_code="NIFTY")
    
    if contracts and contracts.get('Success'):
        print("Success! Found NIFTY contracts.")
        data = contracts['Success']
        # Print first 5 items to see format
        for i in range(min(5, len(data))):
             print(data[i])
             
        # Find unique expiry dates
        expiries = set()
        for c in data:
            if 'expiry_date' in c:
                expiries.add(c['expiry_date'])
        
        print("\nFound Expiry Strings found in metadata:")
        for e in sorted(list(expiries)):
            print(f"  '{e}'")
            
    else:
        print(f"get_names Failed: {contracts}")
        
except Exception as e:
    print(f"Error querying contracts: {e}")
    # Fallback: maybe method name is different?
    print("Available methods:", [m for m in dir(breeze) if 'names' in m or 'script' in m or 'contract' in m])
