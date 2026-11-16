"""
Test Script: Breeze API Option Chain - Uses Existing Session
Tests the option chain API using the already authenticated breeze_manager
"""

from datetime import datetime, timedelta
import json

# Import the already authenticated breeze_manager
from breeze_manager import breeze_manager

def get_next_expiry(index='nifty'):
    """Calculate next weekly expiry date"""
    today = datetime.now()
    
    # NIFTY expires on Thursday (3), BANKNIFTY on Wednesday (2)
    target_weekday = 2 if index.lower() == 'banknifty' else 3
    
    days_ahead = target_weekday - today.weekday()
    
    # If today IS the expiry day, use today
    # If expiry day has passed this week, go to next week
    if days_ahead < 0:
        days_ahead += 7
    
    expiry_date = today + timedelta(days=days_ahead)
    formatted = expiry_date.strftime("%d-%b-%Y")
    print(f"  Expiry for {index}: {formatted} (today: {today.strftime('%A, %d-%b-%Y')})")
    return formatted


def test_option_chain():
    print("="*60)
    print("  BREEZE OPTION CHAIN - QUICK TEST")
    print("="*60)
    
    # Check connection
    print("\n[1] Checking Breeze connection...")
    if not breeze_manager.is_connected():
        print("  ❌ Breeze not connected! Please authenticate first.")
        print("  Run the main app and login via the session token.")
        return
    
    print("  ✅ Breeze is connected!")
    
    # Calculate expiries
    print("\n[2] Calculating expiries...")
    nifty_expiry = get_next_expiry('nifty')
    banknifty_expiry = get_next_expiry('banknifty')
    
    # Get underlying price first
    print("\n[3] Getting NIFTY spot price...")
    price = breeze_manager.get_live_price('nifty')
    if price:
        print(f"  NIFTY LTP: {price['ltp']}")
    else:
        print("  ⚠️ Could not get spot price")
    
    # Test NIFTY Calls
    print(f"\n[4] Fetching NIFTY CALL options (expiry: {nifty_expiry})...")
    try:
        nifty_calls = breeze_manager.breeze.get_option_chain_quotes(
            stock_code="NIFTY",
            exchange_code="NFO",
            product_type="options",
            expiry_date=nifty_expiry,
            right="call",
            strike_price=""
        )
        
        print(f"  Raw response: {json.dumps(nifty_calls, indent=2)[:500]}...")
        
        if nifty_calls and nifty_calls.get('Success'):
            print(f"\n  ✅ SUCCESS! Got {len(nifty_calls['Success'])} CALL options")
            
            # Show sample
            if nifty_calls['Success']:
                sample = nifty_calls['Success'][0]
                print(f"\n  Sample Option:")
                for key, val in sample.items():
                    print(f"    {key}: {val}")
        else:
            print(f"\n  ⚠️ Response: {nifty_calls}")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test NIFTY Puts  
    print(f"\n[5] Fetching NIFTY PUT options...")
    try:
        nifty_puts = breeze_manager.breeze.get_option_chain_quotes(
            stock_code="NIFTY",
            exchange_code="NFO", 
            product_type="options",
            expiry_date=nifty_expiry,
            right="put",
            strike_price=""
        )
        
        if nifty_puts and nifty_puts.get('Success'):
            print(f"  ✅ SUCCESS! Got {len(nifty_puts['Success'])} PUT options")
        else:
            print(f"  ⚠️ Response: {nifty_puts}")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    print("\n" + "="*60)
    print("  TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    test_option_chain()
