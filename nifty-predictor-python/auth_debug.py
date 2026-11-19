"""Inspect non-secret Breeze status from a running local app."""
import requests

try:
    response = requests.get('http://127.0.0.1:5000/api/status', timeout=5)
    response.raise_for_status()
    status = response.json()
    for field in ('breeze_connected', 'breeze_session_configured',
                  'breeze_error_code', 'breeze_startup_quote'):
        print(f'{field}: {status.get(field)}')
except requests.RequestException:
    print('Could not reach local app status.')
