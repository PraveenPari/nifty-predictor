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
# DEMO_MODE=1 serves realistic simulated data (for previews/demos where
# broker APIs are unreachable). NEVER enable in production trading use.
DEMO_MODE = os.getenv("DEMO_MODE", "0") == "1"

# Circuit breaker: skip a dead source for N seconds after consecutive failures
# so one hanging provider can't stall every request.
_BREAKER_FAILS = {}
_BREAKER_UNTIL = {}
_BREAKER_THRESHOLD = 2
_BREAKER_COOLDOWN = 45  # seconds


def _breaker_skip(key: str) -> bool:
    return time.time() < _BREAKER_UNTIL.get(key, 0)


def _breaker_ok(key: str):
    _BREAKER_FAILS.pop(key, None)
    _BREAKER_UNTIL.pop(key, None)


def _breaker_fail(key: str):
    n = _BREAKER_FAILS.get(key, 0) + 1
    _BREAKER_FAILS[key] = n
    if n >= _BREAKER_THRESHOLD:
        _BREAKER_UNTIL[key] = time.time() + _BREAKER_COOLDOWN
        print(f"[BREAKER] '{key}' failing — skipping for {_BREAKER_COOLDOWN}s")

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
try:
    from trade_setup_engine import (  # noqa: E402
        compute_trendlines, build_projection, grade_setup, build_checklist,
        position_sizer, ta_consensus, atr as engine_atr, TA_AVAILABLE,
    )
    SETUP_ENGINE_AVAILABLE = True
except Exception as e:  # pragma: no cover
    print(f"[WARN] trade_setup_engine unavailable: {e}")
    SETUP_ENGINE_AVAILABLE = False
    TA_AVAILABLE = False
from secrets_manager import breeze_login_url, safe_status  # noqa: E402

# Optional: market simulator (powers DEMO_MODE)
try:
    from data_simulator import get_simulator  # noqa: E402
    SIM_AVAILABLE = True
except Exception as e:
    SIM_AVAILABLE = False
    print(f"[BOOT] simulator disabled: {e}")
    get_simulator = None

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


def _demo_price(index: str):
    sim = get_simulator(index)
    d = sim.update_tick()
    d['source'] = 'Demo Simulator'
    return d


def _demo_candles(index: str, count: int = 100):
    sim = get_simulator(index)
    sim.update_tick()
    return sim.get_candles('5m', count)


def _demo_option_chain(index: str):
    sim = get_simulator(index)
    px = sim.get_current_price()['ltp']
    return {
        'underlying': px,
        'expiry': 'DEMO',
        'chain': sim.get_option_chain(),
        'source': 'Demo Simulator',
    }


def _demo_vix():
    s = get_simulator('nifty').get_market_sentiment()
    return {'ltp': s['vix'], 'change': s.get('vix_change', 0), 'source': 'Demo Simulator'}


def _demo_sentiment_extra():
    return get_simulator('nifty').get_market_sentiment()


def get_live_price_hybrid(index: str):
    """Live price: Breeze -> Angel One -> Yahoo (or Demo Simulator in DEMO_MODE)."""
    index = _norm_index(index)
    if DEMO_MODE and SIM_AVAILABLE:
        try:
            return _demo_price(index)
        except Exception as e:
            print(f"[DEMO] price failed: {e}")
    if BREEZE_AVAILABLE and breeze_manager.is_connected():
        data = breeze_manager.get_live_price(index)
        if data:
            return data
    if ANGEL_AVAILABLE and angel_one_enhanced.is_logged_in:
        data = angel_one_enhanced.get_ltp(index)
        if data:
            return data
    if YAHOO_AVAILABLE and not _breaker_skip('yahoo_price'):
        data = yahoo_manager.get_live_price(index)
        if data:
            _breaker_ok('yahoo_price')
            return data
        _breaker_fail('yahoo_price')
    return None


