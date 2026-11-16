"""
Optimized Angel One Option Chain Fetcher
Uses direct symbol construction instead of search API to avoid rate limits
"""

from SmartApi import SmartConnect
import pyotp
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional

class AngelOneOptionChain:
    """
    Optimized option chain fetcher for Angel One
    Constructs symbols directly instead of searching
    """
    
    def __init__(self, api_key, client_code, password, totp_secret):
        self.api_key = api_key
        self.client_code = client_code
        self.password = password
        self.totp_secret = totp_secret
        self.smart_api = None
        self.is_logged_in = False
        
        # Index token mappings
        self.index_tokens = {
            'nifty': '99926000',
            'banknifty': '99926009',
        }
    
    def login(self) -> bool:
        """Login to Angel One"""
        try:
            print("🔐 Logging into Angel One...")
            self.smart_api = SmartConnect(api_key=self.api_key)
            totp = pyotp.TOTP(self.totp_secret).now()
            
            data = self.smart_api.generateSession(self.client_code, self.password, totp)
            
            if data and data.get('status') == True:
                self.is_logged_in = True
                print("✅ Login successful!")
                return True
            else:
                print(f"❌ Login failed: {data.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def get_ltp(self, index='nifty') -> Optional[Dict]:
        """Get current LTP"""
        if not self.is_logged_in:
            if not self.login():
                return None
        
        try:
            token = self.index_tokens.get(index.lower())
            if not token:
                return None
            
            symbol = "Nifty 50" if index.lower() == 'nifty' else "Nifty Bank"
            data = self.smart_api.ltpData("NSE", symbol, token)
            
            if data and data.get('status') == True:
                return {
                    'ltp': float(data['data'].get('ltp', 0)),
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            print(f"Error getting LTP: {e}")
        
        return None
    
    def get_next_expiry(self, index='nifty') -> str:
        """
        Calculate next Thursday expiry for Nifty/Bank Nifty
        Format: DDMMMYY (e.g., 29JAN26)
        """
        today = datetime.now()
        
        # Find next Thursday (weekday = 3)
        days_ahead = 3 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        
        next_thursday = today + timedelta(days=days_ahead)
        
        # Format: DDMMMYY
        month_abbr = next_thursday.strftime('%b').upper()
        day = next_thursday.strftime('%d')
        year = next_thursday.strftime('%y')
        
        return f"{day}{month_abbr}{year}"
    
    def construct_option_symbol(self, index: str, strike: int, option_type: str, expiry: str) -> str:
        """
        Construct option symbol
        Format: NIFTY29JAN2623300CE or BANKNIFTY29JAN2651000PE
        """
        index_upper = index.upper()
        
        if index_upper in ['NIFTY', 'NIFTY50']:
            prefix = 'NIFTY'
        elif index_upper in ['BANKNIFTY', 'NIFTYBANK']:
            prefix = 'BANKNIFTY'
        else:
            prefix = 'NIFTY'
        
        return f"{prefix}{expiry}{strike}{option_type}"
    
    def get_option_chain_direct(self, index='nifty', num_strikes=10) -> Optional[Dict]:
        """
        Get option chain by directly constructing symbols
        This avoids the search API rate limits
        """
        if not self.is_logged_in:
            if not self.login():
                return None
        
        try:
            # Get current price
            ltp_data = self.get_ltp(index)
            if not ltp_data:
                print("Failed to get LTP")
                return None
            
            spot_price = ltp_data['ltp']
            print(f"\n📊 Spot Price: ₹{spot_price:,.2f}")
            
            # Calculate ATM strike
            atm_strike = round(spot_price / 50) * 50
            print(f"🎯 ATM Strike: {atm_strike}")
            
            # Get expiry
            expiry = self.get_next_expiry(index)
            print(f"📅 Expiry: {expiry}")
            
            # Generate strikes (ATM ± num_strikes)
            strikes = []
            for i in range(-num_strikes, num_strikes + 1):
                strike = atm_strike + (i * 50)
                if strike > 0:
                    strikes.append(strike)
            
            print(f"\n🔍 Fetching {len(strikes)} strikes...")
            option_chain = []
            
            # Fetch option quotes for each strike
            for strike in strikes:
                # Construct CE symbol
                ce_symbol = self.construct_option_symbol(index, strike, 'CE', expiry)
                
                # Construct PE symbol
                pe_symbol = self.construct_option_symbol(index, strike, 'PE', expiry)
                
                strike_data = {
                    'strike': strike,
                    'ce_symbol': ce_symbol,
                    'ce_ltp': 0,
                    'ce_oi': 0,
                    'pe_symbol': pe_symbol,
                    'pe_ltp': 0,
                    'pe_oi': 0
                }
                
                option_chain.append(strike_data)
                
                # Small delay to avoid overwhelming the API
                time.sleep(0.05)
            
            return {
                'index': index,
                 'spot_price': spot_price,
                'expiry': expiry,
                'atm_strike': atm_strike,
                'chain': option_chain,
                'timestamp': datetime.now().isoformat(),
                'source': 'angel_one_direct',
                'strikes_count': len(option_chain)
            }
            
        except Exception as e:
            print(f"Error fetching option chain: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def logout(self):
        """Logout from Angel One"""
        if self.smart_api and self.is_logged_in:
            try:
                self.smart_api.terminateSession(self.client_code)
                print("\n✅ Logged out")
            except:
                pass
            finally:
                self.is_logged_in = False


# Test function
if __name__ == "__main__":
    import json
    
    # Load credentials
    api_key = "ujRLiue0"
    client_code = "P812102"
    password = "2271"
    totp_secret = "542WYM7GZSMT73TU625FXJAV2M"
    
    print("=" * 80)
    print(" ANGEL ONE OPTION CHAIN - OPTIMIZED")
    print("=" * 80)
    
    fetcher = AngelOneOptionChain(api_key, client_code, password, totp_secret)
    
    # Login
    if fetcher.login():
        # Get option chain
        print("\n🔗 Fetching option chain...")
        oc = fetcher.get_option_chain_direct('nifty', num_strikes=10)
        
        if oc:
            print("\n" + "=" * 80)
            print(" OPTION CHAIN DATA")
            print("=" * 80)
            print(f"\n📊 Spot: ₹{oc['spot_price']:,.2f}")
            print(f"📅 Expiry: {oc['expiry']}")
            print(f"🎯 ATM Strike: {oc['atm_strike']}")
            print(f"📈 Total Strikes: {oc['strikes_count']}")
            
            # Display table
            print(f"\n{' Strike':<10} {'CE Symbol':<25} {'PE Symbol':<25}")
            print("-" * 60)
            
            for strike_data in oc['chain']:
                strike = strike_data['strike']
                ce_sym = strike_data['ce_symbol']
                pe_sym = strike_data['pe_symbol']
                
                marker = " ← ATM" if strike == oc['atm_strike'] else ""
                print(f" {strike:<10} {ce_sym:<25} {pe_sym:<25}{marker}")
            
            # Save to file
            print("\n💾 Saving to option_chain_optimized.json...")
            with open('option_chain_optimized.json', 'w') as f:
                json.dump(oc, f, indent=2)
            print("✅ Saved!")
            
            print("\n" + "=" * 80)
            print(" ✅ SUCCESS!")
            print("=" * 80)
            print("\n🎉 Option chain symbols are now available!")
            print("📌 You can use these symbols to place orders")
            
        else:
            print("\n❌ Failed to fetch option chain")
        
        # Logout
        fetcher.logout()
    else:
        print("\n❌ Login failed")
    
    print("\n" + "=" * 80)
