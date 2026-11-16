from yahoo_manager import yahoo_manager
import time

print("Testing Yahoo Manager...")
try:
    print("Fetching NIFTY price...")
    price = yahoo_manager.get_live_price('nifty')
    print(f"Price: {price}")
except Exception as e:
    print(f"Error fetching price: {e}")

try:
    print("Fetching Option Chain...")
    oc = yahoo_manager.get_option_chain('nifty')
    print(f"Option Chain keys: {oc.keys() if oc else 'None'}")
except Exception as e:
    print(f"Error fetching option chain: {e}")
