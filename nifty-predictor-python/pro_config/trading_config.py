# Trading Configuration (Display Only - No Live Trading)

# Capital Settings
INITIAL_CAPITAL = 100000
NIFTY_ALLOCATION = 0.60
BANKNIFTY_ALLOCATION = 0.40

# Risk Parameters
RISK_PER_TRADE = 0.02  # 2%
MAX_DRAWDOWN_LIMIT = 0.15  # 15%
MAX_DAILY_LOSS = 0.05  # 5%

# Position Sizing
MAX_POSITION_SIZE = 0.05  # 5% of capital

# Index Configuration
INDEX_CONFIG = {
    'nifty': {
        'lot_size': 75,
        'strike_step': 50,
        'symbol': 'NIFTY'
    },
    'banknifty': {
        'lot_size': 30,
        'strike_step': 100,
        'symbol': 'BANKNIFTY'
    }
}

# Signal Thresholds
SIGNAL_CONFIG = {
    'strong_buy': 0.70,
    'buy': 0.55,
    'hold_min': 0.45,
    'hold_max': 0.55,
    'sell': 0.45,
    'strong_sell': 0.30
}

# Time Settings
MARKET_OPEN = {'hour': 9, 'minute': 15}
MARKET_CLOSE = {'hour': 15, 'minute': 30}
