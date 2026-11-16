"""
Nifty Predictor Pro - Python Flask Server
Professional ML Trading System with Breeze API + Yahoo Finance Hybrid.

Run locally:
    pip install -r requirements.txt
    cp .env.example .env   # fill in secrets
    python app.py

Production (Render/Railway/Docker):
    gunicorn -c gunicorn.conf.py app:app
"""

import os
import threading
import time
from datetime import datetime

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from flask_cors import CORS
from flask.json.provider import DefaultJSONProvider

import numpy as np

# ---------------------------------------------------------------------------
# Configuration (environment-first, safe defaults)
# ---------------------------------------------------------------------------

PORT = int(os.getenv("PORT", "5000"))
SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("FLASK_SECRET_KEY") or "dev-only-insecure-key"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
IS_PROD = os.getenv("FLASK_ENV", "production").lower() == "production"

from pro_config.trading_config import INDEX_CONFIG, MARKET_OPEN, MARKET_CLOSE, SIGNAL_CONFIG  # noqa: E402

print("[BOOT] Loading indicators...")
from indicators_fast import TechnicalIndicatorsFast as TechnicalIndicators  # noqa: E402
print("[BOOT] Loading strategies...")
from strategies import TradingStrategies  # noqa: E402

# Optional: ML predictors (need scikit-learn; app works without them)
try:
    from ml_predictor import get_ml_prediction, train_ml_model  # noqa: E402
    ML_AVAILABLE = True
except Exception as e:
    ML_AVAILABLE = False
    print(f"[BOOT] ml_predictor disabled: {e}")

    def get_ml_prediction(*a, **k):
        return {'direction': 'NEUTRAL', 'confidence': 50, 'bullish_prob': 50,
                'bearish_prob': 50, 'disabled': True}

    def train_ml_model(*a, **k):
        return {'success': False, 'message': 'ML unavailable (scikit-learn not installed)'}

try:
    from stable_ml_predictor import (  # noqa: E402
        get_stable_prediction, train_stable_model, get_ml_stats, validate_past_predictions,
    )
    STABLE_ML_AVAILABLE = True
except Exception as e:
    STABLE_ML_AVAILABLE = False
    print(f"[BOOT] stable_ml_predictor disabled: {e}")

    def get_stable_prediction(*a, **k):
        return {'direction': 'NEUTRAL', 'confidence': 50, 'bullish_prob': 50,
                'bearish_prob': 50, 'disabled': True}

    def train_stable_model(*a, **k):
        return {'success': False, 'message': 'Stable ML unavailable'}

    def get_ml_stats(*a, **k):
        return {'is_trained': False, 'disabled': True}

    def validate_past_predictions(*a, **k):
        return None

# Optional: Angel One (needs SmartApi + credentials)
try:
    from angel_one_enhanced import angel_one_enhanced  # noqa: E402
    ANGEL_AVAILABLE = True
except Exception as e:
    ANGEL_AVAILABLE = False
    print(f"[BOOT] angel_one disabled: {e}")

    class _AngelStub:
        is_logged_in = False
        client_code = None

        def get_ltp(self, *a, **k):
            return None

        def get_candles(self, *a, **k):
            return []

        def get_option_chain(self, *a, **k):
            return None

    angel_one_enhanced = _AngelStub()

# Optional: Breeze (needs breeze-connect + secrets)
try:
    from breeze_manager import breeze_manager  # noqa: E402
    BREEZE_AVAILABLE = True
except Exception as e:
    BREEZE_AVAILABLE = False
    print(f"[BOOT] breeze disabled: {e}")

    class _BreezeStub:
        def is_connected(self):
            return False

        def get_live_price(self, *a, **k):
            return None

        def get_historical_data(self, *a, **k):
            return []

        def get_option_chain(self, *a, **k):
            return None

        def get_vix(self, *a, **k):
            return None

        def generate_session_token(self):
            return None

        def set_session_token(self, *a, **k):
            return False

    breeze_manager = _BreezeStub()

# Optional: Yahoo (needs yfinance — primary free fallback)
try:
    from yahoo_manager import yahoo_manager  # noqa: E402
    YAHOO_AVAILABLE = True
