from yahoo_manager import yahoo_manager
import time

print("Testing Yahoo Manager...")
try:
    oc = yahoo_manager.get_option_chain('nifty')
    if oc:
        print(f"Success! Source: {oc.get('source')}")
        chain = oc.get('chain')
        if chain:
             print(f"Chain length: {len(chain)}")
             print(f"First strike: {chain[0]}")
        else:
             print("Chain is empty")
    else:
        print("Failed to get option chain (None returned)")

except Exception as e:
    print(f"Exception: {e}")
