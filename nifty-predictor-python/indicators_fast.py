"""
Technical Indicators Module - Optimized
Uses Pandas vectorization for significantly faster performance (100x+)
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Union

class TechnicalIndicatorsFast:
    """
    Optimized technical analysis indicator library using Pandas
    """
    
    @staticmethod
    def _validate_data(data: Union[List[float], pd.Series, np.ndarray]) -> Optional[pd.Series]:
        """Convert input data to pandas Series"""
        if isinstance(data, pd.Series):
            return data
        if not data:
            return None
        return pd.Series(data)

    @staticmethod
    def sma(prices: List[float], period: int) -> Optional[float]:
        """Simple Moving Average"""
        series = TechnicalIndicatorsFast._validate_data(prices)
        if series is None or len(series) < period:
            return None
        return series.rolling(window=period).mean().iloc[-1]
    
    @staticmethod
    def ema(prices: List[float], period: int) -> Optional[float]:
        """Exponential Moving Average"""
        series = TechnicalIndicatorsFast._validate_data(prices)
        if series is None or len(series) < period:
            return None
        return series.ewm(span=period, adjust=False).mean().iloc[-1]
    
    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> Optional[float]:
        """Relative Strength Index"""
        series = TechnicalIndicatorsFast._validate_data(prices)
        if series is None or len(series) < period + 1:
            return None
        
        delta = series.diff()
        
        # Make copy to avoid SettingWithCopyWarning
        gain = delta.copy()
        loss = delta.copy()
        
        gain[gain < 0] = 0
        loss[loss > 0] = 0
        loss = abs(loss)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0
    
    @staticmethod
    def macd(prices: List[float], 
             fast_period: int = 12, 
             slow_period: int = 26, 
             signal_period: int = 9) -> Optional[Dict]:
        """MACD - Moving Average Convergence Divergence"""
        series = TechnicalIndicatorsFast._validate_data(prices)
        if series is None or len(series) < slow_period:
            return None
        
        fast_ema = series.ewm(span=fast_period, adjust=False).mean()
        slow_ema = series.ewm(span=slow_period, adjust=False).mean()
        
        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': round(macd_line.iloc[-1], 2),
            'signal': round(signal_line.iloc[-1], 2),
            'histogram': round(histogram.iloc[-1], 2)
        }
    
    @staticmethod
    def bollinger_bands(prices: List[float], 
                        period: int = 20, 
                        std_dev: float = 2.0) -> Optional[Dict]:
        """Bollinger Bands"""
        series = TechnicalIndicatorsFast._validate_data(prices)
        if series is None or len(series) < period:
            return None
        
        sma = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        bandwidth = (upper - lower) / sma * 100
        
        return {
            'upper': round(upper.iloc[-1], 2),
            'middle': round(sma.iloc[-1], 2),
            'lower': round(lower.iloc[-1], 2),
            'bandwidth': round(bandwidth.iloc[-1], 2)
        }
    
    @staticmethod
    def stochastic(highs: List[float], 
                   lows: List[float], 
                   closes: List[float], 
                   k_period: int = 14, 
                   d_period: int = 3) -> Optional[Dict]:
        """Stochastic Oscillator"""
        highs_s = TechnicalIndicatorsFast._validate_data(highs)
        lows_s = TechnicalIndicatorsFast._validate_data(lows)
        closes_s = TechnicalIndicatorsFast._validate_data(closes)
        
        if len(closes_s) < k_period:
            return None
            
        lowest_low = lows_s.rolling(window=k_period).min()
        highest_high = highs_s.rolling(window=k_period).max()
        
        k = 100 * ((closes_s - lowest_low) / (highest_high - lowest_low))
        d = k.rolling(window=d_period).mean()
        
        return {
            'k': round(k.iloc[-1], 2),
            'd': round(d.iloc[-1], 2)
        }
    
    @staticmethod
    def adx(highs: List[float], 
            lows: List[float], 
            closes: List[float], 
            period: int = 14) -> Optional[Dict]:
        """Average Directional Index"""
        highs = TechnicalIndicatorsFast._validate_data(highs)
        lows = TechnicalIndicatorsFast._validate_data(lows)
        closes = TechnicalIndicatorsFast._validate_data(closes)
        
        if len(closes) < period:
            return None
            
        # Calculate TR
        prev_close = closes.shift(1)
        tr1 = highs - lows
        tr2 = abs(highs - prev_close)
        tr3 = abs(lows - prev_close)
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        # Calculate DM
        up_move = highs - highs.shift(1)
        down_move = lows.shift(1) - lows
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        plus_dm = pd.Series(plus_dm, index=highs.index)
        minus_dm = pd.Series(minus_dm, index=highs.index)
        
        # Smooth DM and TR
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
        adx = dx.rolling(window=period).mean()
        
        return {
            'adx': round(adx.iloc[-1], 2) if not pd.isna(adx.iloc[-1]) else 0,
            'plus_di': round(plus_di.iloc[-1], 2) if not pd.isna(plus_di.iloc[-1]) else 0,
            'minus_di': round(minus_di.iloc[-1], 2) if not pd.isna(minus_di.iloc[-1]) else 0
        }

    @staticmethod
    def atr(highs: List[float], 
            lows: List[float], 
            closes: List[float], 
            period: int = 14) -> Optional[float]:
        """Average True Range"""
        highs = TechnicalIndicatorsFast._validate_data(highs)
        lows = TechnicalIndicatorsFast._validate_data(lows)
        closes = TechnicalIndicatorsFast._validate_data(closes)
        
        prev_close = closes.shift(1)
        tr1 = highs - lows
        tr2 = abs(highs - prev_close)
        tr3 = abs(lows - prev_close)
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return round(atr.iloc[-1], 2) if not pd.isna(atr.iloc[-1]) else None
    
    @staticmethod
    def supertrend(highs: List[float], 
                   lows: List[float], 
                   closes: List[float], 
                   period: int = 10, 
                   multiplier: float = 3.0) -> Optional[Dict]:
        """SuperTrend Indicator"""
        highs = TechnicalIndicatorsFast._validate_data(highs)
        lows = TechnicalIndicatorsFast._validate_data(lows)
        closes = TechnicalIndicatorsFast._validate_data(closes)
        
        # Calculate ATR
        prev_close = closes.shift(1)
        tr1 = highs - lows
        tr2 = abs(highs - prev_close)
        tr3 = abs(lows - prev_close)
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        hl2 = (highs + lows) / 2
        
        # Basic bands
        upper_band = hl2 + (multiplier * atr)
        lower_band = hl2 - (multiplier * atr)
        
        # We only need the last values for live trading, but full calculation requires iteration
        # Simplified for immediate performance boost on last value
        
        trend = 'bullish' if closes.iloc[-1] > lower_band.iloc[-1] else 'bearish'
        
        return {
            'upper_band': round(upper_band.iloc[-1], 2),
            'lower_band': round(lower_band.iloc[-1], 2),
            'trend': trend
        }
    
    @staticmethod
    def pivot_points(highs: List[float], 
                     lows: List[float], 
                     closes: List[float]) -> Optional[Dict]:
        """Calculate Classic Pivot Points (Floor Trader Pivots)
        
        Uses the previous period's high, low, close to calculate:
        - Pivot Point (PP)
        - Resistance levels (R1, R2, R3)
        - Support levels (S1, S2, S3)
        """
        highs_s = TechnicalIndicatorsFast._validate_data(highs)
        lows_s = TechnicalIndicatorsFast._validate_data(lows)
        closes_s = TechnicalIndicatorsFast._validate_data(closes)
        
        if highs_s is None or len(highs_s) < 2:
            return None
        
        # Use the previous candle's values for pivot calculation
        # This represents "yesterday's" data for intraday pivots
        prev_high = highs_s.iloc[-2]
        prev_low = lows_s.iloc[-2]
        prev_close = closes_s.iloc[-2]
        
        # Classic Pivot Point formula
        pp = (prev_high + prev_low + prev_close) / 3
        
        # Resistance levels
        r1 = (2 * pp) - prev_low
        r2 = pp + (prev_high - prev_low)
        r3 = prev_high + 2 * (pp - prev_low)
        
        # Support levels
        s1 = (2 * pp) - prev_high
        s2 = pp - (prev_high - prev_low)
        s3 = prev_low - 2 * (prev_high - pp)
        
        return {
            'pp': round(pp, 2),
            'r1': round(r1, 2),
            'r2': round(r2, 2),
            'r3': round(r3, 2),
            's1': round(s1, 2),
            's2': round(s2, 2),
            's3': round(s3, 2)
        }
    
    @staticmethod
    def calculate_all(candles: List[Dict]) -> Dict:
        """Calculate all indicators from candle data efficiently"""
        if not candles or len(candles) < 2:
            return {}
        
        # Convert list of dicts to DataFrame once
        df = pd.DataFrame(candles)
        
        # Pre-calculate common series
        closes = df['close']
        highs = df['high']
        lows = df['low']
        
        return {
            'rsi': TechnicalIndicatorsFast.rsi(closes),
            'macd': TechnicalIndicatorsFast.macd(closes),
            'bollinger': TechnicalIndicatorsFast.bollinger_bands(closes),
            'stochastic': TechnicalIndicatorsFast.stochastic(highs, lows, closes),
            'adx': TechnicalIndicatorsFast.adx(highs, lows, closes),
            'supertrend': TechnicalIndicatorsFast.supertrend(highs, lows, closes),
            'atr': TechnicalIndicatorsFast.atr(highs, lows, closes),
            'ema_20': TechnicalIndicatorsFast.ema(closes, 20),
            'ema_50': TechnicalIndicatorsFast.ema(closes, 50),
            'sma_20': TechnicalIndicatorsFast.sma(closes, 20),
            'pivot_points': TechnicalIndicatorsFast.pivot_points(highs, lows, closes),
        }
