from trade_analytics import analyze_recent_trades
"""
Nifty Predictor Pro - Python Flask Server
Professional ML Trading System with Breeze API + Yahoo Finance Hybrid
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading
import time
from datetime import datetime
import os
import json

print("Importing config...")
from pro_config.trading_config import INDEX_CONFIG, MARKET_OPEN, MARKET_CLOSE, SIGNAL_CONFIG
print("Importing indicators...")
from indicators_fast import TechnicalIndicatorsFast as TechnicalIndicators
print("Importing strategies...")
from strategies import TradingStrategies
print("Importing ml_predictor...")
from ml_predictor import get_ml_prediction, train_ml_model, get_model_stats
print("Importing stable_ml_predictor...")
from stable_ml_predictor import get_stable_prediction, train_stable_model, get_ml_stats, validate_past_predictions
print("Importing angel_one...")
from angel_one_enhanced import angel_one_enhanced
print("Importing breeze_manager...")
from breeze_manager import breeze_manager
print("Importing yahoo_manager...")
from yahoo_manager import yahoo_manager
print("Importing feature_engineer...")
from feature_engineer import feature_engineer
print("Importing ensemble_model...")
from models.ensemble import ensemble_model
print("Importing pro_trader...")
from pro_trader import pro_trader, LOT_SIZES
print("Importing stock_analyzer...")
from stock_analyzer import get_short_term_picks, get_long_term_picks, get_all_analysis, get_market_overview
from stock_analyzer import get_short_term_picks, get_long_term_picks, get_all_analysis, get_market_overview
print("Importing moneycontrol_scraper...")
from moneycontrol_scraper import get_market_movers, get_option_chain as get_mc_option_chain
from accuracy_tracker import accuracy_tracker, get_recent_results

from flask.json.provider import DefaultJSONProvider
import numpy as np

# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'nifty-predictor-secret-2024'

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
CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global state
is_running = True

def is_market_open():
    now = datetime.now()
    if now.weekday() >= 5: return False
    time_min = now.hour * 60 + now.minute
    start = MARKET_OPEN['hour'] * 60 + MARKET_OPEN['minute']
    end = MARKET_CLOSE['hour'] * 60 + MARKET_CLOSE['minute']
    return start <= time_min <= end


def get_option_chain_hybrid(index: str):
    """Get option chain - Angel One -> Breeze -> Yahoo
    
    Note: For option PICK feature, we need actual premium prices (ce_ltp, pe_ltp).
    Angel One skeleton data has OI but no premiums, so we validate and fallback to Yahoo.
    """
    
    def has_valid_premiums(oc):
        """Check if option chain has non-zero premium values"""
        if not oc or not oc.get('chain'):
            return False
        # Check if at least some options have non-zero premiums
        for row in oc['chain']:
            if row.get('ce_ltp', 0) > 0 or row.get('pe_ltp', 0) > 0:
                return True
        return False
    
    # 1. Breeze (Primary & Authenticated Live Broker)
    if breeze_manager.is_connected():
        oc = breeze_manager.get_option_chain(index)
        if oc and oc.get('chain') and has_valid_premiums(oc):
            return oc

    # 2. Angel One (Secondary)
    if angel_one_enhanced.is_logged_in:
        oc = angel_one_enhanced.get_option_chain(index)
        if oc and oc.get('chain') and has_valid_premiums(oc):
            return oc
    
    # 3. MoneyControl Scraper (New Reliable Fallback for Premiums)
    print(f"[INFO] Using MoneyControl Scraper for Option Chain for {index}...")
    oc_mc = get_mc_option_chain(index)
    if oc_mc and oc_mc.get('chain') and has_valid_premiums(oc_mc):
        print(f"[SUCCESS] Option Chain with premiums from MoneyControl for {index}")
        return oc_mc

    # 4. Yahoo Finance (Fallback)
    # print(f"[INFO] Using Yahoo Finance for Option Chain for {index} (has premium data)")
    oc_yahoo = yahoo_manager.get_option_chain(index)
    if oc_yahoo and oc_yahoo.get('chain'):
        print(f"[SUCCESS] Option Chain with premiums from Yahoo for {index}")
        return oc_yahoo
    
    # Last resort: return Angel One skeleton data if available (at least has OI)
    if angel_one_enhanced.is_logged_in:
        oc = angel_one_enhanced.get_option_chain(index)
        if oc:
            print(f"[WARNING] Returning Angel One skeleton data (no premiums) for {index}")
            return oc
    
    print(f"[ERROR] Failed to get option chain from all sources for {index}")
    return None


def get_vix_hybrid():
    """Get VIX - try Breeze first, fallback to Yahoo"""
    vix_data = breeze_manager.get_vix()
    if vix_data and vix_data.get('ltp'):
        return vix_data
    
    # Fallback to Yahoo
    return yahoo_manager.get_vix()


def get_market_analysis(index='nifty'):
    """Get complete market analysis with hybrid data sources"""
    
    # Get live price - Try Yahoo first (most reliable), then Angel One, then Breeze
    price_data = None
    
    # Try Breeze first (fastest and real-time if connected)
    if breeze_manager.is_connected():
        price_data = breeze_manager.get_live_price(index)
        
    # Try Angel One if Breeze failed
    if not price_data and angel_one_enhanced.is_logged_in:
        price_data = angel_one_enhanced.get_ltp(index)
        
    # Try Yahoo as last fallback
    if not price_data:
        price_data = yahoo_manager.get_live_price(index)
    
    if not price_data:
        return {
            'error': 'NO_DATA',
            'message': 'Failed to fetch live price from all sources.',
            'index': index,
            'timestamp': datetime.now().isoformat()
        }

    try:
        # Get candles - Yahoo primary (most reliable), Angel One secondary, Breeze tertiary
        candles = None
        
        # Try Breeze first
        if breeze_manager.is_connected():
            candles = breeze_manager.get_historical_data(index, '5minute', 5)
            
        # Try Angel One if Breeze failed
        if (not candles or len(candles) < 5) and angel_one_enhanced.is_logged_in:
            candles = angel_one_enhanced.get_candles(index, 'FIVE_MINUTE', days=5)
            
        # Try Yahoo as last fallback
        if not candles or len(candles) < 5:
            candles = yahoo_manager.get_candles(index, '5m', '5d')
        
        if not candles or len(candles) < 5:
            return {
                'error': 'NO_CANDLE_DATA',
                'message': 'Failed to fetch candle data.',
                'index': index,
                'price_data': price_data,
                'timestamp': datetime.now().isoformat()
            }
    
        # Calculate indicators
        indicators = TechnicalIndicators.calculate_all(candles)
        
        # Get VIX (hybrid)
        vix_data = get_vix_hybrid()
        vix_value = vix_data.get('ltp', 14) if vix_data else 14
        
        # Get Option Chain (hybrid) for sentiment
        oc = get_option_chain_hybrid(index)
        
        # Calculate PCR from option chain
        pcr = 1.0
        total_ce_oi = 0
        total_pe_oi = 0
        if oc and oc.get('chain'):
            for row in oc['chain']:
                total_ce_oi += row.get('ce_oi', 0)
                total_pe_oi += row.get('pe_oi', 0)
            if total_ce_oi > 0:
                pcr = round(total_pe_oi / total_ce_oi, 2)
        
        # Fetch FII/DII data
        fii_dii_data = yahoo_manager.get_fii_dii()
        
        # Build comprehensive sentiment
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
        
        # Determine sentiment from PCR and VIX
        if pcr > 1.2 and vix_value < 18:
            sentiment['overall_sentiment'] = 'BULLISH'
            sentiment['sentiment_score'] = 20
        elif pcr < 0.8 or vix_value > 20:
            sentiment['overall_sentiment'] = 'BEARISH'
            sentiment['sentiment_score'] = -20
            
        # Run strategies
        strategy_result = TradingStrategies.analyze_all(indicators, price_data['ltp'], sentiment, candles)
        strategies = strategy_result.get('strategies', [])
        
        # STABLE ML Prediction (updates every 15 mins, not every second)
        stable_ml_prediction = get_stable_prediction(candles, indicators)
        
        # Legacy ML prediction for comparison
        ml_prediction = get_ml_prediction(candles, indicators)
        
        # Combine predictions - prioritize stable ML
        prediction = TradingStrategies.calculate_prediction(strategies)
        combined_ce_prob = (prediction['ce_prob'] * 0.3 + stable_ml_prediction.get('bullish_prob', 50) * 0.7)
        combined_pe_prob = (prediction['pe_prob'] * 0.3 + stable_ml_prediction.get('bearish_prob', 50) * 0.7)
        
        direction = stable_ml_prediction.get('direction', 'NEUTRAL')
        confidence = stable_ml_prediction.get('confidence', 50)
        
        # Pro Trading Calculations
        ltp = price_data['ltp']
        lot_size = LOT_SIZES.get(index.lower(), 25)
        
        # Calculate entry, stop loss, target
        if direction == 'BULLISH':
            entry = ltp
            stop_loss = round(ltp * 0.995, 2)  # 0.5% SL
            target = round(ltp * 1.015, 2)      # 1.5% target
        else:
            entry = ltp
            stop_loss = round(ltp * 1.005, 2)
            target = round(ltp * 0.985, 2)
        
        # Risk-Reward calculation
        rr = pro_trader.calculate_risk_reward(entry, stop_loss, target)
        
        # Lot sizing based on risk
        # Estimate option premium (rough approximation)
        estimated_premium = abs(ltp - target) * 0.5 + 50  # Rough estimate
        lot_calc = pro_trader.calculate_lot_size(estimated_premium, 30, 5000, lot_size)
        
        # Profit calculation
        points_move = abs(target - entry)
        profit_per_lot = points_move * lot_size
        total_profit = profit_per_lot * lot_calc['suggested_lots']
        
        # Option recommendation from pro trader
        option_chain_data = oc.get('chain', []) if oc else []
        option_rec = pro_trader.calculate_option_recommendation(
            index, ltp, direction, option_chain_data, 30
        )
        
        # 15-min forward prediction
        forward_prediction = pro_trader.predict_direction_15min(candles, indicators, ml_prediction)
        
        # Backtest results
        backtest = pro_trader.backtest_strategy(candles, 'momentum')
        
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
                'suggested_lots': lot_calc['suggested_lots'],
                'risk_reward': rr['ratio'],
                'profit_on_target': round(total_profit, 2),
                'lot_size': lot_size,
                'max_loss': lot_calc['max_loss']
            },
            'option_recommendation': option_rec,
            'forward_prediction': forward_prediction,
            'backtest': backtest,
            'pro_analysis': strategy_result.get('pro_analysis', ""),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"CRITICAL: Analysis error - {e}")
        return {'error': 'ANALYSIS_ERROR', 'message': str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def status():
    ml_stats = get_ml_stats()
    return jsonify({
        'angel_one_connected': angel_one_enhanced.is_logged_in,
        'angel_one_client': angel_one_enhanced.client_code if angel_one_enhanced.is_logged_in else None,
        'breeze_connected': breeze_manager.is_connected(),
        'market_open': is_market_open(),
        'yahoo_available': True,
        'ml_trained': ml_stats.get('is_trained', False),
        'ml_accuracy': ml_stats.get('training_accuracy', {}),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/analysis')
def analysis():
    index = request.args.get('index', 'nifty')
    return jsonify(get_market_analysis(index))

@app.route('/api/candles')
def candles():
    index = request.args.get('index', 'nifty')
    tf = request.args.get('tf', '5m')
    
    data = None
    # Try Breeze first
    if breeze_manager.is_connected():
        interval_map = {'5m': '5minute', '15m': '30minute', '1h': '1day', '1d': '1day'}
        data = breeze_manager.get_historical_data(index, interval_map.get(tf, '5minute'), 5)
        
    # Fallback to Yahoo
    if not data:
        period_map = {'5m': '5d', '15m': '5d', '1h': '1mo', '1d': '3mo'}
        data = yahoo_manager.get_candles(index, tf, period_map.get(tf, '5d'))
    
    if not data: 
        return jsonify({'error': 'NO_DATA'}), 503
    return jsonify({'candles': data})

@app.route('/api/option-chain')
def option_chain():
    index = request.args.get('index', 'nifty')
    
    # Use reliable hybrid fetcher which now has validation
    oc = get_option_chain_hybrid(index)
    
    if not oc: 
        return jsonify({'error': 'NO_OPTION_CHAIN', 'message': 'Failed to fetch option chain from all sources'}), 503
    return jsonify(oc)

@app.route('/api/vix')
def vix():
    vix_data = get_vix_hybrid()
    if not vix_data:
        return jsonify({'error': 'NO_VIX_DATA'}), 503
    return jsonify(vix_data)

@app.route('/api/pro-prediction')
def pro_prediction():
    """Pro-level prediction with option recommendations"""
    index = request.args.get('index', 'nifty')
    analysis_data = get_market_analysis(index)
    
    if 'error' in analysis_data:
        return jsonify(analysis_data), 503
    
    return jsonify({
        'index': index,
        'forward_prediction': analysis_data.get('forward_prediction'),
        'option_recommendation': analysis_data.get('option_recommendation'),
        'backtest': analysis_data.get('backtest'),
        'trade_recommendation': analysis_data.get('trade_recommendation'),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/ml-stats')
def ml_stats():
    """Get ML model statistics and performance"""
    stats = get_ml_stats()
    return jsonify(stats)

@app.route('/api/backtest')
def backtest():
    """Run backtest on historical data - Uses Breeze as primary"""
    index = request.args.get('index', 'nifty')
    days = int(request.args.get('days', 30))
    
    # Get historical data from Breeze (primary) - works for equity data
    candles = None
    if breeze_manager.is_connected():
        candles = breeze_manager.get_historical_data(index, '5minute', days)
    
    # Fallback to Yahoo only if Breeze fails
    if not candles or len(candles) < 20:
        print(f"DEBUG: Breeze historical failed for backtest, trying Yahoo...")
        candles = yahoo_manager.get_candles(index, '5m', f'{days}d')
    
    if not candles or len(candles) < 20:
        return jsonify({'error': 'INSUFFICIENT_DATA', 'message': 'Need at least 20 candles for backtest'}), 503
    
    result = pro_trader.backtest_strategy(candles, 'momentum')
    return jsonify({
        'index': index,
        'backtest': result,
        'candles_used': len(candles),
        'data_source': 'breeze' if breeze_manager.is_connected() else 'yahoo',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/breeze-login-url')
def breeze_login_url():
    return jsonify({'url': breeze_manager.generate_session_token()})

@app.route('/api/breeze-auth', methods=['POST'])
def breeze_auth():
    token = request.json.get('token')
    if breeze_manager.set_session_token(token):
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Auth failed'}), 401

# --- Missing Endpoints Implementation (Matching Frontend) ---

@app.route('/api/chart-data')
def chart_data():
    """Alias for /api/candles to match frontend call"""
    # Frontend calls: index=nifty&interval=5m&period=5d
    return candles()

@app.route('/api/market-sentiment')
def market_sentiment():
    """Get market sentiment (subset of analysis)"""
    index = request.args.get('index', 'nifty')
    analysis_data = get_market_analysis(index)
    if 'error' in analysis_data:
        return jsonify(analysis_data), 503
    return jsonify(analysis_data.get('sentiment', {}))

@app.route('/api/trade-estimate')
def trade_estimate():
    """Get trade estimate/recommendation (subset of analysis)"""
    # Frontend passes: index, direction, entry, target, stop_loss, lots
    # But get_market_analysis calculates optimal ones. 
    # For now, we return the system generated recommendation.
    index = request.args.get('index', 'nifty')
    analysis_data = get_market_analysis(index)
    if 'error' in analysis_data:
        return jsonify(analysis_data), 503
        
    rec = analysis_data.get('trade_recommendation', {})
    
    # If frontend provided overrides, we could recalculate, but for now returning system rec is safer
    return jsonify(rec)

# =============================================
# MULTI-STOCK ANALYSIS ENDPOINTS
# =============================================

@app.route('/api/top-stocks/short-term')
def top_stocks_short_term():
    """Get top 10 stocks for short-term (15-min) trading"""
    count = int(request.args.get('count', 10))
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
    """Get top 10 stocks for long-term investment"""
    count = int(request.args.get('count', 10))
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
    """Get analysis for all NIFTY50 stocks"""
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
    """Get top gainers and losers from MoneyControl"""
    movers = get_market_movers()
    return jsonify(movers)

@app.route('/api/stock-overview')
def stock_overview():
    """Get market overview and sentiment from analyzed stocks"""
    overview = get_market_overview()
    return jsonify(overview)


# =============================================
# TRAIN ML ENDPOINT (was missing)
# =============================================

@app.route('/api/train-ml')
def train_ml():
    """Trigger ML model retraining"""
    index = request.args.get('index', 'nifty')
    try:
        candles = None
        if breeze_manager.is_connected():
            candles = breeze_manager.get_historical_data(index, '5minute', 10)
        if not candles or len(candles) < 20:
            candles = yahoo_manager.get_candles(index, '5m', '10d')
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


# =============================================
# TRADE HISTORY ENDPOINT
# =============================================

@app.route('/api/trade-history')
def trade_history():
    """Last N hours of trade signals with outcomes"""
    from datetime import timedelta
    hours = int(request.args.get('hours', 4))
    limit = int(request.args.get('limit', 30))
    cutoff = datetime.now() - timedelta(hours=hours)

    all_preds = accuracy_tracker.predictions
    window_preds = [
        p for p in all_preds
        if datetime.fromisoformat(p['timestamp']) >= cutoff
    ]
    window_preds = sorted(window_preds, key=lambda x: x['timestamp'], reverse=True)[:limit]

    rows = []
    for p in window_preds:
        rows.append({
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
        })

    stats = accuracy_tracker.get_accuracy_stats()
    streak = accuracy_tracker.get_streak()
    return jsonify({
        'trades': rows,
        'total_in_window': len(rows),
        'hours': hours,
        'stats': stats,
        'streak': streak,
        'timestamp': datetime.now().isoformat()
    })




# =============================================
# RECENT TRADES ANALYTICS (Last Few Hours + Success Rate)
# =============================================

@app.route('/api/recent-trades')
def recent_trades():
    """Get trade signals from the last few hours with real outcomes and win rate"""
    index = request.args.get('index', 'nifty')
    hours = int(request.args.get('hours', 5))
    
    candles = None
    if breeze_manager.is_connected():
        candles = breeze_manager.get_historical_data(index, '5minute', 1)
    if not candles or len(candles) < 10:
        candles = yahoo_manager.get_candles(index, '5m', '1d')
        
    analysis = analyze_recent_trades(candles, index, hours)
    return jsonify(analysis)


def background_update():
    while is_running:
        try:
            nifty = None
            banknifty = None
            
            # Try Breeze first (fastest)
            if breeze_manager.is_connected():
                nifty = breeze_manager.get_live_price('nifty')
                banknifty = breeze_manager.get_live_price('banknifty')
                
            # Try Angel One if Breeze fails
            if angel_one_enhanced.is_logged_in:
                if not nifty: nifty = angel_one_enhanced.get_ltp('nifty')
                if not banknifty: banknifty = angel_one_enhanced.get_ltp('banknifty')
                
            # Try Yahoo as last fallback
            if not nifty: nifty = yahoo_manager.get_live_price('nifty')
            if not banknifty: banknifty = yahoo_manager.get_live_price('banknifty')
            
            if nifty or banknifty:
                # Validate ML predictions with live prices
                if nifty:
                    validate_past_predictions(nifty.get('ltp', 0) if isinstance(nifty, dict) else nifty)
                
                socketio.emit('price_update', {'nifty': nifty, 'banknifty': banknifty})
            else:
                print(f"DEBUG: NO DATA fetched for indices")
                socketio.emit('price_update', {'error': 'NO_DATA'})
        except Exception as e:
            print(f"Background update error: {e}")
        time.sleep(1.5)  # Faster updates for real-time responsiveness

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  NIFTY PREDICTOR PRO - Python ML Trading System")
    print("  Dashboard: http://127.0.0.1:5000")
    print("="*60 + "\n")
    
    threading.Thread(target=background_update, daemon=True).start()
    socketio.run(app, debug=False, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
