import requests
import json

try:
    response = requests.get('http://127.0.0.1:5000/api/option-chain?index=nifty')
    data = response.json()
    
    if 'chain' not in data:
        print("FAIL: No chain data found")
        print(data)
    else:
        chain = data['chain']
        valid_premiums = 0
        total_strikes = len(chain)
        
        for row in chain:
            if row.get('ce_ltp', 0) > 0 or row.get('pe_ltp', 0) > 0:
                valid_premiums += 1
                
        if valid_premiums > 0:
            print(f"SUCCESS: Found {valid_premiums}/{total_strikes} strikes with valid premiums.")
            print(f"Source: {data.get('source')}")
            print(f"First row: {chain[0]}")
        else:
            print("FAIL: Chain has data but ALL premiums are 0.")
            print(f"Source: {data.get('source')}")

except Exception as e:
    print(f"ERROR: {e}")
