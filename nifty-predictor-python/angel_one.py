"""
Angel One SmartAPI Integration (Python)
Uses real credentials to fetch live market data
"""

from SmartApi import SmartConnect
import pyotp
import time
import pandas as pd
from datetime import datetime, timedelta
from global_constants import INDEX_CONFIG

class AngelOneManager:
    """
    Manages connection to Angel One SmartAPI
    """
    def __init__(self, api_key, client_code, password, totp_secret):
        self.api_key = api_key
        self.client_code = client_code
        self.password = str(password)
        self.totp_secret = totp_secret
        
        self.smart_api = SmartConnect(api_key=self.api_key)
        self.session_data = None
        self.is_logged_in = False
        
        # Symbol Tokens and Mappings
        self.tokens = {
            'nifty': '99926000',
            'banknifty': '99926009'
        }
        self.symbol_map = {
            'nifty': 'Nifty 50',
            'banknifty': 'Nifty Bank'
        }

    def login(self):
        """Login to Angel One and generate session"""
        try:
            print(f"Logging in to Angel One for client: {self.client_code}...")
            totp = pyotp.TOTP(self.totp_secret).now()
            
            data = self.smart_api.generateSession(self.client_code, self.password, totp)
            
            if data['status'] == True:
                self.session_data = data['data']
                self.is_logged_in = True
                print("[SUCCESS] Angel One Login Successful")
                return True
            else:
                print(f"[FAILED] Angel One Login Failed: {data['message']}")
                return False
        except Exception as e:
            print(f"[ERROR] Angel One Login Exception: {e}")
            return False

    def get_ltp(self, index='nifty'):
        """Fetch real-time LTP for Nifty or Bank Nifty"""
        if not self.is_logged_in:
            if not self.login(): return None
            
        try:
            token = self.tokens.get(index)
            symbol = self.symbol_map.get(index)
            if not token or not symbol: return None
            
            data = self.smart_api.ltpData("NSE", symbol, token)
            if data['status'] == True:
                return {
                    'ltp': float(data['data']['ltp']),
                    'change': float(data['data']['netPrice']) if 'netPrice' in data['data'] else 0,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            print(f"Angel One LTP Error: {e}")
            self.is_logged_in = False # Force relogin on next attempt
            
        return None

    def get_candles(self, index='nifty', interval="FIVE_MINUTE"):
        """Fetch historical candle data"""
        if not self.is_logged_in:
            if not self.login(): return []
            
        try:
            token = self.tokens.get(index)
            if not token: return []
            
            # API expects time in 2024/2025 formats
            to_date = datetime.now()
            from_date = to_date - timedelta(days=5)
            
            params = {
                "exchange": "NSE",
                "symboltoken": token,
                "interval": interval,
                "fromdate": from_date.strftime('%Y-%m-%d %H:%M'),
                "todate": to_date.strftime('%Y-%m-%d %H:%M')
            }
            
            data = self.smart_api.getCandleData(params)
            
            if data['status'] == True:
                candles = []
                for c in data['data']:
                    candles.append({
                        'timestamp': int(datetime.strptime(c[0], '%Y-%m-%dT%H:%M:%S%z').timestamp()),
                        'open': float(c[1]),
                        'high': float(c[2]),
                        'low': float(c[3]),
                        'close': float(c[4]),
                        'volume': int(c[5])
                    })
                return candles
        except Exception as e:
            print(f"Angel One Candle Error: {e}")
            
        return []

# Shared instance with YOUR credentials
angel_manager = AngelOneManager(
    api_key='ujRLiue0',
    client_code='P812102',
    password='2271',
    totp_secret='542WYM7GZSMT73TU625FXJAV2M'
)
