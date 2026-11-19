"""
Breeze API Data Manager
Breeze REST market data for indices
"""

import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import threading
from typing import Dict, List, Optional

from breeze_rest import BreezeRest, BreezeError, BreezeAPIError, BreezeSessionError
from pro_config.api_config import BREEZE_API_KEY, BREEZE_SECRET_KEY, BREEZE_SESSION_TOKEN, CACHE_DURATION
from secrets_manager import mask, breeze_login_url


class BreezeManager:
    """Primary data fetcher using Breeze API optimized for NIFTY/BANKNIFTY"""
    
    def __init__(self):
        self.breeze = None
        self.connected = False
        self.cache = {}
        self.cache_time = {}
        self.lock = threading.Lock()
        self.auth_lock = threading.Lock()
        self.init_attempted = False
        self.api_key = BREEZE_API_KEY or ""
        self.secret_key = BREEZE_SECRET_KEY or ""
        self.session_token = None
        self.last_error = ''  # safe reason surfaced to UI when auth fails
        self.last_error_code = ''
        self.last_probe = None  # last verified quote (proof of live feed)
        
        # Exact stock codes for Breeze indices
        self.symbols = {
            'nifty': {'exchange': 'nse', 'stock_code': 'NIFTY', 'product_type': 'cash'},
            'banknifty': {'exchange': 'nse', 'stock_code': 'CNXBAN', 'product_type': 'cash'}
        }
    
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
            client = self.breeze
            quote = client.get_quotes(
                stock_code=sym['stock_code'], exchange_code=sym['exchange'],
                product_type=sym['product_type'])

            if quote and 'Success' in quote and quote['Success']:
                data = quote['Success'][0]
                # SDK might return ltp as string
                ltp = float(data.get('ltp', 0) or data.get('last', 0))
                if ltp <= 0:
                    return None
                previous_close = float(data.get('previous_close') or 0)
                pct = data.get('ltp_percent_change')
                change = float(pct) if pct is not None and pct != '' else (round((ltp - previous_close) / previous_close * 100, 2) if previous_close else 0)
                
                # print(f"DEBUG: {index} Price: {ltp}, Change: {change}%")
                
                result = {
                    'ltp': round(ltp, 2),
                    'change': change,
                    'high': float(data.get('high') or ltp),
                    'low': float(data.get('low') or ltp),
                    'source': 'Breeze',
                    'last_trade_time': data.get('ltt')
                }
                
                with self.lock:
                    if self.breeze is client:
                        self.cache[cache_key] = result
                        self.cache_time[cache_key] = time.time()
                return result
            else:
                print("[BREEZE] Quote response contained no data.")
        except BreezeSessionError:
            with self.lock:
                if self.breeze is client:
                    self.connected = False
                    self.session_token = None
                    self.last_error_code = 'BREEZE_AUTH_REJECTED'
                    self.last_error = 'Breeze session expired or invalid; update server secrets and restart.'
                    self.last_probe = None
                    self.cache.clear()
                    self.cache_time.clear()
            print("[BREEZE] Session invalid or expired; update the session secret and restart.")
            return None
        except (BreezeError, ValueError, TypeError, KeyError, IndexError) as e:
            print(f"[BREEZE] Quote unavailable ({type(e).__name__}); using fallback.")
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
            to_date = datetime.now(ZoneInfo("Asia/Kolkata"))
            from_date = to_date - timedelta(days=days)
            start = from_date.replace(hour=9, minute=15, second=0, microsecond=0).astimezone(timezone.utc)
            end = to_date.replace(hour=15, minute=30, second=0, microsecond=0).astimezone(timezone.utc)
            
            historical = self.breeze.get_historical_data_v2(
                interval=breeze_interval,
                from_date=start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                to_date=end.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                stock_code=sym['stock_code'], exchange_code=sym['exchange'],
                product_type=sym['product_type'])

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
            today = datetime.now(ZoneInfo("Asia/Kolkata"))
            
            # Probe nearby dates using the ISO-8601 format documented by Breeze.
            cached_exp = self.cache.get(f"{index_key}_expiry")
            expiries_to_try = [cached_exp] if cached_exp else []
            for offset in range(0, 11):
                day = today + timedelta(days=offset)
                exp_dt = day.strftime("%Y-%m-%dT06:00:00.000Z")
                if exp_dt not in expiries_to_try:
                    expiries_to_try.append(exp_dt)

            chain_data = []
            used_expiry = ""

            # Limit repeated expiry probes; a single socket call still has its
            # own timeout and can run beyond this soft budget.
            deadline = time.monotonic() + 15
            for expiry_str in expiries_to_try:
                if time.monotonic() >= deadline:
                    print("[BREEZE] Option-chain discovery budget exhausted.")
                    break
                try:
                    oc_calls = self.breeze.get_option_chain_quotes(
                        stock_code=sym['stock_code'], exchange_code='NFO',
                        product_type='options', expiry_date=expiry_str,
                        right='call', strike_price='')
                    if not oc_calls or not oc_calls.get('Success'):
                        continue
                    if time.monotonic() >= deadline:
                        break
                    oc_puts = self.breeze.get_option_chain_quotes(
                        stock_code=sym['stock_code'], exchange_code='NFO',
                        product_type='options', expiry_date=expiry_str,
                        right='put', strike_price='')

                    if oc_calls.get('Success') or (oc_puts and oc_puts.get('Success')):
                        self.cache[f"{index_key}_expiry"] = expiry_str
                        print(f"DEBUG: Found option chain data with expiry {expiry_str}")
                        calls = {float(x['strike_price']): x for x in oc_calls.get('Success', [])}
                        puts = {float(x['strike_price']): x for x in (oc_puts.get('Success') or [])}
                        
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
                        
                except BreezeAPIError:
                    # A date without an expiry can be rejected by the API.
                    continue
                except BreezeError:
                    print("[BREEZE] Option-chain request failed; using fallback.")
                    break
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
                print(f"[BREEZE] No option chain for {index_key}; hybrid fallback may be used.")

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
        """Get login URL (uses key from secrets only)."""
        return breeze_login_url()

    @staticmethod
    def _extract_apisession(raw: str) -> str:
        """Accept a bare apisession token OR a full ICICI redirect URL."""
        t = (raw or '').strip().strip('"').strip("'").strip()
        if 'apisession=' in t.lower():
            import re
            from urllib.parse import parse_qs
            q = t.split('?', 1)[1] if '?' in t else t
            q = q.split('#', 1)[0]
            try:
                params = parse_qs(q, keep_blank_values=True)
                for k, v in params.items():
                    if k.lower() == 'apisession' and v and v[0].strip():
                        return v[0].strip()
            except Exception:
                pass
            m = re.search(r'apisession=([^&\s#]+)', t, re.IGNORECASE)
            if m:
                return m.group(1).strip()
            return ''
        return t.split()[0] if t.split() else ''

    def set_session_token(self, session_token: str):
        """Authenticate with the documented customer-details API; probe a fresh quote.

        Credentials and the resulting session remain in process memory only.
        At startup, the token is read from the server secret environment.
        """
        with self.auth_lock:
            self.last_error = ''
            self.last_error_code = ''
            self.last_probe = None
            clean = self._extract_apisession(session_token)
            if not clean:
                self.last_error_code = 'BREEZE_TOKEN_MISSING'
                self.last_error = 'Empty token — paste the apisession token or redirect URL'
                return False
            if not self.api_key or not self.secret_key:
                self.last_error_code = 'BREEZE_NOT_CONFIGURED'
                self.last_error = 'API key/secret missing in server secrets'
                return False
            client = BreezeRest(self.api_key, self.secret_key)
            try:
                client.authenticate(clean)
            except BreezeError as exc:
                self.last_error_code = 'BREEZE_AUTH_REJECTED' if isinstance(exc, BreezeAPIError) else 'BREEZE_UNAVAILABLE'
                self.last_error = str(exc)
                print(f"[BREEZE] Authentication failed: {exc}")
                return False
            with self.lock:
                self.cache.clear()
                self.cache_time.clear()
                self.breeze = client
                self.connected = True
                self.session_token = clean
            probe = self.get_live_price('nifty')
            if not self.connected:
                self.last_error_code = 'BREEZE_AUTH_REJECTED'
                self.last_error = 'Breeze session expired or invalid; reconnect'
                return False
            if probe and probe.get('ltp'):
                self.last_probe = {k: probe.get(k) for k in ('ltp', 'change', 'source', 'last_trade_time')}
                print("[BREEZE] Session authenticated; quote probe returned data.")
            else:
                self.last_error = 'Login accepted, but the NIFTY quote probe returned no data.'
                print("[BREEZE] Login accepted, but NIFTY quote probe failed.")
            return True

    def status(self):
        """Safe status for APIs/logs — never includes secret values."""
        return {
            'configured': bool(self.api_key and self.secret_key),
            'api_key': mask(self.api_key),
            'connected': self.connected,
            'session_token_set': bool(self.session_token or BREEZE_SESSION_TOKEN),
            'login_url_ready': bool(self.api_key),
        }

    def is_connected(self) -> bool:
        return self.connected

