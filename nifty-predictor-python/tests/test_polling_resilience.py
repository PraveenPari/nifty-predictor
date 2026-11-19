"""Offline tests for expensive request coalescing."""
import os
import threading
import unittest
from unittest.mock import patch

os.environ['BREEZE_API_KEY'] = ''
os.environ['BREEZE_SECRET_KEY'] = ''
os.environ['BREEZE_SESSION_TOKEN'] = ''
os.environ['DEMO_MODE'] = '0'

import app
import stock_analyzer


class PollingTests(unittest.TestCase):
    def setUp(self):
        app._ANALYSIS_CACHE.clear()

    def test_analysis_singleflight_returns_busy_then_cached(self):
        started, release = threading.Event(), threading.Event()
        outcomes = []

        def slow(index):
            started.set()
            self.assertTrue(release.wait(3))
            return {'index': index, 'price_data': {'source': 'Breeze'}}

        with patch.object(app, '_compute_market_analysis', side_effect=slow) as compute:
            worker = threading.Thread(target=lambda: outcomes.append(app.get_market_analysis('nifty')))
            worker.start()
            try:
                self.assertTrue(started.wait(2))
                busy = app.get_market_analysis('nifty')
                self.assertEqual(busy['error'], 'ANALYSIS_BUSY')
            finally:
                release.set()
                worker.join(4)
            self.assertFalse(worker.is_alive())
            self.assertEqual(outcomes[0]['price_data']['source'], 'Breeze')
            cached = app.get_market_analysis('nifty')
            self.assertTrue(cached['analysis_cached'])
            self.assertIn('analysis_age_seconds', cached)
            self.assertEqual(compute.call_count, 1)

    def test_failed_analysis_not_cached(self):
        with patch.object(app, '_compute_market_analysis', return_value={'error': 'NO_DATA'}) as compute:
            app.get_market_analysis('nifty')
            app.get_market_analysis('nifty')
            self.assertEqual(compute.call_count, 2)

    def test_stock_scan_singleflight_and_cache(self):
        analyzer = stock_analyzer.StockAnalyzer()
        started, release = threading.Event(), threading.Event()
        outcomes = []
        def slow(_code, _info):
            started.set()
            self.assertTrue(release.wait(3))
            return {'short_term_score': 50}
        with patch.object(stock_analyzer, 'NIFTY50_STOCKS', {'TEST': {}}), \
             patch.object(analyzer, 'analyze_stock', side_effect=slow) as scan:
            worker = threading.Thread(target=lambda: outcomes.append(analyzer.analyze_all_stocks()))
            worker.start()
            try:
                self.assertTrue(started.wait(2))
                with self.assertRaises(stock_analyzer.StockScanInProgress):
                    analyzer.analyze_all_stocks()
            finally:
                release.set()
                worker.join(4)
            self.assertFalse(worker.is_alive())
            self.assertEqual(len(outcomes[0]), 1)
            self.assertEqual(analyzer.analyze_all_stocks(), outcomes[0])
            self.assertEqual(scan.call_count, 1)

    def test_stock_scan_busy_is_503_not_500(self):
        with patch.object(app, 'get_short_term_picks', side_effect=stock_analyzer.StockScanInProgress()):
            result = app.app.test_client().get('/api/top-stocks/short-term')
        self.assertEqual(result.status_code, 503)
        self.assertEqual(result.get_json()['error'], 'STOCK_SCAN_IN_PROGRESS')


if __name__ == '__main__':
    unittest.main()