def get_candles_hybrid(index: str, tf: str = '5m', days: int = 5):
    """Candles: Breeze -> Angel One -> Yahoo (or Demo Simulator in DEMO_MODE)."""
    index = _norm_index(index)
    if DEMO_MODE and SIM_AVAILABLE:
        try:
            return _demo_candles(index)
        except Exception as e:
            print(f"[DEMO] candles failed: {e}")
    candles = None
    if BREEZE_AVAILABLE and breeze_manager.is_connected():
        candles = breeze_manager.get_historical_data(index, _BREEZE_TF.get(tf, '5minute'), days)
    if (not candles or len(candles) < 5) and ANGEL_AVAILABLE and angel_one_enhanced.is_logged_in:
        tf_map = {'5m': 'FIVE_MINUTE', '15m': 'FIFTEEN_MINUTE', '1h': 'ONE_HOUR', '1d': 'ONE_DAY'}
        candles = angel_one_enhanced.get_candles(index, tf_map.get(tf, 'FIVE_MINUTE'), days=days)
    if (not candles or len(candles) < 5) and YAHOO_AVAILABLE and not _breaker_skip('yahoo_candles'):
        candles = yahoo_manager.get_candles(index, tf, _YAHOO_PERIOD.get(tf, '5d'))
        if candles and len(candles) >= 5:
            _breaker_ok('yahoo_candles')
        else:
            _breaker_fail('yahoo_candles')
    return candles or []


def get_option_chain_hybrid(index: str):
    """Option chain with real premiums: Breeze -> Angel One -> MoneyControl -> Yahoo."""
    index = _norm_index(index)

    def has_valid_premiums(oc):
        if not oc or not oc.get('chain'):
            return False
        return any(r.get('ce_ltp', 0) > 0 or r.get('pe_ltp', 0) > 0 for r in oc['chain'])

    if DEMO_MODE and SIM_AVAILABLE:
        try:
            return _demo_option_chain(index)
        except Exception as e:
            print(f"[DEMO] option chain failed: {e}")
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
    if DEMO_MODE and SIM_AVAILABLE:
        try:
            return _demo_vix()
        except Exception as e:
            print(f"[DEMO] vix failed: {e}")
    if BREEZE_AVAILABLE and breeze_manager.is_connected():
        vix_data = breeze_manager.get_vix()
        if vix_data and vix_data.get('ltp'):
            return vix_data
    if YAHOO_AVAILABLE and not _breaker_skip('yahoo_vix'):
        vix_data = yahoo_manager.get_vix()
        if vix_data and vix_data.get('ltp'):
            _breaker_ok('yahoo_vix')
            return vix_data
        _breaker_fail('yahoo_vix')
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

        if DEMO_MODE and SIM_AVAILABLE:
            fii_dii_data = _demo_sentiment_extra()
        else:
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
            'demo_mode': DEMO_MODE,
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
        'breeze_key_ready': breeze.get('login_url_ready', False),
        'market_open': is_market_open(),
        'demo_mode': DEMO_MODE,
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
        return jsonify({'success': True,
                        'warning': getattr(breeze_manager, 'last_error', '') or None,
                        'probe': getattr(breeze_manager, 'last_probe', None)})
    login = breeze_login_url()
    return jsonify({
        'success': False,
        'message': getattr(breeze_manager, 'last_error', '') or 'Breeze auth failed — token may be expired. Mint a fresh one.',
        'login_url': login,
        'code': 'BREEZE_AUTH_EXPIRED'
    }), 401


# ---------------------------------------------------------------------------
# Routes — stocks & movers
# ---------------------------------------------------------------------------

@app.route('/api/top-stocks/short-term')
def top_stocks_short_term():
    if DEMO_MODE:
        return jsonify({'picks': [], 'count': 0, 'type': 'short_term',
                        'demo_mode': True, 'message': 'Stock picks disabled in demo mode',
                        'timestamp': datetime.now().isoformat()})
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
    if DEMO_MODE:
        return jsonify({'picks': [], 'count': 0, 'type': 'long_term',
                        'demo_mode': True, 'message': 'Stock picks disabled in demo mode',
                        'timestamp': datetime.now().isoformat()})
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
    if DEMO_MODE:
        return jsonify({'gainers': [], 'losers': [], 'demo_mode': True,
                        'message': 'Market movers disabled in demo mode',
                        'timestamp': datetime.now().isoformat()})
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
# Routes — elite engine: forensics, intel, live setup
# ---------------------------------------------------------------------------

def _locate_entry_candle(candles, trade_time, candle_idx):
    """Find entry bar: match trade timestamp first, fall back to stored index."""
    if trade_time:
        t = str(trade_time).strip()
        if t:
            for i, c in enumerate(candles):
                for k in ('time', 'datetime', 'timestamp'):
                    v = c.get(k)
                    if v is None:
                        continue
                    s = str(v)
                    if s == t or t in s or s in t:
                        return i
    try:
        ci = int(candle_idx)
        if 0 <= ci < len(candles):
            return ci
    except (TypeError, ValueError):
        pass
    return len(candles) - 1


