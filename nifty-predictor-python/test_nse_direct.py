import requests
import json
import time

def fetch_nse_option_chain():
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9',
        'referer': 'https://www.nseindia.com/option-chain'
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        # 1. Visit homepage
        print("Visiting NSE homepage...")
        session.get("https://www.nseindia.com", timeout=10)
        
        # 2. Visit Option Chain page to get specific cookies
        session.get("https://www.nseindia.com/option-chain", timeout=10)
        
        # 3. Fetch API
        print("Fetching Option Chain API...")
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
        response = session.get(url, timeout=10)
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Keys: {list(data.keys())}")
                if 'records' in data:
                    print(f"Expiry Dates: {data['records'].get('expiryDates', [])[:3]}")
                    return True
                else:
                    print("No 'records' in data")
                    return False
            except Exception as e:
                print(f"JSON Error: {e}")
                return False
        else:
            print(f"Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

fetch_nse_option_chain()
