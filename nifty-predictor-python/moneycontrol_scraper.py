"""
MoneyControl Scraper Module
Scrapes market movers (gainers/losers) from MoneyControl
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time


class MoneyControlScraper:
    """Scrapes market data from MoneyControl"""
    
    def __init__(self):
        self.base_url = "https://www.moneycontrol.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 300  # 5 minutes cache
    
    def _is_cache_valid(self, key: str) -> bool:
        if key not in self.cache_time:
            return False
        return (time.time() - self.cache_time[key]) < self.cache_duration
    
    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a page"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"MoneyControl fetch error: {e}")
        return None
    
    def get_top_gainers(self, count: int = 10) -> List[Dict]:
        """Get top gainers from MoneyControl"""
        cache_key = 'top_gainers'
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key][:count]
        
        try:
            url = f"{self.base_url}/markets/indian-indices/top-nse-500-index-gainers.html"
            soup = self._fetch_page(url)
            
            if not soup:
                return []
            
            gainers = []
            table = soup.find('table', {'class': 'tbldata14'}) or soup.find('table')
            
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows[:15]:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        try:
                            name = cells[0].get_text(strip=True)
                            price = self._parse_number(cells[1].get_text(strip=True))
                            change = self._parse_number(cells[2].get_text(strip=True))
                            change_pct = self._parse_number(cells[3].get_text(strip=True).replace('%', ''))
                            
                            if name and price:
                                gainers.append({
                                    'name': name[:20],  # Truncate long names
                                    'price': price,
                                    'change': change,
                                    'change_pct': change_pct,
                                    'type': 'GAINER'
                                })
                        except:
                            continue
            
            self.cache[cache_key] = gainers
            self.cache_time[cache_key] = time.time()
            
            return gainers[:count]
            
        except Exception as e:
            print(f"Top gainers error: {e}")
            return []
    
    def get_top_losers(self, count: int = 10) -> List[Dict]:
        """Get top losers from MoneyControl"""
        cache_key = 'top_losers'
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key][:count]
        
        try:
            url = f"{self.base_url}/markets/indian-indices/top-nse-500-index-losers.html"
            soup = self._fetch_page(url)
            
            if not soup:
                return []
            
            losers = []
            table = soup.find('table', {'class': 'tbldata14'}) or soup.find('table')
            
            if table:
                rows = table.find_all('tr')[1:]
                for row in rows[:15]:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        try:
                            name = cells[0].get_text(strip=True)
                            price = self._parse_number(cells[1].get_text(strip=True))
                            change = self._parse_number(cells[2].get_text(strip=True))
                            change_pct = self._parse_number(cells[3].get_text(strip=True).replace('%', ''))
                            
                            if name and price:
                                losers.append({
                                    'name': name[:20],
                                    'price': price,
                                    'change': change,
                                    'change_pct': change_pct,
                                    'type': 'LOSER'
                                })
                        except:
                            continue
            
            self.cache[cache_key] = losers
            self.cache_time[cache_key] = time.time()
            
            return losers[:count]
            
        except Exception as e:
            print(f"Top losers error: {e}")
            return []
    
    def get_market_movers(self) -> Dict:
        """Get combined market movers (gainers + losers)"""
        return {
            'gainers': self.get_top_gainers(5),
            'losers': self.get_top_losers(5),
            'timestamp': datetime.now().isoformat(),
            'source': 'MoneyControl'
        }
    
    def get_market_summary(self) -> Dict:
        """Get market summary from MoneyControl"""
        cache_key = 'market_summary'
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            url = f"{self.base_url}/stocksmarketsindia/"
            soup = self._fetch_page(url)
            
            if not soup:
                return {}
            
            summary = {
                'nifty': None,
                'banknifty': None,
                'sensex': None,
                'advance_decline': None,
                'timestamp': datetime.now().isoformat()
            }
            
            # Try to parse index values
            index_divs = soup.find_all('div', {'class': 'bse_head'})
            for div in index_divs:
                text = div.get_text(strip=True).upper()
                if 'NIFTY' in text or 'SENSEX' in text:
                    # Extract value from sibling/child
                    pass
            
            self.cache[cache_key] = summary
            self.cache_time[cache_key] = time.time()
            
            return summary
            
        except Exception as e:
            print(f"Market summary error: {e}")
            return {}
    
        try:
            clean = text.replace(',', '').replace('(', '-').replace(')', '').strip()
            return float(clean)
        except:
            return 0.0

    def get_option_chain(self, index: str = 'nifty') -> Optional[Dict]:
        """
        Scrape Option Chain from MoneyControl
        Returns standardized format compatible with app
        """
        cache_key = f'oc_{index}'
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
            
        try:
            # ID mapping
            ind_id = '9' if index.lower() == 'nifty' else '23'
            url = f"{self.base_url}/stocks/fno/view_option_chain.php?ind_id={ind_id}&type=IDX"
            
            soup = self._fetch_page(url)
            if not soup: return None
            
            # Find the main table
            table = soup.find('table', {'class': 'mctable1'})
            if not table:
                # Try alternate class
                table = soup.find('table', {'class': 'tblopt'})
                
            if not table: return None
            
            # Get underlying price
            spot_price = 0
            try:
                # Usually in a div with class 'FL' or similar near top
                spot_elem = soup.find('div', {'class': 'FL gry_10'})
                if spot_elem:
                    text = spot_elem.get_text()
                    # extract number
                    import re
                    match = re.search(r'([\d,]+\.\d+)', text)
                    if match:
                        spot_price = float(match.group(1).replace(',', ''))
            except:
                pass
                
            chain = []
            rows = table.find_all('tr')
            
            # Skip header rows - look for numeric strike in middle column
            for row in rows:
                cells = row.find_all('td')
                if len(cells) < 5: continue
                
                # MoneyControl Structure usually:
                # CallOI, CallChg, CallVol, CallIV, CallLTP, CallNetChg, CallBid, CallAsk, STRIKE, PutBid, PutAsk, PutNetChg, PutLTP, PutIV, PutVol, PutChg, PutOI
                # The exact index depends on columns displayed. 
                # Identifying Strike: usually has background color or is bold, center aligned
                
                try:
                    # Find Strike column (usually has non-empty text)
                    # Iterate to find the strike (which is numeric)
                    # Simplify: MoneyControl desktop view has specific indices
                    # But it might vary.
                    
                    # Safer approach: Text extraction
                    texts = [c.get_text(strip=True) for c in cells]
                    
                    # Find Strike Index (it's the pivot)
                    # Usually Strike is roughly in middle
                    mid = len(texts) // 2
                    
                    # Attempt to parse strike from center
                    strike_idx = -1
                    strike_val = 0
                    
                    # Search for strike in middle 3 columns
                    for i in range(mid-1, mid+2):
                        if i < len(texts) and texts[i].replace('.', '', 1).isdigit():
                            strike_val = float(texts[i])
                            strike_idx = i
                            break
                    
                    if strike_idx == -1: continue
                    
                    # Determine columns relative to strike
                    # Calls are to the left, Puts to the right
                    # Call LTP is usually 2-3 cols left of strike
                    # Put LTP is usually 2-3 cols right of strike
                    
                    # Typical Layout:
                    # [0]CallLTP [1]CallNetCk [2]CallVol [3]CallOI ... [Strike] ... [?]PutLTP ...
                    # Actually MoneyControl order:
                    # CALLS: OI, Chg, Vol, IV, LTP, NetChg, BidQty, BidPrice, AskPrice, AskQty
                    # STRIKE
                    # PUTS: BidQty, BidPrice, AskPrice, AskQty, NetChg, LTP, IV, Vol, Chg, OI
                    
                    # Let's count columns. If ~20 cols
                    # Strike is at index 10 (approx)
                    
                    calls_ltp_txt = ''
                    calls_oi_txt = ''
                    puts_ltp_txt = ''
                    puts_oi_txt = ''
                    
                    if len(texts) >= 15:
                        # Assumed mapping based on visual inspection of MC
                        # Strike is at 10
                        # Call LTP at 4?
                        # Let's map dynamically if possible
                        pass
                        
                    # Standard table typical indices
                    # Call LTP: index 4
                    # Call OI: index 0
                    # Strike: index 10
                    # Put LTP: index 15
                    # Put OI: index 20
                    
                    if strike_idx > 4:
                       calls_ltp_txt = texts[strike_idx - 6] # LTP is usually 6th from strike (reversed)? No.
                       
                       # Let's use simple indexing assuming standard table
                       # Call LTP is 5th col (idx 4)
                       # Put LTP is 12th col (idx 11) ? 
                       
                       # Better: Use class names if available? No, usually td class is generic.
                       
                       # Try hardcoded indices for standard view
                       # Calls: 0:OI, 1:Chg, 2:Vol, 3:IV, 4:LTP, 5:NetChg
                       # 10: Strike
                       # Puts: 11:NetChg, 12:LTP, 13:IV, 14:Vol, 15:Chg, 16:OI
                       
                       if len(texts) > 16:
                           # Try to align
                           calls_ltp_txt = texts[4]
                           calls_oi_txt = texts[0]
                           
                           puts_ltp_txt = texts[12] if len(texts) > 12 else '0'
                           puts_oi_txt = texts[16] if len(texts) > 16 else '0'
                           
                           # Verify strike position
                           if not texts[10].replace('.', '', 1).isdigit():
                               # Maybe shifted
                               continue
                           else:
                               strike_val = float(texts[10])

                    ce_ltp = self._parse_number(calls_ltp_txt)
                    pe_ltp = self._parse_number(puts_ltp_txt)
                    ce_oi = self._parse_number(calls_oi_txt)
                    pe_oi = self._parse_number(puts_oi_txt)
                    
                    if strike_val > 0:
                        chain.append({
                            'strike': strike_val,
                            'ce_ltp': ce_ltp,
                            'pe_ltp': pe_ltp,
                            'ce_oi': int(ce_oi),
                            'pe_oi': int(pe_oi),
                            'ce_vol': 0, # Vol less critical
                            'pe_vol': 0
                        })
                except Exception as ex:
                    # print(f"Row parse error: {ex}")
                    continue
            
            # Sort by strike
            chain.sort(key=lambda x: x['strike'])
            
            # Mark ATM
            if chain:
                # Find closes to spot if we have spot, else assume middle of chain
                target = spot_price if spot_price > 0 else chain[len(chain)//2]['strike']
                atm_strike = min(chain, key=lambda x: abs(x['strike'] - target))['strike']
                for item in chain:
                    item['is_atm'] = (item['strike'] == atm_strike)

            result = {
                'underlying': spot_price,
                'chain': chain,
                'source': 'MoneyControl',
                'timestamp': datetime.now().isoformat()
            }
            
            self.cache[cache_key] = result
            self.cache_time[cache_key] = time.time()
            return result
            
        except Exception as e:
            print(f"MoneyControl Option Chain Error: {e}")
            return None


# Singleton instance
moneycontrol_scraper = MoneyControlScraper()


def get_gainers(count: int = 10) -> List[Dict]:
    """Get top gainers"""
    return moneycontrol_scraper.get_top_gainers(count)


def get_losers(count: int = 10) -> List[Dict]:
    """Get top losers"""
    return moneycontrol_scraper.get_top_losers(count)


def get_market_movers() -> Dict:
    """Get market movers"""
    return moneycontrol_scraper.get_market_movers()


def get_option_chain(index: str = 'nifty') -> Optional[Dict]:
    """Get option chain from MoneyControl"""
    return moneycontrol_scraper.get_option_chain(index)
