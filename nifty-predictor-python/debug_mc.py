import requests
from bs4 import BeautifulSoup

url = "https://www.moneycontrol.com/stocks/fno/view_option_chain.php?ind_id=9&type=IDX"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
}

try:
    print(f"Fetching {url}...")
    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    table = soup.find('table', {'class': 'tblopt'})
    if table:
         print("Found tblopt.")
         html = str(table)[:2000]
         print(html)
         
         rows = table.find_all('tr')
         print(f"Row count: {len(rows)}")
    else:
        print("Table tblopt not found")

except Exception as e:
    print(f"Error: {e}")
