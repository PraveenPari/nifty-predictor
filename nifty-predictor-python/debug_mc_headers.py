import requests
from bs4 import BeautifulSoup

url = "https://www.moneycontrol.com/stocks/fno/view_option_chain.php?ind_id=9&type=IDX"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.moneycontrol.com/stocks/fno/view_option_chain.php',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
}

try:
    print(f"Fetching {url} with headers...")
    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    table = soup.find('table', {'class': 'tblopt'}) or soup.find('table', {'class': 'mctable1'})
    if table:
         rows = table.find_all('tr')
         print(f"Row count: {len(rows)}")
         if len(rows) > 2:
             print("Success! Found rows.")
         else:
             print("Found table but empty rows.")
    else:
        print("Table not found")

except Exception as e:
    print(f"Error: {e}")
