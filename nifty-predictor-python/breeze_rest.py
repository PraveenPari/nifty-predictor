"""Read-only Breeze REST client.

Implements the customer-details, quotes, option-chain and historical-v2
requests described by ICICI.  The SDK 1.0.69 downloads SecurityMaster.zip at
import time, although these REST endpoints do not need it.  Keeping this
client separate avoids that startup dependency and applies socket timeouts.
See https://api.icicidirect.com/breezeapi/documents/index.html
"""
import base64
import binascii
import hashlib
import json
from datetime import datetime, timezone

import requests


class BreezeError(Exception):
    """A safe-to-display error that never includes request credentials."""


class BreezeAPIError(BreezeError):
    """The server returned an API error (as distinct from transport failure)."""


class BreezeSessionError(BreezeAPIError):
    """ICICI explicitly reported an invalid or expired session."""


class BreezeRest:
    API = 'https://api.icicidirect.com/breezeapi/api/v1/'
    API_V2 = 'https://breezeapi.icicidirect.com/api/v2/'

    def __init__(self, api_key, secret_key, timeout=15):
        self.api_key = api_key
        self.secret_key = secret_key
        self.timeout = timeout
        self.session = None

    @staticmethod
    def _response(response):
        try:
            result = response.json()
        except (ValueError, TypeError):
            raise BreezeError('Breeze returned an invalid response') from None
        if not isinstance(result, dict):
            raise BreezeError('Breeze returned an invalid response')
        if response.status_code >= 400 or result.get('Status', 200) not in (200, '200'):
            # Broker messages are not reflected verbatim: they may echo credentials.
            if str(result.get('Error') or '').strip().lower() in (
                    'invalid session.', 'invalid session', 'session expired',
                    'session expired.', 'resource not available.'):
                raise BreezeSessionError('Breeze session expired or invalid; reconnect')
            status = result.get("Status")
            status = str(status) if isinstance(status, int) or (isinstance(status, str) and status.isdigit() and len(status) <= 3) else "unknown"
            raise BreezeAPIError(f"Breeze request rejected (HTTP {response.status_code}, API status {status})")
        return result

    def _get(self, url, **kwargs):
        try:
            response = requests.get(url, timeout=self.timeout, **kwargs)
        except requests.Timeout:
            raise BreezeError('Breeze request timed out; try again') from None
        except requests.RequestException:
            raise BreezeError('Could not reach Breeze; try again') from None
        return self._response(response)

    def authenticate(self, token):
        body = json.dumps({'SessionToken': token, 'AppKey': self.api_key}, separators=(',', ':'))
        result = self._get(self.API + 'customerdetails', data=body,
                           headers={'Content-Type': 'application/json'})
        try:
            session = result['Success']['session_token']
            decoded = base64.b64decode(session, validate=True).decode('ascii')
            user, key = decoded.split(':', 1)
            if not user or not key:
                raise ValueError
        except (KeyError, TypeError, ValueError, UnicodeError, binascii.Error):
            raise BreezeError('Breeze login response did not contain a valid session') from None
        self.session = session

    def _signed_get(self, endpoint, fields):
        body = json.dumps({k: v for k, v in fields.items() if v is not None and v != ''},
                          separators=(',', ':'))
        stamp = datetime.now(timezone.utc).isoformat()[:19] + '.000Z'
        checksum = hashlib.sha256((stamp + body + self.secret_key).encode('utf-8')).hexdigest()
        headers = {'Content-Type': 'application/json', 'X-Checksum': 'token ' + checksum,
                   'X-Timestamp': stamp, 'X-AppKey': self.api_key,
                   'X-SessionToken': self.session}
        return self._get(self.API + endpoint, data=body, headers=headers)

    def get_quotes(self, **fields):
        return self._signed_get('quotes', fields)

    def get_option_chain_quotes(self, **fields):
        return self._signed_get('optionchain', fields)

    def get_historical_data_v2(self, **fields):
        fields = dict(fields)
        fields['exch_code'] = fields.pop('exchange_code')
        headers = {'Content-Type': 'application/json', 'X-SessionToken': self.session,
                   'apikey': self.api_key}
        return self._get(self.API_V2 + 'historicalcharts', params=fields, headers=headers)
