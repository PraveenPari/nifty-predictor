"""Quick debug script to test analysis endpoint"""
import traceback
try:
    from app import get_market_analysis
    result = get_market_analysis('nifty')
    print('Result keys:', list(result.keys()))
    if 'error' in result:
        print('ERROR:', result.get('error'))
        print('Message:', result.get('message'))
    else:
        print('Price:', result.get('price_data', {}).get('ltp'))
        print('Direction:', result.get('prediction', {}).get('direction'))
except Exception as e:
    traceback.print_exc()
