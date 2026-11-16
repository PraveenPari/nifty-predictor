"""
Test Script: Breeze API Option Chain
Tests if we can fetch option chain data from Breeze API with current session
"""

from breeze_connect import BreezeConnect
from datetime import datetime, timedelta
import json

# Import credentials from config
from pro_config.api_config import BREEZE_API_KEY, BREEZE_SECRET_KEY

def get_next_expiry(index='nifty'):
    """Calculate next weekly expiry date - CORRECTED"""
    today = datetime.now()
    
    # NIFTY expires on Thursday (3), BANKNIFTY on Wednesday (2)
    target_weekday = 2 if index.lower() == 'banknifty' else 3
    
    days_ahead = target_weekday - today.weekday()
    
    # If today IS the expiry day, use today (before 3:30 PM cutoff)
    # If expiry day has passed this week, go to next week
    if days_ahead < 0:
        days_ahead += 7
    # If days_ahead == 0, it means today is the expiry day - use today
    
    expiry_date = today + timedelta(days=days_ahead)
    
    # Format: DD-MMM-YYYY (e.g., 22-Jan-2026)
    formatted = expiry_date.strftime("%d-%b-%Y")
    print(f"    DEBUG: Calculated expiry for {index}: {formatted} (today is {today.strftime('%A, %d-%b-%Y')})")
    return formatted


def test_option_chain():
    print("="*60)
    print("  BREEZE API - OPTION CHAIN TEST")
    print("="*60)
    
    # Initialize Breeze
    print(f"\n[1] Initializing BreezeConnect...")
    print(f"    API Key: {BREEZE_API_KEY[:10]}...")
    
    breeze = BreezeConnect(api_key=BREEZE_API_KEY)
    
    # Get session token from user
    print("\n[2] Session Token Required")
    print("    Please login at:")
    print(f"    https://api.icicidirect.com/api/v2/login?api_key={BREEZE_API_KEY}")
    print()
    
    session_token = input("    Enter session token: ").strip()
    
    if not session_token:
        print("    ERROR: No session token provided!")
        return
    
    # Generate session
    print(f"\n[3] Generating session with token: {session_token[:10]}...")
    try:
        breeze.generate_session(api_secret=BREEZE_SECRET_KEY, session_token=session_token)
        print("    ✅ Session authenticated!")
    except Exception as e:
        print(f"    ❌ Session auth failed: {e}")
        return
    
    # Calculate expiry
    nifty_expiry = get_next_expiry('nifty')
    banknifty_expiry = get_next_expiry('banknifty')
    
    print(f"\n[4] Calculated Expiries:")
    print(f"    NIFTY: {nifty_expiry}")
    print(f"    BANKNIFTY: {banknifty_expiry}")
    
    # Test NIFTY Option Chain - CALLS
    print(f"\n[5] Fetching NIFTY CALL Option Chain...")
    try:
        nifty_calls = breeze.get_option_chain_quotes(
            stock_code="NIFTY",
            exchange_code="NFO",
            product_type="options",
            expiry_date=nifty_expiry,
            right="call",
            strike_price=""  # Empty = all strikes
        )
        
        if nifty_calls and nifty_calls.get('Success'):
            print(f"    ✅ SUCCESS! Got {len(nifty_calls['Success'])} CALL options")
            
            # Show sample data
            if len(nifty_calls['Success']) > 0:
                sample = nifty_calls['Success'][0]
                print(f"\n    Sample CALL Option:")
                print(f"    Strike: {sample.get('strike_price')}")
                print(f"    LTP: {sample.get('ltp') or sample.get('last_price')}")
                print(f"    OI: {sample.get('open_interest')}")
                print(f"    IV: {sample.get('implied_volatility', 'N/A')}")
        else:
            print(f"    ⚠️ No data returned: {nifty_calls}")
            
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Test NIFTY Option Chain - PUTS
    print(f"\n[6] Fetching NIFTY PUT Option Chain...")
    try:
        nifty_puts = breeze.get_option_chain_quotes(
            stock_code="NIFTY",
            exchange_code="NFO",
            product_type="options",
            expiry_date=nifty_expiry,
            right="put",
            strike_price=""
        )
        
        if nifty_puts and nifty_puts.get('Success'):
            print(f"    ✅ SUCCESS! Got {len(nifty_puts['Success'])} PUT options")
        else:
            print(f"    ⚠️ No data returned: {nifty_puts}")
            
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Test BANKNIFTY Option Chain
    print(f"\n[7] Fetching BANKNIFTY Option Chain...")
    try:
        banknifty_calls = breeze.get_option_chain_quotes(
            stock_code="CNXBAN",  # BankNifty code in Breeze
            exchange_code="NFO",
            product_type="options",
            expiry_date=banknifty_expiry,
            right="call",
            strike_price=""
        )
        
        if banknifty_calls and banknifty_calls.get('Success'):
            print(f"    ✅ SUCCESS! Got {len(banknifty_calls['Success'])} CALL options")
        else:
            print(f"    ⚠️ No data returned: {banknifty_calls}")
            
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("  TEST COMPLETE")
    print("="*60)
    print("\nIf you see SUCCESS messages above, option chain is working!")
    print("If not, your Breeze account may need F&O subscription/permissions.")


if __name__ == "__main__":
    test_option_chain()
