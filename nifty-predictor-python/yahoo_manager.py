import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

class YahooFinanceManager:
    def __init__(self):
        self.tickers = {
            'nifty': '^NSEI',
            'banknifty': '^NSEBANK',
            'vix': '^INDIAVIX'
        }

    def get_live_price(self, index='nifty'):
        try:
            # print(f"DEBUG: Fetching live price for {index}...")
            symbol = self.tickers.get(index)
            if not symbol:
                return None
            
            # Fetch latest data (1 day)
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1d")
            
            if df.empty:
                print(f"DEBUG: Empty data for {index}")
                return None
                
            price = df['Close'].iloc[-1]
            prev_close = df['Close'].iloc[0] if len(df) > 1 else df['Open'].iloc[0] # Approx prev close or open
            
            # Better prev close estimation
            try:
                info = ticker.info
                if 'previousClose' in info:
                    prev_close = info['previousClose']
            except:
                pass

            # print(f"DEBUG: {index} Price: {price}, Prev: {prev_close}")
            
            # Calculate change
            change = 0.0
            if prev_close:
                change = ((price - prev_close) / prev_close) * 100

            return {
                'ltp': round(float(price), 2),
                'change': round(float(change), 2),
                'timestamp': datetime.now().isoformat(),
                'source': 'Yahoo Finance'
            }
        except Exception as e:
            print(f"Yahoo Finance Live Price Error: {e}")
            return None

    def get_candles(self, index='nifty', interval='5m', period='5d'):
        try:
            symbol = self.tickers.get(index)
            if not symbol:
                return []
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                return []

            candles = []
            for time, row in df.iterrows():
                # Yahoo finance timestamp is naive or has tz, we need to ensure it's comparable
                ts = int(time.timestamp())
                candles.append({
                    'timestamp': ts,
                    'datetime': time.isoformat(),
                    'open': row['Open'],
                    'high': row['High'],
                    'low': row['Low'],
                    'close': row['Close'],
                    'volume': int(row['Volume'])
                })
            
            return candles

        except Exception as e:
            print(f"Yahoo Finance Candle Error: {e}")
            return []

    def get_option_chain(self, index='nifty'):
        """
        Fetch Option Chain from Yahoo Finance as fallback
        Optimized for reliability and speed
        """
        try:
            # print(f"DEBUG: Yahoo Fallback - Fetching Option Chain for {index}...")
            symbol = self.tickers.get(index)
            if not symbol: return None
            
            tk = yf.Ticker(symbol)
            
            # Get Expiries
            try:
                expiries = tk.options
            except:
                print(f"DEBUG: Yahoo - Failed to get expiries for {index}")
                return None
                
            if not expiries:
                print("DEBUG: Yahoo - No option expiries found")
                return None
                
            # Pick nearest expiry
            nearest_expiry = expiries[0]
            # print(f"DEBUG: Yahoo - Using Expiry: {nearest_expiry}")
            
            # Fetch chain
            try:
                chain = tk.option_chain(nearest_expiry)
                calls = chain.calls
                puts = chain.puts
            except Exception as e:
                print(f"DEBUG: Yahoo - Failed to fetch chain: {e}")
                return None
            
            # Get Underlying Price
            spot_data = self.get_live_price(index)
            spot = spot_data['ltp'] if spot_data else 0
            
            if spot == 0:
                 # Try to use the last price from the chain as approximation if spot fetch failed
                 # Or just return None because picking implies direction from spot
                 return None

            # Create a unified dictionary: {strike: {ce_oi, pe_oi, ...}}
            chain_dict = {}
            
            # Helper to safely get float
            def safe_float(val):
                try: return float(val) if pd.notna(val) else 0.0
                except: return 0.0
                
            def safe_int(val):
                try: return int(val) if pd.notna(val) else 0
                except: return 0

            # Process Calls
            for _, row in calls.iterrows():
                strike = safe_float(row['strike'])
                if strike > 0:
                    if strike not in chain_dict: chain_dict[strike] = {}
                    chain_dict[strike]['ce_oi'] = safe_int(row['openInterest'])
                    chain_dict[strike]['ce_ltp'] = safe_float(row['lastPrice'])
                    chain_dict[strike]['ce_vol'] = safe_int(row['volume'])

            # Process Puts
            for _, row in puts.iterrows():
                strike = safe_float(row['strike'])
                if strike > 0:
                    if strike not in chain_dict: chain_dict[strike] = {}
                    chain_dict[strike]['pe_oi'] = safe_int(row['openInterest'])
                    chain_dict[strike]['pe_ltp'] = safe_float(row['lastPrice'])
                    chain_dict[strike]['pe_vol'] = safe_int(row['volume'])
            
            # Filter near ATM (narrow range for speed)
            all_strikes = sorted(chain_dict.keys())
            if not all_strikes: return None
            
            atm_strike = min(all_strikes, key=lambda x: abs(x - spot))
            atm_idx = all_strikes.index(atm_strike)
            
            # 8 strikes up/down
            start_idx = max(0, atm_idx - 8)
            end_idx = min(len(all_strikes), atm_idx + 9)
            
            final_chain = []
            for k in all_strikes[start_idx:end_idx]:
                data = chain_dict[k]
                final_chain.append({
                    'strike': k,
                    'ce_oi': data.get('ce_oi', 0),
                    'pe_oi': data.get('pe_oi', 0),
                    'ce_ltp': data.get('ce_ltp', 0),
                    'pe_ltp': data.get('pe_ltp', 0),
                    'ce_vol': data.get('ce_vol', 0),
                    'pe_vol': data.get('pe_vol', 0),
                    'is_atm': (k == atm_strike)
                })

            return {
                'underlying': spot,
                'expiry': nearest_expiry, 
                'chain': final_chain,
                'source': 'Yahoo'
            }
            
        except Exception as e:
            print(f"Yahoo Option Chain Error: {e}")
            return None

    def get_vix(self):
        """Fetch India VIX"""
        try:
            return self.get_live_price('vix')
        except:
             return None

    def get_fii_dii(self):
        """
        Fetch FII/DII data by scraping MoneyControl
        Returns dict with fii_net and dii_net values in crores
        Cached for 30 minutes to avoid slow page loads
        """
        # Check cache first
        if hasattr(self, '_fii_dii_cache'):
            cache_time = self._fii_dii_cache.get('timestamp')
            if cache_time and (datetime.now() - cache_time) < timedelta(minutes=30):
                return self._fii_dii_cache['data']
        
        import requests
        from bs4 import BeautifulSoup
        
        try:
            print("DEBUG: Fetching FII/DII data from MoneyControl...")
            
            # MoneyControl FII/DII page
            url = "https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/index.php"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
            
            response = requests.get(url, headers=headers, timeout=5) # Reduced timeout
            
            if response.status_code != 200:
                print(f"DEBUG: MoneyControl returned status {response.status_code}")
                # Return cached data if available even if expired, else 0
                if hasattr(self, '_fii_dii_cache'):
                     return self._fii_dii_cache['data']
                return {'fii_net': 0, 'dii_net': 0, 'source': 'unavailable'}
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the FII/DII table
            fii_net = 0
            dii_net = 0
            
            # Look for table with FII/DII data
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        text = cells[0].get_text(strip=True).upper()
                        if 'FII' in text or 'FOREIGN' in text:
                            try:
                                # Net value is usually in a later column
                                for cell in cells[1:]:
                                    val_text = cell.get_text(strip=True).replace(',', '').replace('(', '-').replace(')', '')
                                    if val_text and val_text not in ['-', '']:
                                        try:
                                            fii_net = float(val_text)
                                            break
                                        except:
                                            continue
                            except:
                                pass
                        elif 'DII' in text or 'DOMESTIC' in text:
                            try:
                                for cell in cells[1:]:
                                    val_text = cell.get_text(strip=True).replace(',', '').replace('(', '-').replace(')', '')
                                    if val_text and val_text not in ['-', '']:
                                        try:
                                            dii_net = float(val_text)
                                            break
                                        except:
                                            continue
                            except:
                                pass
            
            # If still 0, try alternate approach - look for specific class/id
            if fii_net == 0 and dii_net == 0:
                # Try finding by common patterns
                all_text = soup.get_text()
                import re
                
                # Pattern for FII net
                fii_match = re.search(r'FII[^\d]*Net[^\d]*([+-]?\d+[\d,]*\.?\d*)', all_text, re.IGNORECASE)
                if fii_match:
                    try:
                        fii_net = float(fii_match.group(1).replace(',', ''))
                    except:
                        pass
                
                # Pattern for DII net
                dii_match = re.search(r'DII[^\d]*Net[^\d]*([+-]?\d+[\d,]*\.?\d*)', all_text, re.IGNORECASE)
                if dii_match:
                    try:
                        dii_net = float(dii_match.group(1).replace(',', ''))
                    except:
                        pass
            
            print(f"DEBUG: FII Net: {fii_net}, DII Net: {dii_net}")
            
            data = {
                'fii_net': round(fii_net, 2),
                'dii_net': round(dii_net, 2),
                'source': 'MoneyControl',
                'timestamp': datetime.now().isoformat()
            }
            
            # Update cache
            self._fii_dii_cache = {
                'timestamp': datetime.now(),
                'data': data
            }
            
            return data
            
        except Exception as e:
            print(f"FII/DII Fetch Error: {e}")
            # Return cached data if available even if expired
            if hasattr(self, '_fii_dii_cache'):
                 return self._fii_dii_cache['data']
            return {'fii_net': 0, 'dii_net': 0, 'source': 'error'}

# Singleton instance
yahoo_manager = YahooFinanceManager()