def _tl_window_payload(tl, window_start):
    """Trendline → window-relative payload the chart can draw directly."""
    return {
        'name': tl['name'], 'color': tl['color'], 'width': tl['width'],
        'slope_pct': tl['slope_pct'], 'touch_count': tl['touch_count'],
        'broken': tl['broken'], 'current_value': tl['current_value'],
        'anchor_bar': tl['anchor_bar'] - window_start,
        'anchor_value': tl['anchor_value'],
        'slope_per_bar': tl['slope_per_bar'],
    }


def _outcome_lesson(result, direction, first_target_hit, first_sl_hit, rr):
    if result == 'WIN':
        if first_target_hit is not None and (first_sl_hit is None or first_target_hit < first_sl_hit):
            return ('A', 'Textbook execution — target hit before any heat. '
                    'This is the setup to repeat and size up on.')
        return ('B', 'Profitable, but price tested the stop zone first. '
                'Edge intact — consider a trigger candle before entry next time.')
    if result == 'FLAT':
        return ('C', 'Chop — neither side paid. Capital preserved; '
                'in range regimes, wait for the range edge, not the middle.')
    if result == 'ACTIVE':
        return ('—', 'Trade still live — manage per plan, do not move the stop.')
    # LOSS
    if first_sl_hit is not None and (first_target_hit is None or first_sl_hit < first_target_hit):
        return ('D', 'Invalidation hit first — the stop did its job. '
                'Review: was the trigger an A-setup? One loss means nothing; the process is everything.')
    return ('D', 'Loss recorded. Re-check: thin RR (<1.5) or counter-trend entries '
            'are the two killers — the elite checklist now blocks both.')


@app.route('/api/trade-forensics')
def trade_forensics():
    """
    Full replay of one past trade: candle window, trade-time trendlines,
    entry/target/SL/exit markers, the model's projection, and graded outcome.
    """
    if not SETUP_ENGINE_AVAILABLE:
        return jsonify({'error': 'ENGINE_UNAVAILABLE'}), 503
    index = request.args.get('index', 'nifty')
    candles = get_candles_hybrid(index, '5m', 1)
    if not candles or len(candles) < 20:
        return jsonify({'error': 'INSUFFICIENT_DATA'}), 503
    try:
        entry = float(request.args.get('entry', 0))
        stop_loss = float(request.args.get('stop_loss', 0))
        target = float(request.args.get('target', 0))
        exit_px = float(request.args.get('exit', 0) or 0)
        points = float(request.args.get('points', 0) or 0)
        pnl = float(request.args.get('pnl', request.args.get('pnl_per_lot', 0) or 0) or 0)
    except ValueError:
        return jsonify({'error': 'BAD_LEVELS'}), 400
    if entry <= 0:
        return jsonify({'error': 'BAD_LEVELS'}), 400
    direction = (request.args.get('direction', 'BULLISH') or 'BULLISH').upper()
    if direction in ('LONG', 'CE', 'CALL'):
        direction = 'BULLISH'
    elif direction in ('SHORT', 'PE', 'PUT'):
        direction = 'BEARISH'
    result = (request.args.get('result', 'ACTIVE') or 'ACTIVE').upper()

    entry_i = _locate_entry_candle(candles, request.args.get('time'), request.args.get('candle_idx'))
    pre = candles[:entry_i + 1]
    trendlines = compute_trendlines(pre, lookback=min(60, len(pre)), extend_bars=14)
    projection = build_projection(pre, direction, entry, stop_loss, target, trendlines)

    # Forward scan: first target / SL touch after entry
    first_target_hit, first_sl_hit = None, None
    for j in range(entry_i + 1, len(candles)):
        try:
            h, l = float(candles[j]['high']), float(candles[j]['low'])
        except (KeyError, ValueError, TypeError):
            continue
        if direction == 'BULLISH':
            if first_target_hit is None and target and h >= target:
                first_target_hit = j
            if first_sl_hit is None and stop_loss and l <= stop_loss:
                first_sl_hit = j
        else:
            if first_target_hit is None and target and l <= target:
                first_target_hit = j
            if first_sl_hit is None and stop_loss and h >= stop_loss:
                first_sl_hit = j
        if first_target_hit is not None and first_sl_hit is not None:
            break

    start = max(0, entry_i - 90)
    window = candles[start:start + 200]
    rel = lambda j: (j - start) if j is not None else None  # noqa: E731

    bull = direction == 'BULLISH'
    markers = [{
        'bar': rel(entry_i), 'position': 'belowBar' if bull else 'aboveBar',
        'color': '#f59e0b', 'shape': 'arrowUp' if bull else 'arrowDown',
        'text': f"ENTRY {entry:.1f}",
    }]
    end_j = len(window) - 1 + start
    exit_j = first_target_hit if result == 'WIN' and first_target_hit is not None else \
        (first_sl_hit if result == 'LOSS' and first_sl_hit is not None else end_j)
    exit_color = {'WIN': '#10b981', 'LOSS': '#ef4444'}.get(result, '#3b82f6')
    markers.append({
        'bar': rel(min(exit_j, start + len(window) - 1)),
        'position': 'aboveBar' if bull else 'belowBar',
        'color': exit_color, 'shape': 'circle',
        'text': f"{result} {exit_px:.1f}" if exit_px else result,
    })

    grade, lesson = _outcome_lesson(result, direction, first_target_hit, first_sl_hit,
                                    projection.get('risk_reward', 0))

    return jsonify({
        'index': index, 'direction': direction, 'result': result,
        'entry': entry, 'stop_loss': stop_loss, 'target': target,
        'exit': exit_px, 'points': points, 'pnl_per_lot': pnl,
        'entry_bar': rel(entry_i),
        'candles': window,
        'markers': markers,
        'trendlines': [_tl_window_payload(t, start) for t in trendlines],
        'projection': projection,
        'outcome': {
            'grade': grade, 'lesson': lesson,
            'target_hit_first': first_target_hit is not None and (
                first_sl_hit is None or first_target_hit < first_sl_hit),
            'bars_to_target': (first_target_hit - entry_i) if first_target_hit else None,
            'bars_to_stop': (first_sl_hit - entry_i) if first_sl_hit else None,
        },
        'timestamp': datetime.now().isoformat(),
    })


