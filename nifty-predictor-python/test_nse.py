from nsepython import nse_optionchain_scrapper
import json

print("Testing NSEPython...")
try:
    print("Fetching NIFTY Option Chain...")
    oc = nse_optionchain_scrapper('NIFTY')
    print("Fetch successful.")
    # Check if we got data
    if oc and 'records' in oc:
        print(f"Expiry dates: {oc['records']['expiryDates'][:3]}")
        print("Data seems valid.")
    else:
        print("Data structure unexpected or empty.")
        print(str(oc)[:200])
except Exception as e:
    print(f"Error fetching from nsepython: {e}")
