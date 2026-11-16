import requests
import time

token = '54602447'
print(f"Authenticating with token: {token}")

try:
    resp = requests.post('http://127.0.0.1:5000/api/breeze-auth', json={'token': token})
    print(f"Auth Response: {resp.json()}")
    
    time.sleep(1)
    
    status = requests.get('http://127.0.0.1:5000/api/status').json()
    print(f"Breeze Connected: {status.get('breeze_connected')}")
except Exception as e:
    print(f"Error: {e}")
