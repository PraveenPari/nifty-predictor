"""
Quick Option Chain Test
Tests if Angel One option chain is working
"""

from angel_one_enhanced import angel_one_enhanced
from datetime import datetime
import json

print("=" * 80)
print(" OPTION CHAIN TEST - ANGEL ONE")
print("=" * 80)

# Step 1: Login
print("\n🔐 Step 1: Logging into Angel One...")
if angel_one_enhanced.login():
    print("✅ Login successful!")
    print(f"   Client Code: {angel_one_enhanced.client_code}")
else:
    print("❌ Login failed!")
    print("\n⚠️  Please update your credentials in .env file:")
    print("   ANGEL_ONE_PASSWORD=<your_password>")
    print("   ANGEL_ONE_TOTP_SECRET=<your_totp_secret>")
    print("\nHow to get TOTP secret:")
    print("   1. Login to https://smartapi.angelbroking.com/")
    print("   2. Go to Security Settings")
    print("   3. Enable 2FA/TOTP")
    print("   4. Copy the secret key (long alphanumeric string)")
    exit(1)

# Step 2: Get Current Price
print("\n📊 Step 2: Getting current NIFTY price...")
ltp_data = angel_one_enhanced.get_ltp('nifty')

if ltp_data:
    print(f"✅ NIFTY LTP: ₹{ltp_data['ltp']:,.2f}")
    print(f"   Change: {ltp_data['change']:+.2f} ({ltp_data['change_pct']:+.2f}%)")
    spot_price = ltp_data['ltp']
else:
    print("❌ Failed to get LTP")
    spot_price = 23500  # Fallback

# Step 3: Get Option Chain
print("\n🔗 Step 3: Fetching Option Chain...")
print("⚠️  Note: This may take 30-60 seconds due to API rate limits...")

option_chain = angel_one_enhanced.get_option_chain('nifty')

if option_chain:
    print(f"\n✅ OPTION CHAIN RETRIEVED!")
    print("=" * 80)
    print(f"📌 Spot Price: ₹{option_chain['spot_price']:,.2f}")
    print(f"📅 Expiry: {option_chain['expiry']}")
    print(f"🎯 Strikes Available: {len(option_chain['chain'])}")
    print(f"📡 Source: {option_chain.get('source', 'unknown')}")
    
    if option_chain.get('note'):
        print(f"ℹ️  Note: {option_chain['note']}")
    
    print("\n" + "=" * 80)
    print(" OPTION CHAIN DATA")
    print("=" * 80)
    
    # Display option chain in table format
    print(f"\n{'Strike':<10} {'CE Symbol':<40} {'PE Symbol':<40}")
    print("-" * 90)
    
    for strike_data in option_chain['chain']:
        strike = strike_data['strike']
        ce_symbol = strike_data.get('ce_symbol', 'N/A')[:38]
        pe_symbol = strike_data.get('pe_symbol', 'N/A')[:38]
        
        # Highlight ATM strike
        atm_strike = round(option_chain['spot_price'] / 50) * 50
        marker = " ← ATM" if strike == atm_strike else ""
        
        print(f"{strike:<10} {ce_symbol:<40} {pe_symbol:<40}{marker}")
    
    print("\n" + "=" * 80)
    
    # Save to file
    print("\n💾 Saving option chain to 'option_chain_data.json'...")
    with open('option_chain_data.json', 'w') as f:
        json.dump(option_chain, f, indent=2)
    print("✅ Saved!")
    
    print("\n" + "=" * 80)
    print(" TEST COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print("\n✅ Option chain is working!")
    print("✅ You can now use it in your trading application")
    print("\n💡 Access via API:")
    print("   GET http://localhost:5000/api/option-chain?index=nifty")
    
else:
    print("\n❌ OPTION CHAIN NOT AVAILABLE")
    print("\n⚠️  Possible reasons:")
    print("   1. Angel One API limitations for option chain")
    print("   2. Market is closed")
    print("   3. API rate limiting")
    print("\n💡 Fallback: The system will use Yahoo Finance for option chain")

# Logout
print("\n🔓 Logging out...")
angel_one_enhanced.logout()
print("✅ Done!")
print("=" * 80)
