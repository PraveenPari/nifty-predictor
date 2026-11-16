from breeze_manager import breeze_manager
import time

print("Testing Breeze Connectivity...")
if breeze_manager.is_connected():
    print("SUCCESS: Breeze is connected!")
    # Test a simple call
    print("Fetching NIFTY price...")
    price = breeze_manager.get_live_price('nifty')
    print(f"Price: {price}")
else:
    print("FAILURE: Breeze is NOT connected.")
    print("Check logs above for details.")
