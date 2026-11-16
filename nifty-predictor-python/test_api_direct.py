"""Direct test of get_market_analysis function"""
import sys
import traceback
from app import get_market_analysis

print("="*60)
print("Testing get_market_analysis directly")
print("="*60)

try:
    result = get_market_analysis('nifty')
    print("\n✓ SUCCESS!")
    print(f"Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
    if isinstance(result, dict) and 'error' in result:
        print(f"\nERROR in result: {result}")
    else:
        print(f"\nPrice: {result.get('price_data', {}).get('ltp', 'N/A')}")
        print(f"Prediction: {result.get('prediction', {})}")
except Exception as e:
    print(f"\n✗ EXCEPTION: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