except Exception as e:
    YAHOO_AVAILABLE = False
    print(f"[BOOT] yahoo disabled: {e}")
    yahoo_manager = None

# Optional: Pro trader math (needs scipy)
try:
    from pro_trader import pro_trader, LOT_SIZES  # noqa: E402
    PRO_TRADER_AVAILABLE = True
except Exception as e:
    PRO_TRADER_AVAILABLE = False
    print(f"[BOOT] pro_trader disabled: {e}")
    LOT_SIZES = {'nifty': 75, 'banknifty': 30}
    pro_trader = None

# Optional: stock picks + market movers
try:
    from stock_analyzer import (  # noqa: E402
        get_short_term_picks, get_long_term_picks, get_all_analysis, get_market_overview,
    )
    STOCKS_AVAILABLE = True
except Exception as e:
    STOCKS_AVAILABLE = False
    print(f"[BOOT] stock_analyzer disabled: {e}")

try:
    from moneycontrol_scraper import get_market_movers, get_option_chain as get_mc_option_chain  # noqa: E402
    MC_AVAILABLE = True
except Exception as e:
    MC_AVAILABLE = False
    print(f"[BOOT] moneycontrol disabled: {e}")

    def get_market_movers(*a, **k):
        return {'gainers': [], 'losers': [], 'disabled': True}

    def get_mc_option_chain(*a, **k):
        return None

from accuracy_tracker import accuracy_tracker  # noqa: E402
from trade_analytics import analyze_recent_trades  # noqa: E402
from secrets_manager import breeze_login_url, safe_status  # noqa: E402

# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = SECRET_KEY


class NumpyJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        if isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


app.json = NumpyJSONProvider(app)
CORS(app, resources={r"/api/*": {"origins": CORS_ORIGINS}})

socketio = SocketIO(app, cors_allowed_origins="*" if CORS_ORIGINS == "*" else CORS_ORIGINS,
                    async_mode='threading')

is_running = True
_bg_started = False
_bg_lock = threading.Lock()

# Breeze interval names for historical API
_BREEZE_TF = {'5m': '5minute', '15m': '15minute', '1h': '1hour', '1d': '1day'}
_YAHOO_PERIOD = {'5m': '5d', '15m': '5d', '1h': '1mo', '1d': '3mo'}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_market_open():
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    time_min = now.hour * 60 + now.minute
    start = MARKET_OPEN['hour'] * 60 + MARKET_OPEN['minute']
    end = MARKET_CLOSE['hour'] * 60 + MARKET_CLOSE['minute']
    return start <= time_min <= end


def _norm_index(index: str) -> str:
    return 'banknifty' if 'bank' in (index or '').lower() else 'nifty'


def get_live_price_hybrid(index: str):
    """Live price: Breeze -> Angel One -> Yahoo."""
    index = _norm_index(index)
    if BREEZE_AVAILABLE and breeze_manager.is_connected():
        data = breeze_manager.get_live_price(index)
        if data:
            return data
    if ANGEL_AVAILABLE and angel_one_enhanced.is_logged_in:
        data = angel_one_enhanced.get_ltp(index)
        if data:
            return data
    if YAHOO_AVAILABLE:
        return yahoo_manager.get_live_price(index)
    return None


def get_candles_hybrid(index: str, tf: str = '5m', days: int = 5):
    """Candles: Breeze -> Angel One -> Yahoo."""
    index = _norm_index(index)
    candles = None
    if BREEZE_AVAILABLE and breeze_manager.is_connected():
        candles = breeze_manager.get_historical_data(index, _BREEZE_TF.get(tf, '5minute'), days)
    if (not candles or len(candles) < 5) and ANGEL_AVAILABLE and angel_one_enhanced.is_logged_in:
        tf_map = {'5m': 'FIVE_MINUTE', '15m': 'FIFTEEN_MINUTE', '1h': 'ONE_HOUR', '1d': 'ONE_DAY'}
        candles = angel_one_enhanced.get_candles(index, tf_map.get(tf, 'FIVE_MINUTE'), days=days)
    if (not candles or len(candles) < 5) and YAHOO_AVAILABLE:
        candles = yahoo_manager.get_candles(index, tf, _YAHOO_PERIOD.get(tf, '5d'))
    return candles or []


