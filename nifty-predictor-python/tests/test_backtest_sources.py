"""Offline provider-selection and backtest source tests."""
import os
import unittest
from unittest.mock import patch

# No real broker credentials or token needed for tests.
os.environ['BREEZE_API_KEY'] = ''
os.environ['BREEZE_SECRET_KEY'] = ''
os.environ['BREEZE_SESSION_TOKEN'] = ''
os.environ['DEMO_MODE'] = '0'

import app


def candles(n):
    return [{'time': f'2026-01-14T09:{15 + i % 45:02}:00+05:30',
             'open': 100 + i, 'high': 102 + i, 'low': 99 + i,
             'close': 101 + i, 'volume': 10} for i in range(n)]


class BacktestSourceTests(unittest.TestCase):
    def setUp(self):
        self.flags = patch.multiple(app, DEMO_MODE=False, BREEZE_AVAILABLE=True,
                                    ANGEL_AVAILABLE=False, YAHOO_AVAILABLE=True)
        self.flags.start()
        self.addCleanup(self.flags.stop)
        self.connected = patch.object(app.breeze_manager, 'is_connected', return_value=True)
        self.connected.start()
        self.addCleanup(self.connected.stop)
        self.skip = patch.object(app, '_breaker_skip', return_value=False)
        self.skip.start()
        self.addCleanup(self.skip.stop)
        self.http = app.app.test_client()

    @patch.object(app.yahoo_manager, 'get_candles')
    @patch.object(app.breeze_manager, 'get_historical_data')
    def test_backtest_uses_and_reports_breeze(self, breeze, yahoo):
        breeze.return_value = candles(25)
        result = self.http.get('/api/backtest?index=nifty&days=7')
        self.assertEqual(result.status_code, 200)
        data = result.get_json()
        self.assertEqual(data['data_source'], 'Breeze')
        self.assertEqual(data['candles_used'], 25)
        self.assertTrue(data['simulated'])
        self.assertEqual(data['strategy'], 'SMA crossover')
        breeze.assert_called_once_with('nifty', '5minute', 7)
        yahoo.assert_not_called()

    @patch.object(app.yahoo_manager, 'get_candles')
    @patch.object(app.breeze_manager, 'get_historical_data')
    def test_short_breeze_data_uses_and_reports_yahoo(self, breeze, yahoo):
        breeze.return_value = candles(10)
        yahoo.return_value = candles(25)
        result = self.http.get('/api/backtest?index=nifty&days=30')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.get_json()['data_source'], 'Yahoo Finance')
        yahoo.assert_called_once_with('nifty', '5m', '1mo')

    @patch.object(app.yahoo_manager, 'get_candles')
    @patch.object(app.breeze_manager, 'get_historical_data')
    def test_insufficient_candles_do_not_report_a_fake_source(self, breeze, yahoo):
        breeze.return_value = candles(10)
        yahoo.return_value = candles(3)
        result = self.http.get('/api/backtest?index=nifty&days=5')
        self.assertEqual(result.status_code, 503)
        self.assertEqual(result.get_json()['error'], 'INSUFFICIENT_DATA')
        self.assertNotIn('data_source', result.get_json())

    @patch.object(app, 'analyze_recent_trades', return_value={'trades': [], 'summary': {}})
    @patch.object(app.breeze_manager, 'get_historical_data', return_value=candles(20))
    def test_recent_trades_identifies_simulation_and_source(self, breeze, analysis):
        result = self.http.get('/api/recent-trades?index=nifty&hours=4')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.get_json()['data_source'], 'Breeze')
        self.assertTrue(result.get_json()['simulated'])


if __name__ == '__main__':
    unittest.main()
