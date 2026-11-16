"""
Real-Time Market Data Simulator
Generates realistic OHLCV data with market microstructure
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
import math
import time
import json
from global_constants import INDEX_CONFIG, MARKET_CONFIG, TIMEFRAME_CONFIG


class MarketDataSimulator:
    """
    Sophisticated market data simulator with:
    - Mean-reverting price behavior
    - Volatility clustering (GARCH-like)
    - Intraday patterns (gap open, lunch lull, closing volatility)
    - Realistic volume profiles
    """
    
    def __init__(self, index='nifty'):
        self.index = index
        self.config = INDEX_CONFIG[index]
        self.base_price = self.config['base_price']
        self.current_price = self.base_price
        self.volatility = self.config['volatility']
        
        # State variables
        self.price_history = []
        self.candle_history = []
        self.current_candle = None
        self.candle_start_time = None
        self.trend_direction = 0  # -1, 0, 1
        self.trend_strength = 0.5
        self.volatility_regime = 'normal'  # low, normal, high
        
        # Generate initial history
        self._generate_initial_history()
    
    def _generate_initial_history(self, periods=100):
        """Generate initial historical candles for indicators"""
        now = datetime.now()
        
        for i in range(periods, 0, -1):
            candle_time = now - timedelta(minutes=5 * i)
            self._generate_candle(candle_time, is_historical=True)
    
    def _get_intraday_factor(self, hour, minute):
        """
        Calculate volatility multiplier based on time of day
        - Morning (9:15-10:30): High volatility (gap fill, opening rush)
        - Midday (10:30-14:00): Lower volatility (consolidation)
        - Afternoon (14:00-15:30): Higher volatility (trend development, closing)
        """
        time_in_minutes = hour * 60 + minute
        
        # Before market open
        if time_in_minutes < 9 * 60 + 15:
            return 0.5
        
        # Opening rush (9:15 - 10:30)
        if time_in_minutes < 10 * 60 + 30:
            return 1.5 + 0.3 * random.random()
        
        # Lunch lull (11:30 - 13:00)
        if 11 * 60 + 30 <= time_in_minutes < 13 * 60:
            return 0.6 + 0.2 * random.random()
        
        # Pre-close volatility (14:30 - 15:30)
        if time_in_minutes >= 14 * 60 + 30:
            return 1.4 + 0.4 * random.random()
        
        # Normal trading
        return 1.0 + 0.2 * (random.random() - 0.5)
    
    def _update_trend(self):
        """Update market trend with momentum and mean reversion"""
        # Random trend changes
        if random.random() < 0.05:  # 5% chance of trend change
            self.trend_direction = random.choice([-1, 0, 1])
            self.trend_strength = random.uniform(0.3, 0.8)
        
        # Mean reversion when price deviates too much
        deviation = (self.current_price - self.base_price) / self.base_price
        if abs(deviation) > 0.02:  # More than 2% deviation
            self.trend_direction = -1 if deviation > 0 else 1
            self.trend_strength = min(0.9, abs(deviation) * 20)
    
    def _update_volatility_regime(self):
        """Switch between volatility regimes"""
        r = random.random()
        if self.volatility_regime == 'normal':
            if r < 0.02:
                self.volatility_regime = 'high'
            elif r < 0.04:
                self.volatility_regime = 'low'
        elif self.volatility_regime == 'high':
            if r < 0.1:
                self.volatility_regime = 'normal'
        else:  # low
            if r < 0.08:
                self.volatility_regime = 'normal'
    
    def _get_volatility_multiplier(self):
        """Get volatility multiplier based on regime"""
        multipliers = {
            'low': 0.5,
            'normal': 1.0,
            'high': 2.0
        }
        return multipliers[self.volatility_regime]
    
    def _generate_price_move(self, dt: datetime):
        """Generate realistic price movement"""
        self._update_trend()
        self._update_volatility_regime()
        
        # Base random component
        random_component = np.random.normal(0, 1)
        
        # Trend component
        trend_component = self.trend_direction * self.trend_strength * 0.5
        
        # Combine
        move = random_component + trend_component
        
        # Apply volatility
        intraday_factor = self._get_intraday_factor(dt.hour, dt.minute)
        vol_multiplier = self._get_volatility_multiplier()
        
        price_change = move * self.volatility * intraday_factor * vol_multiplier * self.current_price
        
        self.current_price += price_change
        
        # Bounds check
        min_price = self.base_price * 0.95
        max_price = self.base_price * 1.05
        self.current_price = max(min_price, min(max_price, self.current_price))
        
        return self.current_price
    
    def _generate_volume(self, dt: datetime, price_change: float):
        """Generate realistic volume based on time and price movement"""
        base_volume = 500000 if self.index == 'nifty' else 200000
        
        # Volume is higher with larger price moves
        volatility_factor = 1 + min(3, abs(price_change) / (self.current_price * 0.001))
        
        # Time-based volume pattern
        hour = dt.hour
        if 9 <= hour < 10:
            time_factor = 1.5
        elif 14 <= hour < 16:
            time_factor = 1.3
        elif 12 <= hour < 13:
            time_factor = 0.6
        else:
            time_factor = 1.0
        
        volume = int(base_volume * volatility_factor * time_factor * (0.5 + random.random()))
        return volume
    
    def _generate_candle(self, timestamp: datetime, is_historical=False):
        """Generate a complete OHLCV candle"""
        # Generate multiple ticks within the candle
        ticks = []
        for _ in range(20):  # 20 ticks per candle
            price = self._generate_price_move(timestamp)
            ticks.append(price)
        
        open_price = ticks[0]
        close_price = ticks[-1]
        high_price = max(ticks)
        low_price = min(ticks)
        volume = self._generate_volume(timestamp, close_price - open_price)
        
        candle = {
            'timestamp': int(timestamp.timestamp()),
            'datetime': timestamp.isoformat(),
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': volume
        }
        
        self.candle_history.append(candle)
        
        # Keep only last 500 candles
        if len(self.candle_history) > 500:
            self.candle_history = self.candle_history[-500:]
        
        return candle
    
    def get_current_price(self):
        """Get current live price with micro-movements"""
        # #region agent log
        old_price = self.current_price
        # #endregion
        now = datetime.now()
        self._generate_price_move(now)
        # #region agent log
        log_data = {"location":"data_simulator.py:206","message":"get_current_price price updated","data":{"oldPrice":old_price,"newPrice":self.current_price,"index":self.index},"timestamp":int(time.time() * 1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}
        with open('e:\\WORKOUT CODE\\.cursor\\debug.log', 'a') as f: f.write(json.dumps(log_data) + '\n')
        # #endregion
        return {
            'ltp': round(self.current_price, 2),
            'change': round(((self.current_price - self.base_price) / self.base_price) * 100, 2),
            'open': round(self.base_price, 2),
            'high': round(max(self.current_price, self.base_price * 1.002), 2),
            'low': round(min(self.current_price, self.base_price * 0.998), 2),
            'timestamp': now.isoformat()
        }
    
    def get_candles(self, timeframe='5m', count=100):
        """Get historical candles"""
        if len(self.candle_history) < count:
            # Generate more history if needed
            self._generate_initial_history(count - len(self.candle_history))
        
        return self.candle_history[-count:]
    
    def update_tick(self):
        """Called every second to update price"""
        now = datetime.now()
        
        # Generate new candle every 5 minutes
        if self.candle_start_time is None:
            self.candle_start_time = now
            self.current_candle = {
                'timestamp': int(now.timestamp()),
                'datetime': now.isoformat(),
                'open': self.current_price,
                'high': self.current_price,
                'low': self.current_price,
                'close': self.current_price,
                'volume': 0
            }
        
        # Update current candle with new tick
        self._generate_price_move(now)
        
        self.current_candle['close'] = round(self.current_price, 2)
        self.current_candle['high'] = max(self.current_candle['high'], self.current_price)
        self.current_candle['low'] = min(self.current_candle['low'], self.current_price)
        self.current_candle['volume'] += random.randint(1000, 5000)
        
        # Check if candle is complete (5 minutes)
        if (now - self.candle_start_time).seconds >= 300:
            self.candle_history.append(self.current_candle.copy())
            
            # Keep only last 500 candles
            if len(self.candle_history) > 500:
                self.candle_history = self.candle_history[-500:]
            
            # Start new candle
            self.candle_start_time = now
            self.current_candle = {
                'timestamp': int(now.timestamp()),
                'datetime': now.isoformat(),
                'open': self.current_price,
                'high': self.current_price,
                'low': self.current_price,
                'close': self.current_price,
                'volume': 0
            }
        
        return self.get_current_price()
    
    def get_option_chain(self, expiry_days=7):
        """Generate realistic option chain data"""
        spot = self.current_price
        strike_step = self.config['strike_step']
        atm_strike = round(spot / strike_step) * strike_step
        
        chain = []
        for offset in range(-10, 11):
            strike = atm_strike + (offset * strike_step)
            
            # Black-Scholes approximation for option prices
            time_to_expiry = expiry_days / 365
            vol = self.volatility * 15  # Annualized
            
            # Simplified option pricing
            itm_ce = max(0, spot - strike)
            itm_pe = max(0, strike - spot)
            
            extrinsic_ce = spot * vol * math.sqrt(time_to_expiry) * 0.4
            extrinsic_pe = spot * vol * math.sqrt(time_to_expiry) * 0.4
            
            ce_price = round(itm_ce + extrinsic_ce * math.exp(-abs(offset) * 0.15), 2)
            pe_price = round(itm_pe + extrinsic_pe * math.exp(-abs(offset) * 0.15), 2)
            
            # OI data
            ce_oi = int(1000000 * math.exp(-abs(offset) * 0.2) * (0.5 + random.random()))
            pe_oi = int(1200000 * math.exp(-abs(offset) * 0.2) * (0.5 + random.random()))
            
            chain.append({
                'strike': strike,
                'ce_oi': ce_oi,
                'ce_change': random.randint(-50000, 50000),
                'ce_price': ce_price,
                'pe_price': pe_price,
                'pe_oi': pe_oi,
                'pe_change': random.randint(-50000, 50000),
                'is_atm': offset == 0
            })
        
        return chain
    
    def get_market_sentiment(self):
        """Generate market sentiment data"""
        return {
            'vix': round(12 + random.uniform(-2, 5), 2),
            'vix_change': round(random.uniform(-1, 1), 2),
            'pcr': round(0.8 + random.uniform(0, 0.6), 2),
            'total_ce_oi': random.randint(5000000, 8000000),
            'total_pe_oi': random.randint(6000000, 9000000),
            'fii_net': random.randint(-2000, 2000),
            'dii_net': random.randint(-1000, 1500),
            'advance_decline': random.uniform(0.4, 1.6)
        }


# Singleton instances
nifty_simulator = MarketDataSimulator('nifty')
banknifty_simulator = MarketDataSimulator('banknifty')


def get_simulator(index='nifty'):
    """Get the simulator for the specified index"""
    return nifty_simulator if index == 'nifty' else banknifty_simulator
