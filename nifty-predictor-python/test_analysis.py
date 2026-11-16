
import sys
import os
import traceback
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

print("Testing market analysis...", flush=True)

try:
    from app import get_market_analysis, get_simulator
    print("Imported app successfully", flush=True)

    print("Running for NIFTY...", flush=True)
    res = get_market_analysis('nifty')
    print("NIFTY Result Keys:", list(res.keys()), flush=True)

    print("Running for BANKNIFTY...", flush=True)
    res_bn = get_market_analysis('banknifty')
    print("BANKNIFTY Result Keys:", list(res_bn.keys()), flush=True)

    import json
    # Try to serialize to JSON to check for numpy issues
    print("Attempting to serialize to JSON...", flush=True)
    json_str = json.dumps(res, default=str) # Using default=str acts as fallback but pure json might fail if no default provided, but flask uses something else?
    # Actually flask jsonify is slightly better but let's see if simple dump fails. 
    # Usually numpy types need special handling.
    # Let's try without default=str first to see strict failure, but flask jsonify isn't that strict.
    # However, app.py uses jsonify. 
    print("JSON serialization successful (with default=str).")
    
    # Check for numpy types explicitly
    import numpy as np
    def check_numpy(obj):
        if isinstance(obj, (np.integer, np.floating, np.ndarray)):
            return True
        if isinstance(obj, dict):
            return any(check_numpy(v) for v in obj.values())
        if isinstance(obj, list):
            return any(check_numpy(v) for v in obj)
        return False
    
    if check_numpy(res):
        print("WARNING: Numpy types detected in response!", flush=True)
    else:
        print("No numpy types detected.", flush=True)
    
    print("SUCCESS", flush=True)

except Exception as e:
    print("ERROR DURING EXECUTION:", flush=True)
    print(str(e), flush=True)
    traceback.print_exc()