# Singleton instance
breeze_manager = BreezeManager()

# Auto-connect from the hosting environment (or a local ignored .env file).
# Never print token contents; a missing or rejected token leaves fallbacks active.
if BREEZE_SESSION_TOKEN:
    print("[BREEZE] Session secret present; attempting auto-connect.")
    try:
        if breeze_manager.set_session_token(BREEZE_SESSION_TOKEN):
            if breeze_manager.last_probe:
                print("[BREEZE] Auto-connect authenticated; startup quote received.")
            else:
                print("[BREEZE] Auto-connect authenticated; startup quote unavailable.")
        else:
            print(f"[BREEZE] Auto-connect failed ({breeze_manager.last_error_code}). Check Render secrets and the ICICI session.")
    except Exception as exc:
        breeze_manager.connected = False
        breeze_manager.last_error_code = 'BREEZE_UNAVAILABLE'
        breeze_manager.last_error = 'Breeze auto-connect failed unexpectedly.'
        print(f"[BREEZE] Auto-connect failed unexpectedly ({type(exc).__name__}).")
else:
    breeze_manager.last_error_code = 'BREEZE_TOKEN_MISSING'
    breeze_manager.last_error = 'Set BREEZE_SESSION_TOKEN in server secrets and restart.'
    print("[BREEZE] Session token missing. Set BREEZE_SESSION_TOKEN in server secrets and restart.")
