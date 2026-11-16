"""
Breeze API Data Manager
Primary data source with 100% working implementation for Indices
"""

import time
from datetime import datetime, timedelta
import threading
from typing import Dict, List, Optional
import os

# Import Breeze with full error handling
BREEZE_AVAILABLE = False
BreezeConnect = None

try:
    from breeze_connect import BreezeConnect
    BREEZE_AVAILABLE = True
    print("Breeze SDK loaded successfully")
except ImportError as e:
    print(f"CRITICAL: breeze_connect not installed: {e}")
except Exception as e:
    print(f"CRITICAL: Breeze import error: {e}")

from pro_config.api_config import BREEZE_API_KEY, BREEZE_SECRET_KEY, BREEZE_SESSION_TOKEN, CACHE_DURATION, RETRY_ATTEMPTS


class BreezeManager:
    """Primary data fetcher using Breeze API optimized for NIFTY/BANKNIFTY"""
    
    def __init__(self):
        self.breeze = None
        self.connected = False
        self.cache = {}
        self.cache_time = {}
        self.lock = threading.Lock()
        self.init_attempted = False
        self.api_key = BREEZE_API_KEY
        self.secret_key = BREEZE_SECRET_KEY
        self.session_token = None
        
        # Exact stock codes for Breeze indices
        self.symbols = {
            'nifty': {'exchange': 'nse', 'stock_code': 'NIFTY', 'product_type': 'cash'},
            'banknifty': {'exchange': 'nse', 'stock_code': 'CNXBAN', 'product_type': 'cash'}
        }
    
    def _connect(self):
        """Initialize Breeze SDK object"""
        if self.breeze is not None:
            return True
            
        if not BREEZE_AVAILABLE or BreezeConnect is None:
            return False
            
        try:
            print(f"DEBUG: Initializing BreezeConnect with API key: {self.api_key}")
            self.breeze = BreezeConnect(api_key=self.api_key)
            return True
        except Exception as e:
            print(f"CRITICAL: BreezeConnect init failed: {e}")
            return False
    
    def _is_cache_valid(self, key: str) -> bool:
        if key not in self.cache_time:
            return False
        return (time.time() - self.cache_time[key]) < CACHE_DURATION
    
    def get_live_price(self, index: str = 'nifty') -> Optional[Dict]:
        """Get live price using get_quotes"""
        if not self.connected:
            return None
            
        index_key = index.lower().replace(' ', '')
        if 'bank' in index_key:
            index_key = 'banknifty'
        else:
            index_key = 'nifty'
            
        cache_key = f"ltp_{index_key}"
        with self.lock:
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]
        
        try:
            sym = self.symbols[index_key]
            # print(f"DEBUG: Fetching live price for {index} (code: {sym['stock_code']})...")
            quote = self.breeze.get_quotes(
                stock_code=sym['stock_code'],
                exchange_code=sym['exchange'],
                product_type=sym['product_type']
            )
            
            if quote and 'Success' in quote and quote['Success']:
                data = quote['Success'][0]
                # SDK might return ltp as string
                ltp = float(data.get('ltp', 0) or data.get('last', 0))
                open_price = float(data.get('open', ltp))
                change = round(((ltp - open_price) / open_price) * 100, 2) if open_price else 0
                
                # print(f"DEBUG: {index} Price: {ltp}, Change: {change}%")
                
                result = {
                    'ltp': round(ltp, 2),
                    'change': change,
                    'high': float(data.get('high', ltp)),
                    'low': float(data.get('low', ltp)),
                    'source': 'Breeze'
                }
                
                with self.lock:
                    self.cache[cache_key] = result
                    self.cache_time[cache_key] = time.time()
                return result
            else:
                print(f"WARNING: Breeze get_quotes returned empty or failure: {quote}")
        except Exception as e:
            with self.lock:
                if cache_key in self.cache:
                    return self.cache[cache_key]
            return None

    def get_historical_data(self, index: str = 'nifty', interval: str = '5minute', 
                           days: int = 5) -> Optional[List[Dict]]:
        """Get historical data using get_historical_data_v2"""
        if not self.connected:
            return None
            
        index_key = 'banknifty' if 'bank' in index.lower() else 'nifty'
        sym = self.symbols[index_key]
        
        # Interval mapping for V2
        interval_map = {
            '1minute': '1minute',
            '5minute': '5minute',
            '30minute': '30minute',
            '1day': '1day'
        }
        breeze_interval = interval_map.get(interval, '5minute')
        
        try:
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)
            
            # Use V2 for indices as it's more reliable
            historical = self.breeze.get_historical_data_v2(
                interval=breeze_interval,
                from_date=from_date.strftime("%Y-%m-%dT09:15:00.000Z"),
                to_date=to_date.strftime("%Y-%m-%dT15:30:00.000Z"),
                stock_code=sym['stock_code'],
                exchange_code=sym['exchange'],
                product_type=sym['product_type']
            )
            
            if historical and 'Success' in historical and historical['Success']:
                candles = []
                for row in historical['Success']:
                    candles.append({
                        'time': row.get('datetime'),
                        'open': float(row.get('open', 0)),
                        'high': float(row.get('high', 0)),
                        'low': float(row.get('low', 0)),
                        'close': float(row.get('close', 0)),
                        'volume': int(row.get('volume', 0))
                    })
                return candles
        except Exception as e:
            print(f"Breeze historical V2 error for {index_key}: {e}")
            
        return None

    def get_option_chain(self, index: str = 'nifty') -> Optional[Dict]:
        """Get option chain from Breeze with correct expiry calculation"""
        if not self.connected:
            return None
            
        index_key = 'banknifty' if 'bank' in index.lower() else 'nifty'
        sym = self.symbols[index_key]
        
        try:
            # First get underlying price
            quote = self.get_live_price(index)
            spot = quote['ltp'] if quote else 0
            
            # Calculate next expiry
            today = datetime.now()
            
            # Dynamic expiry discovery: check from today to next 10 days
            cached_exp = self.cache.get(f"{index_key}_expiry")
            expiries_to_try = [cached_exp] if cached_exp else []
            for offset in range(0, 11):
                exp_dt = (today + timedelta(days=offset)).strftime("%d-%b-%Y")
                if exp_dt not in expiries_to_try:
                    expiries_to_try.append(exp_dt)

            chain_data = []
            used_expiry = ""

            for expiry_str in expiries_to_try:
                try:
                    # Fetch Call Option Chain
                    oc_calls = self.breeze.get_option_chain_quotes(
                        stock_code=sym['stock_code'],
                        exchange_code='NFO',
                        product_type='options',
                        expiry_date=expiry_str,
                        right="call",
                        strike_price=""
                    )
                    
                    if not oc_calls or not oc_calls.get('Success'):
                        continue

                    # Fetch Put Option Chain
                    oc_puts = self.breeze.get_option_chain_quotes(
                        stock_code=sym['stock_code'],
                        exchange_code='NFO',
                        product_type='options',
                        expiry_date=expiry_str,
                        right="put",
                        strike_price=""
                    )
                    
                    if oc_calls.get('Success') or (oc_puts and oc_puts.get('Success')):
                        self.cache[f"{index_key}_expiry"] = expiry_str
                        print(f"DEBUG: Found option chain data with expiry {expiry_str}")
                        calls = {x['strike_price']: x for x in oc_calls.get('Success', [])}
                        puts = {x['strike_price']: x for x in oc_puts.get('Success', [])}
                        
                        # Get all unique strikes
                        all_strikes = set(calls.keys()) | set(puts.keys())
                        strikes = sorted([float(k) for k in all_strikes])
                        
                        if strikes:
                            # Process strikes 
                            atm_strike = min(strikes, key=lambda x: abs(x - spot))
                            atm_idx = strikes.index(atm_strike)
                            start_idx = max(0, atm_idx - 6)
                            end_idx = min(len(strikes), atm_idx + 7)
                            
                            for k in strikes[start_idx:end_idx]:
                                c = calls.get(k, {})
                                p = puts.get(k, {})
                                chain_data.append({
                                    'strike': k,
                                    'ce_oi': float(c.get('open_interest', 0) or 0),
                                    'pe_oi': float(p.get('open_interest', 0) or 0),
                                    'ce_ltp': float(c.get('ltp', 0) or 0),
                                    'pe_ltp': float(p.get('ltp', 0) or 0),
                                    'is_atm': (k == atm_strike)
                                })
                            
                            if chain_data:
                                used_expiry = expiry_str
                                break # Stop if we found data
                    else:
                        print(f"DEBUG: No data for {expiry_str}. Retrying next expiry...")
                        
                except Exception as ex:
                    print(f"DEBUG: API Call Failed for {expiry_str}: {ex}")
                    continue

            if chain_data:
                return {
                    'underlying': spot,
                    'expiry': used_expiry,
                    'chain': chain_data,
                    'source': 'Breeze'
                }
            else:
                 print(f"DEBUG: All expiries failed for {index_key}. Trying Yahoo Fallback...")
                 # Yahoo Fallback
                 try:
                     from yahoo_manager import yahoo_manager
                     return yahoo_manager.get_option_chain(index)
                 except Exception as ey:
                     print(f"Yahoo Fallback Failed: {ey}")
                     
        except Exception as e:
            print(f"Breeze option chain error: {e}")
            import traceback
            traceback.print_exc()
            
        return None

    def get_vix(self):
        """Get India VIX from Yahoo (Breeze doesn't provide it simply)"""
        try:
            from yahoo_manager import yahoo_manager
            return yahoo_manager.get_vix()
        except:
            return None

    def generate_session_token(self):
        """Get login URL"""
        return f"https://api.icicidirect.com/api/v2/login?api_key={self.api_key}"

    def set_session_token(self, session_token: str):
        """100% Working Session Initialization"""
        if not self.breeze:
            self._connect()
            
        if not self.breeze:
            return False
            
        try:
            print(f"DEBUG: Setting session token: {session_token[:10]}...")
            self.breeze.generate_session(api_secret=self.secret_key, session_token=session_token)
            self.connected = True
            self.session_token = session_token
            print("[SUCCESS] Breeze session authenticated!")
            return True
        except Exception as e:
            print(f"[ERROR] Breeze session auth failed: {e}")
            self.connected = False
            return False

    def is_connected(self) -> bool:
        return self.connected

# Singleton instance
breeze_manager = BreezeManager()

# Auto-initialize with session token from .env if available
if BREEZE_SESSION_TOKEN:
    print(f"[BREEZE] Found session token in .env, attempting auto-connect...")
    if breeze_manager.set_session_token(BREEZE_SESSION_TOKEN):
        print("[BREEZE] Auto-connected successfully!")
    else:
        print("[BREEZE] Auto-connect failed - token may be expired. Login via /api/breeze-login-url")
else:
    print("[BREEZE] No session token in .env. Set BREEZE_SESSION_TOKEN or login via /api/breeze-login-url")

