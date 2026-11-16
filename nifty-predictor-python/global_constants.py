"""
Configuration for the Nifty Predictor Pro Python Application
"""

# Trading Configuration
TRADING_CONFIG = {
    'capital': 1000000,  # Pro Account: 10 Lakhs
    'risk_percentage': 2,  # Risk per trade
    'profit_target': 1.5,  # Risk-Reward ratio
    'min_lots': 1,
    'max_lots': 50  # Increased for higher profit potential
}

# Market Hours (IST)
MARKET_CONFIG = {
    'open_hour': 9,
    'open_minute': 15,
    'close_hour': 15,
    'close_minute': 30
}

# Index Configuration (lot sizes mirror pro_config/trading_config.py —
# the single source of truth; simulator display values only)
try:
    from pro_config.trading_config import LOT_SIZES as _LOT_SIZES
except ImportError:
    _LOT_SIZES = {'nifty': 75, 'banknifty': 30}

INDEX_CONFIG = {
    'nifty': {
        'name': 'NIFTY 50',
        'base_price': 25487,
        'strike_step': 50,
        'volatility': 0.0015,  # 0.15% base volatility
        'lot_size': _LOT_SIZES.get('nifty', 75)
    },
    'banknifty': {
        'name': 'BANK NIFTY',
        'base_price': 59855,
        'strike_step': 100,
        'volatility': 0.002,  # 0.20% base volatility
        'lot_size': _LOT_SIZES.get('banknifty', 30)
    }
}

# Timeframe Configuration
TIMEFRAME_CONFIG = {
    '1m': {'seconds': 60, 'candles': 60},
    '5m': {'seconds': 300, 'candles': 100},
    '15m': {'seconds': 900, 'candles': 50},
    '1h': {'seconds': 3600, 'candles': 24},
    '1d': {'seconds': 86400, 'candles': 30}
}

# ML Model Configuration
ML_CONFIG = {
    'lookback_period': 60,
    'prediction_horizon': 5,
    'retrain_interval': 300,  # Retrain every 5 minutes
    'min_training_samples': 100
}

# Strategy Weights for Combined Prediction
STRATEGY_WEIGHTS = {
    'rsi': 1.0,
    'macd': 1.0,
    'bollinger': 0.9,
    'stochastic': 0.8,
    'adx': 1.1,
    'supertrend': 1.2,
    'vwap': 0.9,
    'ichimoku': 1.0,
    'cci': 0.8,
    'williams_r': 0.7,
    'ml_prediction': 1.5  # ML gets higher weight
}
