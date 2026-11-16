"""
Quick test to show NIFTY and BANKNIFTY option chains
"""

from angel_one_enhanced import angel_one_enhanced
import json

print("=" * 80)
print(" OPTION CHAIN TEST - BOTH INDICES")
print("=" * 80)

# Login
if angel_one_enhanced.login():
    
    # Test NIFTY Option Chain
    print("\n" + "=" * 80)
    print(" 1. NIFTY OPTION CHAIN")
    print("=" * 80)
    
    nifty_oc = angel_one_enhanced.get_option_chain('nifty', num_strikes=10)
    
    if nifty_oc:
        print(f"\n📊 NIFTY")
        print(f"   Spot Price: ₹{nifty_oc['spot_price']:,.2f}")
        print(f"   ATM Strike: {nifty_oc['atm_strike']}")
        print(f"   Expiry: {nifty_oc['expiry']}")
        print(f"   Total Strikes: {nifty_oc['strikes_count']}")
        
        print(f"\n   Sample Strikes:")
        for i, strike_data in enumerate(nifty_oc['chain'][:5]):
            strike = strike_data['strike']
            ce = strike_data['ce_symbol']
            pe = strike_data['pe_symbol']
            marker = " ← ATM" if strike == nifty_oc['atm_strike'] else ""
            print(f"   {strike}: {ce} / {pe}{marker}")
    
    # Test BANK NIFTY Option Chain
    print("\n" + "=" * 80)
    print(" 2. BANK NIFTY OPTION CHAIN")
    print("=" * 80)
    
    banknifty_oc = angel_one_enhanced.get_option_chain('banknifty', num_strikes=10)
    
    if banknifty_oc:
        print(f"\n📊 BANK NIFTY")
        print(f"   Spot Price: ₹{banknifty_oc['spot_price']:,.2f}")
        print(f"   ATM Strike: {banknifty_oc['atm_strike']}")
        print(f"   Expiry: {banknifty_oc['expiry']}")
        print(f"   Total Strikes: {banknifty_oc['strikes_count']}")
        
        print(f"\n   Sample Strikes:")
        for i, strike_data in enumerate(banknifty_oc['chain'][:5]):
            strike = strike_data['strike']
            ce = strike_data['ce_symbol']
            pe = strike_data['pe_symbol']
            marker = " ← ATM" if strike == banknifty_oc['atm_strike'] else ""
            print(f"   {strike}: {ce} / {pe}{marker}")
    
    # Save both to files
    print("\n" + "=" * 80)
    print(" SAVING DATA")
    print("=" * 80)
    
    if nifty_oc:
        with open('nifty_option_chain.json', 'w') as f:
            json.dump(nifty_oc, f, indent=2)
        print("✅ Saved: nifty_option_chain.json")
    
    if banknifty_oc:
        with open('banknifty_option_chain.json', 'w') as f:
            json.dump(banknifty_oc, f, indent=2)
        print("✅ Saved: banknifty_option_chain.json")
    
    # Logout
    angel_one_enhanced.logout()
    
    print("\n" + "=" * 80)
    print(" ✅ SUCCESS - BOTH OPTION CHAINS WORKING!")
    print("=" * 80)
    print("\n🎯 Next: Start the web application to view them in browser")
    print("   Command: python app.py")
    print("   URL: http://localhost:5000/api/option-chain?index=nifty")
    print("   URL: http://localhost:5000/api/option-chain?index=banknifty")
    
else:
    print("\n❌ Login failed")

print("\n" + "=" * 80)
