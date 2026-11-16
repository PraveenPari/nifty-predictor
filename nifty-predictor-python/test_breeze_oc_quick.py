"""
Quick Test: Verify Breeze Option Chain
Uses the existing session from the running app
"""

import sys
sys.path.insert(0, '.')

def test_breeze_option_chain():
    print("=" * 60)
    print("  BREEZE OPTION CHAIN - QUICK TEST")
    print("=" * 60)
    
    try:
        # Try to import and use the existing breeze_manager
        from breeze_manager import breeze_manager
        
        print(f"\n[1] Checking Breeze connection status...")
        print(f"    Connected: {breeze_manager.is_connected()}")
        
        if not breeze_manager.is_connected():
            print("    ❌ Breeze not connected. Need to initialize session first.")
            return False
        
        print(f"\n[2] Testing NIFTY Option Chain...")
        nifty_oc = breeze_manager.get_option_chain('nifty')
        
        if nifty_oc and nifty_oc.get('chain'):
            print(f"    ✅ SUCCESS! Got {len(nifty_oc['chain'])} strikes")
            print(f"    Underlying: {nifty_oc.get('underlying')}")
            print(f"    Expiry: {nifty_oc.get('expiry')}")
            print(f"    Source: {nifty_oc.get('source')}")
            
            # Show sample
            if nifty_oc['chain']:
                sample = nifty_oc['chain'][0]
                print(f"\n    Sample Strike: {sample}")
        else:
            print(f"    ⚠️ No option chain data returned")
            print(f"    Response: {nifty_oc}")
            return False
            
        print(f"\n[3] Testing BANKNIFTY Option Chain...")
        bnf_oc = breeze_manager.get_option_chain('banknifty')
        
        if bnf_oc and bnf_oc.get('chain'):
            print(f"    ✅ SUCCESS! Got {len(bnf_oc['chain'])} strikes")
        else:
            print(f"    ⚠️ No data: {bnf_oc}")
            
        print("\n" + "=" * 60)
        print("  TEST COMPLETE - BREEZE OPTION CHAIN IS WORKING!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_breeze_option_chain()