@app.route('/api/market-intel')
def market_intel():
    """
    Free-source market intelligence: MoneyControl movers + summary, FII/DII,
    advance/decline breadth. Never 500s — degrades gracefully to demo/cached.
    """
    intel = {
        'gainers': [], 'losers': [], 'summary': {}, 'breadth': {},
        'fii_dii': {}, 'sources': [], 'demo': DEMO_MODE,
        'timestamp': datetime.now().isoformat(), 'note': '',
    }
    if DEMO_MODE and SIM_AVAILABLE:
        try:
            sim = get_simulator('nifty')
            sent = sim.get_market_sentiment()
            px = sim.get_current_price()['ltp']
            # Deterministic demo breadth board (clearly labelled demo)
            board = ['RELIANCE', 'HDFCBANK', 'INFY', 'ICICIBANK', 'TCS', 'SBIN',
                     'TATAMOTORS', 'AXISBANK', 'KOTAKBANK', 'LT']
            movers = []
            for i, sym in enumerate(board):
                drift = ((px * (i + 3) * 7919) % 1000) / 1000  # 0..1 deterministic
                chg = round((drift - 0.45) * 6, 2)
                movers.append({'symbol': sym, 'ltp': round(px * (0.02 + i * 0.011), 2),
                               'change_pct': chg, 'volume': int(1e6 + drift * 9e6)})
            movers.sort(key=lambda m: m['change_pct'], reverse=True)
            intel['gainers'] = movers[:5]
            intel['losers'] = list(reversed(movers[-5:]))
            intel['breadth'] = {'advances': sent.get('advances', 0),
                                'declines': sent.get('declines', 0),
                                'undecided': sent.get('undecided', 0)}
            intel['fii_dii'] = {'fii_net': sent.get('fii_net', 0),
                                'dii_net': sent.get('dii_net', 0)}
            intel['sources'] = ['Demo Simulator']
            intel['note'] = 'Demo feed — connect live data for real MoneyControl intel.'
            return jsonify(intel)
        except Exception as e:
            intel['note'] = f'Demo intel unavailable: {e}'
            return jsonify(intel)

    # Live: MoneyControl with a hard time budget so the request can't hang
    if MC_AVAILABLE:
        try:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=1) as pool:
                fut = pool.submit(get_market_movers)
                mc = fut.result(timeout=14)
            if isinstance(mc, dict):
                intel['gainers'] = mc.get('gainers', []) or []
                intel['losers'] = mc.get('losers', []) or []
                if intel['gainers'] or intel['losers']:
                    intel['sources'].append('MoneyControl')
        except Exception as e:
            intel['note'] = f'MoneyControl unreachable ({e}); showing alternate sources. '
    try:
        if YAHOO_AVAILABLE:
            fii = yahoo_manager.get_fii_dii()
            if fii:
                intel['fii_dii'] = fii
                intel['sources'].append('Yahoo/FII-DII')
    except Exception:
        pass
    if not intel['sources']:
        intel['note'] += 'All free intel sources unreachable right now — retry shortly.'
    return jsonify(intel)


