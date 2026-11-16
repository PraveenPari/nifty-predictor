import json
import time
from datetime import datetime
from nsepython import nse_get_index_quote

class NSEManager:
    """
    Manager for fetching real-time market data from NSE using nsepython.
    This replaces specialized managers for Yahoo/Angel for index data.
    """
    def __init__(self):
        self.indices = {
            'nifty': 'NIFTY 50',
            'banknifty': 'NIFTY BANK'
        }
        self.last_cache = {}
        self.cache_duration = 1  # 1 second cache to prevent hitting NSE too hard

    def get_live_price(self, index_key):
        """Fetch live LTP and change for a given index"""
        try:
            index_name = self.indices.get(index_key)
            if not index_name:
                return None

            # Cache check
            now = time.time()
            if index_key in self.last_cache:
                data, timestamp = self.last_cache[index_key]
                if now - timestamp < self.cache_duration:
                    return data

            # Fetch fresh data
            res = nse_get_index_quote(index_name)
            if not res or 'last' not in res:
                return None

            # Convert string numbers (e.g., '25,682.40') to float
            ltp = float(res['last'].replace(',', ''))
            perc_change = float(res.get('percChange', 0))
            
            # Open/High/Low
            open_val = float(res.get('open', '0').replace(',', ''))
            high_val = float(res.get('high', '0').replace(',', ''))
            low_val = float(res.get('low', '0').replace(',', ''))

            data = {
                'ltp': ltp,
                'change': round(ltp * (perc_change / 100), 2) if perc_change else 0,
                'percent_change': perc_change,
                'open': open_val,
                'high': high_val,
                'low': low_val,
                'timestamp': datetime.now().isoformat(),
                'source': 'NSE'
            }

            self.last_cache[index_key] = (data, now)
            return data
        except Exception as e:
            print(f"Error fetching NSE data for {index_key}: {e}")
            return None

nse_manager = NSEManager()