def get_option_chain_hybrid(index: str):
    """Option chain with real premiums: Breeze -> Angel One -> MoneyControl -> Yahoo."""
    index = _norm_index(index)

    def has_valid_premiums(oc):
        if not oc or not oc.get('chain'):
            return False
        return any(r.get('ce_ltp', 0) > 0 or r.get('pe_ltp', 0) > 0 for r in oc['chain'])

    if BREEZE_AVAILABLE and breeze_manager.is_connected():
        oc = breeze_manager.get_option_chain(index)
        if oc and oc.get('chain') and has_valid_premiums(oc):
            return oc
    if ANGEL_AVAILABLE and angel_one_enhanced.is_logged_in:
        oc = angel_one_enhanced.get_option_chain(index)
        if oc and oc.get('chain') and has_valid_premiums(oc):
            return oc
    if MC_AVAILABLE:
        oc = get_mc_option_chain(index)
        if oc and oc.get('chain') and has_valid_premiums(oc):
            return oc
    if YAHOO_AVAILABLE:
        oc = yahoo_manager.get_option_chain(index)
        if oc and oc.get('chain'):
            return oc
    # Last resort: skeleton chain (OI only) so levels still render
    if ANGEL_AVAILABLE and angel_one_enhanced.is_logged_in:
        return angel_one_enhanced.get_option_chain(index)
    return None


def get_vix_hybrid():
    if BREEZE_AVAILABLE:
        vix_data = breeze_manager.get_vix()
        if vix_data and vix_data.get('ltp'):
            return vix_data
    if YAHOO_AVAILABLE:
        return yahoo_manager.get_vix()
    return {'ltp': 14, 'source': 'default'}