@app.route('/api/live-trade-setup')
def live_trade_setup():
    """
    Buffett-grade live setup: elite checklist, A+/A/B/C grade, projection cone,
    trendlines + position sizing for the current market state.
    """
    if not SETUP_ENGINE_AVAILABLE:
        return jsonify({'error': 'ENGINE_UNAVAILABLE'}), 503
    index = _norm_index(request.args.get('index', 'nifty'))
    try:
        capital = max(10000, min(100000000, float(request.args.get('capital', 200000))))
    except ValueError:
        capital = 200000

    data = get_market_analysis(index)
    if 'error' in data:
        return jsonify(data), 503
    candles = get_candles_hybrid(index, '5m', 5)
    if not candles or len(candles) < 30:
        return jsonify({'error': 'INSUFFICIENT_DATA'}), 503

    rec = data.get('trade_recommendation', {})
    ind = data.get('indicators', {}) or {}
    sent = data.get('sentiment', {}) or {}
    pred = data.get('prediction', {}) or {}
    price = float(rec.get('entry') or (data.get('price_data') or {}).get('ltp') or candles[-1]['close'])

    direction = (rec.get('direction') or pred.get('direction') or 'NEUTRAL').upper()
    if direction not in ('BULLISH', 'BEARISH'):
        direction = 'BULLISH' if pred.get('ce_prob', 50) >= pred.get('pe_prob', 50) else 'BEARISH'
    entry = float(rec.get('entry') or price)
    stop_loss = float(rec.get('stop_loss') or price * 0.995)
    target = float(rec.get('target') or price * 1.015)
    rr = float(rec.get('risk_reward') or 0)

    adx = ind.get('adx') or {}
    adx_v = adx.get('adx', 0) or 0
    regime = 'TRENDING' if adx_v >= 25 else ('TRANSITION' if adx_v >= 18 else 'RANGE')
    piv = ind.get('pivot_points') or {}
    supports = [piv[k] for k in ('s1', 's2', 's3') if piv.get(k)]
    resistances = [piv[k] for k in ('r1', 'r2', 'r3') if piv.get(k)]

    trendlines = compute_trendlines(candles[-120:], lookback=60, extend_bars=14)
    start = len(candles) - min(120, len(candles))
    tav = ta_consensus(candles)
    checklist = build_checklist(direction, price, ind, sent, regime, supports, resistances)
    if not rr:
        risk = abs(entry - stop_loss) or 1
        rr = round(abs(target - entry) / risk, 2)
    grade = grade_setup(checklist, rr, tav)
    projection = build_projection(candles, direction, entry, stop_loss, target, trendlines)

    risk_map = {'A+': 2.0, 'A': 1.0, 'B': 0.5, 'C': 0.0}
    sizing = position_sizer(capital, risk_map.get(grade['grade'], 0.5),
                            entry, stop_loss, LOT_SIZES.get(index, 25))

    return jsonify({
        'index': index, 'price': round(price, 2), 'direction': direction,
        'confidence': rec.get('confidence', pred.get('confidence', 50)),
        'regime': regime, 'adx': round(adx_v, 1),
        'levels': {'entry': round(entry, 2), 'stop_loss': round(stop_loss, 2),
                   'target': round(target, 2), 'risk_reward': rr,
                   'supports': supports, 'resistances': resistances},
        'grade': grade,
        'projection': projection,
        'sizing': sizing,
        'ta_consensus': tav,
        'trendlines': [_tl_window_payload(t, 0) for t in trendlines],
        'candles': candles[start:],
        'timestamp': datetime.now().isoformat(),
    })


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
