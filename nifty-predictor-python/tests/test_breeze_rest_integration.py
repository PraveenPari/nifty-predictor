"""Offline contract tests for the read-only Breeze integration."""
import base64
import hashlib
import json
import os
import subprocess
import sys
import unittest
from unittest.mock import patch

import requests

from breeze_rest import BreezeError, BreezeRest
from breeze_manager import BreezeManager
from secrets_manager import breeze_login_url


class Response:
    def __init__(self, value, status=200):
        self.value = value
        self.status_code = status

    def json(self):
        return self.value


class BreezeTests(unittest.TestCase):
    def setUp(self):
        self.session = base64.b64encode(b'example-user:example-session').decode()
        self.client = BreezeRest('example-key', 'example-secret', timeout=7)

    @patch('breeze_rest.requests.get')
    def test_auth_quote_checksum_and_history_contract(self, get):
        get.side_effect = [Response({'Success': {'session_token': self.session}, 'Status': 200}),
                           Response({'Success': [{'ltp': 123}], 'Status': 200}),
                           Response({'Success': [], 'Status': 200})]
        self.client.authenticate('example-token')
        auth = get.call_args_list[0]
        self.assertEqual(auth.args[0], self.client.API + 'customerdetails')
        self.assertEqual(json.loads(auth.kwargs['data']), {'SessionToken': 'example-token', 'AppKey': 'example-key'})
        self.assertEqual(auth.kwargs['timeout'], 7)
        self.client.get_quotes(stock_code='NIFTY', exchange_code='nse', product_type='cash')
        quote = get.call_args_list[1]
        self.assertEqual(quote.args[0], self.client.API + 'quotes')
        headers, body = quote.kwargs['headers'], quote.kwargs['data']
        self.assertEqual(headers['X-SessionToken'], self.session)
        checksum = hashlib.sha256((headers['X-Timestamp'] + body + 'example-secret').encode()).hexdigest()
        self.assertEqual(headers['X-Checksum'], 'token ' + checksum)
        self.client.get_historical_data_v2(stock_code='NIFTY', exchange_code='nse', interval='5minute')
        history = get.call_args_list[2]
        self.assertEqual(history.args[0], self.client.API_V2 + 'historicalcharts')
        self.assertEqual(history.kwargs['params']['exch_code'], 'nse')
        self.assertNotIn('exchange_code', history.kwargs['params'])
        self.assertEqual(history.kwargs['headers']['apikey'], 'example-key')
        self.assertEqual(history.kwargs['timeout'], 7)

    @patch('breeze_rest.requests.get')
    def test_errors_are_safe_and_timeout_is_set(self, get):
        get.side_effect = requests.Timeout('secret-bearing exception')
        with self.assertRaisesRegex(BreezeError, 'timed out') as error:
            self.client.authenticate('example-token')
        self.assertNotIn('secret', str(error.exception))
        self.assertEqual(get.call_args.kwargs['timeout'], 7)
        get.side_effect = None
        get.return_value = Response({'Status': 500, 'Error': 'example-token'}, 200)
        with self.assertRaises(BreezeError) as error:
            self.client.authenticate('example-token')
        self.assertNotIn('example-token', str(error.exception))

    @patch('breeze_rest.requests.get')
    def test_manager_probe_is_fresh_and_uses_broker_percent(self, get):
        quote = {'ltp': '123', 'open': '100', 'previous_close': '120',
                 'ltp_percent_change': '2.5', 'high': 125, 'low': 118,
                 'ltt': 'market timestamp'}
        get.side_effect = [Response({'Success': {'session_token': self.session}, 'Status': 200}),
                           Response({'Success': [quote], 'Status': 200})]
        manager = BreezeManager()
        manager.api_key, manager.secret_key = 'example-key', 'example-secret'
        manager.cache['ltp_nifty'] = {'ltp': 999}
        manager.cache_time['ltp_nifty'] = 10**12
        self.assertTrue(manager.set_session_token('example-token'))
        self.assertEqual(manager.last_probe['ltp'], 123)
        self.assertEqual(manager.last_probe['change'], 2.5)
        self.assertEqual(manager.last_probe['last_trade_time'], 'market timestamp')
        self.assertEqual(get.call_count, 2)

    @patch('breeze_rest.requests.get')
    def test_expired_quote_session_does_not_report_connected(self, get):
        get.side_effect = [Response({'Success': {'session_token': self.session}, 'Status': 200}),
                           Response({'Success': None, 'Status': 500, 'Error': 'Invalid session.'})]
        manager = BreezeManager()
        manager.api_key, manager.secret_key = 'example-key', 'example-secret'
        self.assertFalse(manager.set_session_token('example-token'))
        self.assertFalse(manager.connected)
        self.assertEqual(manager.last_error_code, 'BREEZE_AUTH_REJECTED')
        self.assertIsNone(manager.last_probe)

    @patch('breeze_rest.requests.get')
    def test_quote_failure_not_claimed_as_verified(self, get):
        get.side_effect = [Response({'Success': {'session_token': self.session}, 'Status': 200}),
                           Response({'Success': [], 'Status': 200})]
        manager = BreezeManager()
        manager.api_key, manager.secret_key = 'example-key', 'example-secret'
        self.assertTrue(manager.set_session_token('example-token'))
        self.assertIsNone(manager.last_probe)
        self.assertIn('quote probe', manager.last_error)

    @patch('breeze_rest.requests.get')
    def test_history_market_hours_are_utc_and_candles_map(self, get):
        get.return_value = Response({'Status': 200, 'Success': [
            {'datetime': '2026-01-01 09:15:00', 'open': '10', 'high': '12',
             'low': '9', 'close': '11', 'volume': '123'}]})
        manager = BreezeManager()
        manager.connected = True
        manager.breeze = self.client
        self.client.session = self.session
        candles = manager.get_historical_data('nifty')
        self.assertEqual(candles[0]['close'], 11)
        params = get.call_args.kwargs['params']
        self.assertTrue(params['from_date'].endswith('T03:45:00.000Z'))
        self.assertTrue(params['to_date'].endswith('T10:00:00.000Z'))

    @patch('breeze_rest.requests.get')
    def test_rejected_and_timeout_auth_have_distinct_status(self, get):
        manager = BreezeManager()
        manager.api_key, manager.secret_key = 'example-key', 'example-secret'
        get.return_value = Response({'Status': 500, 'Error': 'Invalid session.'})
        self.assertFalse(manager.set_session_token('example-token'))
        self.assertEqual(manager.last_error_code, 'BREEZE_AUTH_REJECTED')
        get.side_effect = requests.Timeout('secret-bearing exception')
        self.assertFalse(manager.set_session_token('example-token'))
        self.assertEqual(manager.last_error_code, 'BREEZE_UNAVAILABLE')

    def test_login_url_escapes_key(self):
        with patch.dict(os.environ, {'BREEZE_API_KEY': 'a+b/='}):
            self.assertEqual(breeze_login_url(), 'https://api.icicidirect.com/apiuser/login?api_key=a%2Bb%2F%3D')

    def test_import_does_not_fetch_security_master(self):
        script = "import urllib.request; urllib.request.urlopen=lambda *a, **k: (_ for _ in ()).throw(RuntimeError('network during import')); import breeze_manager; assert 'breeze_connect' not in __import__('sys').modules"
        env = dict(os.environ, BREEZE_SESSION_TOKEN='')
        subprocess.run([sys.executable, '-c', script], env=env, check=True, capture_output=True, timeout=10)

    def test_option_chain_maps_string_strikes_and_iso_expiry(self):
        class FakeClient:
            def get_quotes(self, **kwargs):
                return {'Success': [{'ltp': 100, 'high': 100, 'low': 100}]}
            def get_option_chain_quotes(self, **kwargs):
                self.expiry = kwargs['expiry_date']
                return {'Success': [{'strike_price': '100.0', 'open_interest': '10', 'ltp': '5'}]}
        manager = BreezeManager()
        manager.connected, manager.breeze = True, FakeClient()
        result = manager.get_option_chain('nifty')
        self.assertEqual(result['chain'][0]['ce_oi'], 10)
        self.assertEqual(result['chain'][0]['pe_oi'], 10)
        self.assertTrue(manager.breeze.expiry.endswith('T06:00:00.000Z'))


if __name__ == '__main__':
    unittest.main()
