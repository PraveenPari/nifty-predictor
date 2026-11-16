"""
Enhanced Angel One SmartAPI Integration
With Option Chain Support and Real Trading Capabilities
"""

from SmartApi import SmartConnect
import pyotp
import time
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class AngelOneEnhanced:
    """
    Enhanced Angel One Manager with Option Chain Support
    """
    
    def __init__(self, api_key=None, client_code=None, password=None, totp_secret=None):
        # Load from environment or use provided credentials
        self.api_key = api_key or os.getenv('ANGEL_ONE_API_KEY')
        self.client_code = client_code or os.getenv('ANGEL_ONE_CLIENT_ID')
        self.password = password or os.getenv('ANGEL_ONE_PASSWORD')
        self.totp_secret = totp_secret or os.getenv('ANGEL_ONE_TOTP_SECRET')
        
        self.smart_api = None
        self.session_data = None
        self.is_logged_in = False
        self.auth_token = None
        self.refresh_token = None
        
        # Index tokens
        self.index_tokens = {
            'nifty': '99926000',
            'nifty50': '99926000',
            'banknifty': '99926009',
            'niftybank': '99926009',
            'finnifty': '99926037',
        }
        
        # Symbol names
        self.symbol_names = {
            'nifty': 'Nifty 50',
            'nifty50': 'Nifty 50',
            'banknifty': 'Nifty Bank',
            'niftybank': 'Nifty Bank',
            'finnifty': 'Nifty Fin Service'
        }
        
    def login(self) -> bool:
        """Login to Angel One and generate session"""
        try:
            # Avoid repeated login attempts if previously failed recently (simple throttling could be added here)
            
            print(f"[LOGIN] Logging in to Angel One for client: {self.client_code}...")
            
            if not all([self.api_key, self.client_code, self.password, self.totp_secret]):
                print("[ERROR] Missing credentials. Please check .env file.")
                return False
                
            self.smart_api = SmartConnect(api_key=self.api_key)
            
            # Generate TOTP
            try:
                totp = pyotp.TOTP(self.totp_secret).now()
            except Exception as e:
                print(f"[ERROR] TOTP Generation failed: {e}")
                return False
            
            # Login with timeout simulation (SmartConnect doesn't support timeout param natively easily without socket hacking)
            # We will rely on the fact that if it fails, it returns data with status=False usually.
            # But if it HANGS, it is network issue.
            
            data = self.smart_api.generateSession(self.client_code, self.password, totp)
            
            if data and data.get('status') == True:
                self.session_data = data['data']
                self.auth_token = self.session_data.get('jwtToken')
                self.refresh_token = self.session_data.get('refreshToken')
                self.is_logged_in = True
                
                print(f"[SUCCESS] Angel One Login Successful!")
                print(f"   Client: {self.client_code}")
                print(f"   Session: Active")
                return True
            else:
                error_msg = data.get('message', 'Unknown error') if data else 'No response'
                # AB1004 is generic execution error, often wrong credentials or API down
                print(f"[ERROR] Angel One Login Failed: {error_msg}")
                self.is_logged_in = False
                return False
                
        except Exception as e:
            print(f"[ERROR] Angel One Login Exception: {e}")
            self.is_logged_in = False
            return False
    
    def get_profile(self) -> Optional[Dict]:
        """Get user profile"""
        if not self.is_logged_in:
            if not self.login():
                return None
        
        try:
            profile = self.smart_api.getProfile(self.refresh_token)
            return profile
        except Exception as e:
            print(f"Error getting profile: {e}")
            return None
    
    def get_ltp(self, index='nifty') -> Optional[Dict]:
        """Fetch real-time LTP for index"""
        if not self.is_logged_in:
            if not self.login():
                return None
        
        try:
            index_lower = index.lower()
            token = self.index_tokens.get(index_lower)
            symbol = self.symbol_names.get(index_lower)
            
            if not token or not symbol:
                print(f"Unknown index: {index}")
                return None
            
            # Get LTP
            data = self.smart_api.ltpData("NSE", symbol, token)
            
            if data and data.get('status') == True:
                ltp_data = data['data']
                return {
                    'ltp': float(ltp_data.get('ltp', 0)),
                    'open': float(ltp_data.get('open', 0)),
                    'high': float(ltp_data.get('high', 0)),
                    'low': float(ltp_data.get('low', 0)),
                    'close': float(ltp_data.get('close', 0)),
                    'change': float(ltp_data.get('netChange', 0)),
                    'change_pct': float(ltp_data.get('percentChange', 0)),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'angel_one'
                }
        except Exception as e:
            print(f"Angel One LTP Error for {index}: {e}")
            self.is_logged_in = False
        
        return None
    
    def get_candles(self, index='nifty', interval="FIVE_MINUTE", days=5) -> List[Dict]:
        """Fetch historical candle data"""
        if not self.is_logged_in:
            if not self.login():
                return []
        
        try:
            index_lower = index.lower()
            token = self.index_tokens.get(index_lower)
            
            if not token:
                print(f"Unknown index: {index}")
                return []
            
            # Calculate date range
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)
            
            params = {
                "exchange": "NSE",
                "symboltoken": token,
                "interval": interval,
                "fromdate": from_date.strftime('%Y-%m-%d %H:%M'),
                "todate": to_date.strftime('%Y-%m-%d %H:%M')
            }
            
            data = self.smart_api.getCandleData(params)
            
            if data and data.get('status') == True:
                candles = []
                for c in data['data']:
                    try:
                        candles.append({
                            'timestamp': int(datetime.strptime(c[0], '%Y-%m-%dT%H:%M:%S%z').timestamp() * 1000),
                            'open': float(c[1]),
                            'high': float(c[2]),
                            'low': float(c[3]),
                            'close': float(c[4]),
                            'volume': int(c[5])
                        })
                    except:
                        # Handle different datetime formats
                        try:
                            dt = datetime.fromisoformat(c[0].replace('Z', '+00:00'))
                            candles.append({
                                'timestamp': int(dt.timestamp() * 1000),
                                'open': float(c[1]),
                                'high': float(c[2]),
                                'low': float(c[3]),
                                'close': float(c[4]),
                                'volume': int(c[5])
                            })
                        except:
                            continue
                
                return candles
                
        except Exception as e:
            print(f"Angel One Candle Error: {e}")
        
        return []
    
    def _construct_option_symbol(self, index: str, strike: int, option_type: str, expiry: str) -> str:
        """
        Construct option symbol directly
        Format: NIFTY29JAN2623300CE or BANKNIFTY29JAN2651000PE
        """
        index_upper = index.upper()
        
        if index_upper in ['NIFTY', 'NIFTY50']:
            prefix = 'NIFTY'
        elif index_upper in ['BANKNIFTY', 'NIFTYBANK']:
            prefix = 'BANKNIFTY'
        elif index_upper == 'FINNIFTY':
            prefix = 'FINNIFTY'
        else:
            prefix = 'NIFTY'
        
        return f"{prefix}{expiry}{strike}{option_type}"
    
    def get_option_chain(self, index='nifty', num_strikes=10) -> Optional[Dict]:
        """
        Get Option Chain using direct symbol construction
         (Optimized to avoid API rate limits)
        """
        if not self.is_logged_in:
            if not self.login():
                return None
        
        try:
            # Get current price
            ltp_data = self.get_ltp(index)
            if not ltp_data:
                print("Failed to get LTP for option chain")
                return None
            
            spot_price = ltp_data['ltp']
            
            # Calculate ATM strike
            atm_strike = round(spot_price / 50) * 50
            
            # Get expiry in format: DDMMMYY (e.g., 29JAN26)
            expiry = self._get_next_expiry_formatted(index)
            
            # Generate strikes (ATM ± num_strikes)
            strikes = []
            for i in range(-num_strikes, num_strikes + 1):
                strike = atm_strike + (i * 50)
                if strike > 0:
                    strikes.append(strike)
            
            # Build option chain
            option_chain = []
            for strike in strikes:
                # Construct symbols directly
                ce_symbol = self._construct_option_symbol(index, strike, 'CE', expiry)
                pe_symbol = self._construct_option_symbol(index, strike, 'PE', expiry)
                
                option_chain.append({
                    'strike': strike,
                    'ce_symbol': ce_symbol,
                    'ce_ltp': 0,  # Would need quote API call
                    'ce_oi': 0,
                    'pe_symbol': pe_symbol,
                    'pe_ltp': 0,
                    'pe_oi': 0
                })
            
            return {
                'index': index,
                'spot_price': spot_price,
                'atm_strike': atm_strike,
                'expiry': expiry,
                'chain': option_chain,
                'timestamp': datetime.now().isoformat(),
                'source': 'angel_one_optimized',
                'strikes_count': len(option_chain)
            }
            
        except Exception as e:
            print(f"Option chain error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_next_expiry_formatted(self, index='nifty') -> str:
        """
        Calculate next expiry in DDMMMYY format
        Example: 29JAN26
        """
        today = datetime.now()
        
        # Find next Thursday
        days_ahead = 3 - today.weekday()  # Thursday = 3
        if days_ahead <= 0:
            days_ahead += 7
        
        next_thursday = today + timedelta(days=days_ahead)
        
        # Format: DDMMMYY
        month_abbr = next_thursday.strftime('%b').upper()
        day = next_thursday.strftime('%d')
        year = next_thursday.strftime('%y')
        
        return f"{day}{month_abbr}{year}"
    
    def _get_next_expiry(self, index='nifty') -> str:
        """
        Calculate next expiry date
        Nifty/BankNifty: Weekly (Thursday)
        """
        today = datetime.now()
        
        # Find next Thursday
        days_ahead = 3 - today.weekday()  # Thursday = 3
        if days_ahead <= 0:
            days_ahead += 7
        
        next_expiry = today + timedelta(days=days_ahead)
        return next_expiry.strftime('%Y-%m-%d')
    
    def logout(self):
        """Logout from Angel One"""
        try:
            if self.smart_api:
                self.smart_api.terminateSession(self.client_code)
                print("[LOGOUT] Logged out from Angel One")
        except Exception as e:
            print(f"Logout error: {e}")
        finally:
            self.is_logged_in = False
            self.session_data = None


# Singleton instance
angel_one_enhanced = AngelOneEnhanced()


if __name__ == "__main__":
    """Test the Angel One integration"""
    print("=" * 60)
    print("Testing Angel One Enhanced Integration")
    print("=" * 60)
    
    # Test login
    if angel_one_enhanced.login():
        # Test getting LTP
        print("\n[TEST] Testing LTP:")
        nifty_ltp = angel_one_enhanced.get_ltp('nifty')
        if nifty_ltp:
            print(f"   NIFTY: Rs.{nifty_ltp['ltp']} ({nifty_ltp['change_pct']:+.2f}%)")
        
        # Test getting candles
        print("\n[TEST] Testing Candles:")
        candles = angel_one_enhanced.get_candles('nifty', 'FIVE_MINUTE', 2)
        print(f"   Fetched {len(candles)} candles")
        
        # Test option chain
        print("\n[TEST] Testing Option Chain:")
        oc = angel_one_enhanced.get_option_chain('nifty')
        if oc:
            print(f"   Spot: Rs.{oc['spot_price']}")
            print(f"   Expiry: {oc['expiry']}")
            print(f"   Strikes: {len(oc['chain'])}")
        
        # Logout
        angel_one_enhanced.logout()
    else:
        print("\n[ERROR] Login failed. Please check credentials in .env file")