def get_market_analysis(index='nifty'):
    """Complete market analysis with hybrid data sources."""
    index = _norm_index(index)
    price_data = get_live_price_hybrid(index)
    if not price_data:
        return {
            'error': 'NO_DATA',
            'message': 'Failed to fetch live price from all sources.',
            'index': index,
            'timestamp': datetime.now().isoformat()
        }

    try:
        candles = get_candles_hybrid(index, '5m', 5)
        if not candles or len(candles) < 5:
            return {
                'error': 'NO_CANDLE_DATA',
                'message': 'Failed to fetch candle data.',
                'index': index,
                'price_data': price_data,
                'timestamp': datetime.now().isoformat()
            }

        indicators = TechnicalIndicators.calculate_all(candles)

        vix_data = get_vix_hybrid()
        vix_value = vix_data.get('ltp', 14) if vix_data else 14

        oc = get_option_chain_hybrid(index)

        pcr = 1.0
        total_ce_oi = 0
        total_pe_oi = 0
        if oc and oc.get('chain'):
            for row in oc['chain']:
                total_ce_oi += row.get('ce_oi', 0)
                total_pe_oi += row.get('pe_oi', 0)
            if total_ce_oi > 0:
                pcr = round(total_pe_oi / total_ce_oi, 2)

        fii_dii_data = yahoo_manager.get_fii_dii() if YAHOO_AVAILABLE else {}

        sentiment = {
            'overall_sentiment': 'NEUTRAL',
            'sentiment_score': 0,
            'vix': round(vix_value, 2),
            'pcr': pcr,
            'total_ce_oi': total_ce_oi,
            'total_pe_oi': total_pe_oi,
            'fii_net': fii_dii_data.get('fii_net', 0),
            'dii_net': fii_dii_data.get('dii_net', 0)
        }
        if pcr > 1.2 and vix_value < 18:
            sentiment['overall_sentiment'] = 'BULLISH'
            sentiment['sentiment_score'] = 20
        elif pcr < 0.8 or vix_value > 20:
            sentiment['overall_sentiment'] = 'BEARISH'
            sentiment['sentiment_score'] = -20

        option_chain_data = oc.get('chain', []) if oc else []
        strategy_result = TradingStrategies.analyze_all(
            indicators, price_data['ltp'], sentiment, candles, option_chain_data)
        strategies = strategy_result.get('strategies', [])

        stable_ml_prediction = get_stable_prediction(candles, indicators)
        ml_prediction = get_ml_prediction(candles, indicators)

        prediction = TradingStrategies.calculate_prediction(strategies)
        combined_ce_prob = (prediction['ce_prob'] * 0.3 + stable_ml_prediction.get('bullish_prob', 50) * 0.7)
        combined_pe_prob = (prediction['pe_prob'] * 0.3 + stable_ml_prediction.get('bearish_prob', 50) * 0.7)

        direction = stable_ml_prediction.get('direction', 'NEUTRAL')
        confidence = stable_ml_prediction.get('confidence', 50)

        # --- Trade math ---
        ltp = price_data['ltp']
        lot_size = LOT_SIZES.get(index, 25)

        if direction == 'BULLISH':
            entry, stop_loss, target = ltp, round(ltp * 0.995, 2), round(ltp * 1.015, 2)
        else:
            entry, stop_loss, target = ltp, round(ltp * 1.005, 2), round(ltp * 0.985, 2)

        if PRO_TRADER_AVAILABLE:
            rr = pro_trader.calculate_risk_reward(entry, stop_loss, target)
            estimated_premium = abs(ltp - target) * 0.5 + 50
            lot_calc = pro_trader.calculate_lot_size(estimated_premium, 30, 5000, lot_size)
            option_rec = pro_trader.calculate_option_recommendation(
                index, ltp, direction, option_chain_data, 30)
            forward_prediction = pro_trader.predict_direction_15min(candles, indicators, ml_prediction)
            backtest = pro_trader.backtest_strategy(candles, 'momentum')
            rr_ratio = rr.get('ratio', 0)
            suggested_lots = lot_calc.get('suggested_lots', 1)
            max_loss = lot_calc.get('max_loss', 0)
        else:
            rr_ratio, suggested_lots, max_loss = 3.0, 1, 0
            option_rec = {'recommendation': 'Pro trader module unavailable'}
            forward_prediction = {'direction': direction, 'confidence': confidence}
            backtest = {'win_rate': 0, 'disabled': True}

        points_move = abs(target - entry)
        profit_per_lot = points_move * lot_size
        total_profit = profit_per_lot * suggested_lots

        return {
            'index': index,
            'price_data': price_data,
            'indicators': indicators,
            'strategies': strategies,
            'sentiment': sentiment,
            'vix': vix_data,
            'prediction': {
                'direction': direction,
                'ce_prob': round(combined_ce_prob),
                'pe_prob': round(combined_pe_prob),
                'stable_ml': stable_ml_prediction,
                'ml': ml_prediction
            },
            'trade_recommendation': {
                'direction': direction,
                'recommendation': f"BUY {'CALL' if direction == 'BULLISH' else 'PUT'}" if confidence > 60 else 'WAIT',
                'confidence': confidence,
                'entry': round(entry, 2),
                'stop_loss': round(stop_loss, 2),
                'target': round(target, 2),
                'suggested_lots': suggested_lots,
                'risk_reward': rr_ratio,
                'profit_on_target': round(total_profit, 2),
                'lot_size': lot_size,
                'max_loss': max_loss
            },
            'option_recommendation': option_rec,
            'forward_prediction': forward_prediction,
            'backtest': backtest,
            'pro_analysis': strategy_result.get('pro_analysis', ""),
            'pro_verdict': strategy_result.get('pro_verdict'),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[ERROR] Analysis failed: {e}")
        return {'error': 'ANALYSIS_ERROR', 'message': str(e)}


# ---------------------------------------------------------------------------
# Routes — pages & health
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/healthz')
@app.route('/api/health')
def health():
    """Liveness probe for hosts / load balancers. No secrets exposed."""
    return jsonify({
        'status': 'ok',
        'market_open': is_market_open(),
        'breeze_connected': bool(BREEZE_AVAILABLE and breeze_manager.is_connected()),
        'timestamp': datetime.now().isoformat()
    })


@app.route('/readyz')
def ready():
    """Readiness probe — can we serve analysis (any data source)?"""
    price = get_live_price_hybrid('nifty')
    ok = price is not None
    return jsonify({
        'ready': ok,
        'source': (price or {}).get('source') if price else None,
        'timestamp': datetime.now().isoformat()
    }), (200 if ok else 503)


@app.route('/api/status')
def status():
    ml_stats = get_ml_stats()
    breeze = safe_status().get('breeze', {})
    return jsonify({
        'angel_one_connected': bool(ANGEL_AVAILABLE and angel_one_enhanced.is_logged_in),
        'angel_one_client': angel_one_enhanced.client_code if ANGEL_AVAILABLE and angel_one_enhanced.is_logged_in else None,
        'breeze_connected': bool(BREEZE_AVAILABLE and breeze_manager.is_connected()),
        'breeze_configured': breeze.get('fully_configured', False),
        'market_open': is_market_open(),
        'yahoo_available': YAHOO_AVAILABLE,
        'ml_available': ML_AVAILABLE and STABLE_ML_AVAILABLE,
        'ml_trained': ml_stats.get('is_trained', False),
        'ml_accuracy': ml_stats.get('training_accuracy', {}),
        'timestamp': datetime.now().isoformat()
    })


# ---------------------------------------------------------------------------
# Routes — market data
# ---------------------------------------------------------------------------

@app.route('/api/analysis')
def analysis():
    index = request.args.get('index', 'nifty')
    data = get_market_analysis(index)
    return jsonify(data), (503 if 'error' in data else 200)


@app.route('/api/strategies')
def strategies_route():
    """Classic + pro strategies only (lightweight)."""
    index = request.args.get('index', 'nifty')
    data = get_market_analysis(index)
    if 'error' in data:
        return jsonify(data), 503
    classic = [s for s in data['strategies'] if s.get('category') != 'pro']
    pro = [s for s in data['strategies'] if s.get('category') == 'pro']
    return jsonify({
        'index': index,
        'classic': classic,
        'pro': pro,
        'pro_verdict': data.get('pro_verdict'),
        'prediction': data.get('prediction'),
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/pro-strategies')
def pro_strategies_route():
    """Pro strategies + confluence verdict only."""
    index = request.args.get('index', 'nifty')
    data = get_market_analysis(index)
    if 'error' in data:
        return jsonify(data), 503
    pro = [s for s in data['strategies'] if s.get('category') == 'pro']
    return jsonify({
        'index': index,
        'strategies': pro,
        'count': len(pro),
        'pro_verdict': data.get('pro_verdict'),
        'pro_analysis': data.get('pro_analysis'),
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/candles')
def candles():
    index = request.args.get('index', 'nifty')
    tf = request.args.get('tf', request.args.get('interval', '5m'))
    data = get_candles_hybrid(index, tf, 5)
    if not data:
        return jsonify({'error': 'NO_DATA'}), 503
    return jsonify({'candles': data})


@app.route('/api/chart-data')
def chart_data():
    """Alias for /api/candles (frontend compat)."""
    return candles()


@app.route('/api/option-chain')
def option_chain():
    index = request.args.get('index', 'nifty')
    oc = get_option_chain_hybrid(index)
    if not oc:
        return jsonify({'error': 'NO_OPTION_CHAIN',
                        'message': 'Failed to fetch option chain from all sources'}), 503
    return jsonify(oc)


@app.route('/api/vix')
def vix():
    vix_data = get_vix_hybrid()
    if not vix_data:
        return jsonify({'error': 'NO_VIX_DATA'}), 503
    return jsonify(vix_data)


@app.route('/api/market-sentiment')
def market_sentiment():
    index = request.args.get('index', 'nifty')
    data = get_market_analysis(index)
    if 'error' in data:
        return jsonify(data), 503
    return jsonify(data.get('sentiment', {}))


@app.route('/api/trade-estimate')
def trade_estimate():
    index = request.args.get('index', 'nifty')
    data = get_market_analysis(index)
    if 'error' in data:
        return jsonify(data), 503
    return jsonify(data.get('trade_recommendation', {}))


@app.route('/api/pro-prediction')
def pro_prediction():
    """Pro-level prediction with option recommendations."""
    index = request.args.get('index', 'nifty')
    data = get_market_analysis(index)
    if 'error' in data:
        return jsonify(data), 503
    return jsonify({
        'index': index,
        'forward_prediction': data.get('forward_prediction'),
        'option_recommendation': data.get('option_recommendation'),
        'backtest': data.get('backtest'),
        'trade_recommendation': data.get('trade_recommendation'),
        'pro_verdict': data.get('pro_verdict'),
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/ml-stats')
def ml_stats():
    return jsonify(get_ml_stats())


@app.route('/api/backtest')
def backtest():
    index = request.args.get('index', 'nifty')
    try:
        days = max(1, min(60, int(request.args.get('days', 30))))
    except ValueError:
        days = 30
    candles = get_candles_hybrid(index, '5m', days)
    if not candles or len(candles) < 20:
        return jsonify({'error': 'INSUFFICIENT_DATA',
                        'message': 'Need at least 20 candles for backtest'}), 503
    if not PRO_TRADER_AVAILABLE:
        return jsonify({'error': 'BACKTEST_UNAVAILABLE',
                        'message': 'Pro trader module unavailable (scipy not installed)'}), 503
    result = pro_trader.backtest_strategy(candles, 'momentum')
    return jsonify({
        'index': index,
        'backtest': result,
        'candles_used': len(candles),
        'data_source': 'breeze' if (BREEZE_AVAILABLE and breeze_manager.is_connected()) else 'yahoo',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/train-ml')
def train_ml():
    """Trigger ML model retraining."""
    index = request.args.get('index', 'nifty')
    try:
        candles = get_candles_hybrid(index, '5m', 10)
        if not candles or len(candles) < 20:
            return jsonify({'success': False, 'message': 'Insufficient data for training'})
        result_stable = train_stable_model(candles)
        result_legacy = train_ml_model(candles)
        return jsonify({
            'success': True,
            'index': index,
            'stable_ml': result_stable,
            'legacy_ml': result_legacy,
            'candles_used': len(candles),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------------------------------------------------------------------
# Routes — Breeze auth (secrets stay server-side)
# ---------------------------------------------------------------------------

@app.route('/api/breeze-login-url')
def breeze_login_url_route():
    url = breeze_login_url()
    if not url:
        return jsonify({
            'error': 'BREEZE_NOT_CONFIGURED',
            'message': 'Set BREEZE_API_KEY secret first. See SECURITY.md.'
        }), 503
    return jsonify({'url': url})


@app.route('/api/breeze-auth', methods=['POST'])
def breeze_auth():
    payload = request.get_json(silent=True) or {}
    token = (payload.get('token') or '').strip()
    if not token:
        return jsonify({'success': False, 'message': 'Missing session token'}), 400
    if not BREEZE_AVAILABLE:
        return jsonify({'success': False, 'message': 'Breeze SDK not installed'}), 503
    if breeze_manager.set_session_token(token):
        return jsonify({'success': True})
    login = breeze_login_url()
    return jsonify({
        'success': False,
        'message': 'Breeze auth failed — token may be expired. Mint a fresh one.',
        'login_url': login,
        'code': 'BREEZE_AUTH_EXPIRED'
    }), 401


# ---------------------------------------------------------------------------
# Routes — stocks & movers
# ---------------------------------------------------------------------------

@app.route('/api/top-stocks/short-term')
def top_stocks_short_term():
    if not STOCKS_AVAILABLE:
        return jsonify({'error': 'STOCKS_UNAVAILABLE'}), 503
    count = min(20, max(1, int(request.args.get('count', 10))))
    picks = get_short_term_picks(count)
    return jsonify({
        'picks': picks,
        'count': len(picks),
        'type': 'short_term',
        'description': 'Top stocks for 15-min intraday trades based on momentum and technical indicators',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/top-stocks/long-term')
def top_stocks_long_term():
    if not STOCKS_AVAILABLE:
        return jsonify({'error': 'STOCKS_UNAVAILABLE'}), 503
    count = min(20, max(1, int(request.args.get('count', 10))))
    picks = get_long_term_picks(count)
    return jsonify({
        'picks': picks,
        'count': len(picks),
        'type': 'long_term',
        'description': 'Top stocks for investment based on trend and technical strength',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/all-stocks')
def all_stocks_analysis():
    if not STOCKS_AVAILABLE:
        return jsonify({'error': 'STOCKS_UNAVAILABLE'}), 503
    stocks = get_all_analysis()
    overview = get_market_overview()
    return jsonify({
        'stocks': stocks,
        'count': len(stocks),
        'market_overview': overview,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/market-movers')
def market_movers():
    return jsonify(get_market_movers())


@app.route('/api/stock-overview')
def stock_overview():
    if not STOCKS_AVAILABLE:
        return jsonify({'error': 'STOCKS_UNAVAILABLE'}), 503
    return jsonify(get_market_overview())


# ---------------------------------------------------------------------------
# Routes — trade history & analytics
# ---------------------------------------------------------------------------

@app.route('/api/trade-history')
def trade_history():
    """Last N hours of trade signals with outcomes."""
    from datetime import timedelta
    try:
        hours = max(1, min(72, int(request.args.get('hours', 4))))
        limit = max(1, min(100, int(request.args.get('limit', 30))))
    except ValueError:
        hours, limit = 4, 30
    cutoff = datetime.now() - timedelta(hours=hours)

    window_preds = []
    for p in accuracy_tracker.predictions:
        try:
            if datetime.fromisoformat(p['timestamp']) >= cutoff:
                window_preds.append(p)
        except (KeyError, ValueError):
            continue
    window_preds = sorted(window_preds, key=lambda x: x['timestamp'], reverse=True)[:limit]

    rows = [{
        'id': p['id'],
        'time': p['timestamp'],
        'direction': p['direction'],
        'signal': p.get('signal', 'N/A'),
        'confidence': p.get('confidence', 0),
        'entry_price': p.get('entry_price', 0),
        'exit_price': p.get('exit_price'),
        'percent_change': p.get('percent_change'),
        'result': p.get('result', 'PENDING'),
        'validated': p.get('validated', False),
    } for p in window_preds]

    return jsonify({
        'trades': rows,
        'total_in_window': len(rows),
        'hours': hours,
        'stats': accuracy_tracker.get_accuracy_stats(),
        'streak': accuracy_tracker.get_streak(),
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/recent-trades')
def recent_trades():
    """Trade signals from the last few hours with real outcomes and win rate."""
    index = request.args.get('index', 'nifty')
    try:
        hours = max(1, min(24, int(request.args.get('hours', 5))))
    except ValueError:
        hours = 5
    candles = get_candles_hybrid(index, '5m', 1)
    if not candles or len(candles) < 10:
        return jsonify({'error': 'INSUFFICIENT_DATA'}), 503
    return jsonify(analyze_recent_trades(candles, index, hours))


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(_e):
    return jsonify({'error': 'NOT_FOUND', 'message': 'Unknown endpoint'}), 404


@app.errorhandler(500)
def server_error(_e):
    return jsonify({'error': 'SERVER_ERROR', 'message': 'Unexpected error — check logs'}), 500


# ---------------------------------------------------------------------------
# Background price broadcaster (started once, lazily)
# ---------------------------------------------------------------------------

def background_update():
    while is_running:
        try:
            nifty = get_live_price_hybrid('nifty')
            banknifty = get_live_price_hybrid('banknifty')
            if nifty or banknifty:
                if nifty and isinstance(nifty, dict):
                    validate_past_predictions(nifty.get('ltp', 0))
                socketio.emit('price_update', {'nifty': nifty, 'banknifty': banknifty})
            else:
                socketio.emit('price_update', {'error': 'NO_DATA'})
        except Exception as e:
            print(f"[WARN] Background update error: {e}")
        time.sleep(2)


def ensure_background_started():
    global _bg_started
    with _bg_lock:
        if not _bg_started:
            _bg_started = True
            socketio.start_background_task(background_update)


@socketio.on('connect')
def on_connect():
    ensure_background_started()


@socketio.on('subscribe')
def on_subscribe(_data=None):
    ensure_background_started()


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  NIFTY PREDICTOR PRO - Python ML Trading System")
    print(f"  Dashboard: http://127.0.0.1:{PORT}")
    print(f"  Health:    http://127.0.0.1:{PORT}/healthz")
    print(f"  Env:       {'production' if IS_PROD else 'development'}")
    print("=" * 60 + "\n")
    ensure_background_started()
    socketio.run(app, debug=False, host='0.0.0.0', port=PORT, allow_unsafe_werkzeug=True)
