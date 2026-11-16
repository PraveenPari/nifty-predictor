"""
Technical Indicators Module
All indicators implemented from scratch for robustness
"""

import numpy as np
from typing import List, Dict, Optional, Tuple


class TechnicalIndicators:
    """
    Complete technical analysis indicator library
    """
    
    @staticmethod
    def sma(prices: List[float], period: int) -> Optional[float]:
        """Simple Moving Average"""
        if len(prices) < period:
            return None
        return np.mean(prices[-period:])
    
    @staticmethod
    def ema(prices: List[float], period: int) -> Optional[float]:
        """Exponential Moving Average"""
        if len(prices) < period:
            return None
        
        multiplier = 2 / (period + 1)
        ema = np.mean(prices[:period])
        
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> Optional[float]:
        """Relative Strength Index"""
        if len(prices) < period + 1:
            return None
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            gains.append(max(change, 0))
            losses.append(abs(min(change, 0)))
        
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def macd(prices: List[float], 
             fast_period: int = 12, 
             slow_period: int = 26, 
             signal_period: int = 9) -> Optional[Dict]:
        """MACD - Moving Average Convergence Divergence"""
        if len(prices) < slow_period:
            return None
        
        fast_ema = TechnicalIndicators.ema(prices, fast_period)
        slow_ema = TechnicalIndicators.ema(prices, slow_period)
        
        if fast_ema is None or slow_ema is None:
            return None
        
        macd_line = fast_ema - slow_ema
        signal_line = macd_line * 0.9  # Simplified
        histogram = macd_line - signal_line
        
        return {
            'macd': round(macd_line, 2),
            'signal': round(signal_line, 2),
            'histogram': round(histogram, 2)
        }
    
    @staticmethod
    def bollinger_bands(prices: List[float], 
                        period: int = 20, 
                        std_dev: float = 2.0) -> Optional[Dict]:
        """Bollinger Bands"""
        if len(prices) < period:
            return None
        
        sma = np.mean(prices[-period:])
        std = np.std(prices[-period:])
        
        return {
            'upper': round(sma + (std * std_dev), 2),
            'middle': round(sma, 2),
            'lower': round(sma - (std * std_dev), 2),
            'bandwidth': round((std * std_dev * 2) / sma * 100, 2)
        }
    
    @staticmethod
    def stochastic(highs: List[float], 
                   lows: List[float], 
                   closes: List[float], 
                   k_period: int = 14, 
                   d_period: int = 3) -> Optional[Dict]:
        """Stochastic Oscillator"""
        if len(closes) < k_period:
            return None
        
        highest_high = max(highs[-k_period:])
        lowest_low = min(lows[-k_period:])
        current_close = closes[-1]
        
        if highest_high == lowest_low:
            k = 50
        else:
            k = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
        
        d = k * 0.9  # Simplified D line
        
        return {
            'k': round(k, 2),
            'd': round(d, 2)
        }
    
    @staticmethod
    def adx(highs: List[float], 
            lows: List[float], 
            closes: List[float], 
            period: int = 14) -> Optional[Dict]:
        """Average Directional Index"""
        if len(closes) < period:
            return None
        
        plus_dm = 0
        minus_dm = 0
        tr = 0
        
        for i in range(1, min(period, len(highs))):
            high_diff = highs[i] - highs[i-1]
            low_diff = lows[i-1] - lows[i]
            
            if high_diff > low_diff and high_diff > 0:
                plus_dm += high_diff
            if low_diff > high_diff and low_diff > 0:
                minus_dm += low_diff
            
            tr += max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
        
        if tr == 0:
            return {'adx': 0, 'plus_di': 0, 'minus_di': 0}
        
        plus_di = (plus_dm / tr) * 100
        minus_di = (minus_dm / tr) * 100
        
        if plus_di + minus_di == 0:
            dx = 0
        else:
            dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100
        
        return {
            'adx': round(dx, 2),
            'plus_di': round(plus_di, 2),
            'minus_di': round(minus_di, 2)
        }
    
    @staticmethod
    def atr(highs: List[float], 
            lows: List[float], 
            closes: List[float], 
            period: int = 14) -> Optional[float]:
        """Average True Range"""
        if len(closes) < period:
            return None
        
        tr_values = []
        for i in range(1, len(highs)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            tr_values.append(tr)
        
        return round(np.mean(tr_values[-period:]), 2) if tr_values else None
    
    @staticmethod
    def supertrend(highs: List[float], 
                   lows: List[float], 
                   closes: List[float], 
                   period: int = 10, 
                   multiplier: float = 3.0) -> Optional[Dict]:
        """SuperTrend Indicator"""
        atr = TechnicalIndicators.atr(highs, lows, closes, period)
        if atr is None:
            return None
        
        hl2 = (highs[-1] + lows[-1]) / 2
        upper_band = hl2 + (multiplier * atr)
        lower_band = hl2 - (multiplier * atr)
        
        trend = 'bullish' if closes[-1] > lower_band else 'bearish'
        
        return {
            'upper_band': round(upper_band, 2),
            'lower_band': round(lower_band, 2),
            'trend': trend
        }
    
    @staticmethod
    def vwap(highs: List[float], 
             lows: List[float], 
             closes: List[float], 
             volumes: List[int]) -> Optional[float]:
        """Volume Weighted Average Price"""
        if len(closes) < 1 or sum(volumes) == 0:
            return None
        
        typical_prices = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]
        total_vp = sum(tp * v for tp, v in zip(typical_prices, volumes))
        total_vol = sum(volumes)
        
        return round(total_vp / total_vol, 2)
    
    @staticmethod
    def ichimoku(highs: List[float], 
                 lows: List[float], 
                 closes: List[float]) -> Optional[Dict]:
        """Ichimoku Cloud"""
        conversion_period = 9
        base_period = 26
        
        if len(closes) < base_period:
            return None
        
        # Tenkan-sen (Conversion Line)
        conversion_high = max(highs[-conversion_period:])
        conversion_low = min(lows[-conversion_period:])
        tenkan = (conversion_high + conversion_low) / 2
        
        # Kijun-sen (Base Line)
        base_high = max(highs[-base_period:])
        base_low = min(lows[-base_period:])
        kijun = (base_high + base_low) / 2
        
        # Senkou Span A (Leading Span A)
        senkou_a = (tenkan + kijun) / 2
        
        # Senkou Span B (Leading Span B) - simplified
        senkou_b = (base_high + base_low) / 2
        
        return {
            'tenkan': round(tenkan, 2),
            'kijun': round(kijun, 2),
            'senkou_a': round(senkou_a, 2),
            'senkou_b': round(senkou_b, 2),
            'current_price': closes[-1]
        }
    
    @staticmethod
    def cci(highs: List[float], 
            lows: List[float], 
            closes: List[float], 
            period: int = 20) -> Optional[float]:
        """Commodity Channel Index"""
        if len(closes) < period:
            return None
        
        typical_prices = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]
        sma = np.mean(typical_prices[-period:])
        mean_deviation = np.mean([abs(tp - sma) for tp in typical_prices[-period:]])
        
        if mean_deviation == 0:
            return 0
        
        return round((typical_prices[-1] - sma) / (0.015 * mean_deviation), 2)
    
    @staticmethod
    def williams_r(highs: List[float], 
                   lows: List[float], 
                   closes: List[float], 
                   period: int = 14) -> Optional[float]:
        """Williams %R"""
        if len(closes) < period:
            return None
        
        highest_high = max(highs[-period:])
        lowest_low = min(lows[-period:])
        
        if highest_high == lowest_low:
            return -50
        
        return round(((highest_high - closes[-1]) / (highest_high - lowest_low)) * -100, 2)
    
    @staticmethod
    def pivot_points(high: float, low: float, close: float) -> Dict:
        """Standard Pivot Points"""
        pivot = (high + low + close) / 3
        
        return {
            'pivot': round(pivot, 2),
            'r1': round((2 * pivot) - low, 2),
            'r2': round(pivot + (high - low), 2),
            'r3': round(high + 2 * (pivot - low), 2),
            's1': round((2 * pivot) - high, 2),
            's2': round(pivot - (high - low), 2),
            's3': round(low - 2 * (high - pivot), 2)
        }
    
    @staticmethod
    def parabolic_sar(highs: List[float], 
                      lows: List[float], 
                      closes: List[float], 
                      af: float = 0.02, 
                      max_af: float = 0.2) -> Optional[Dict]:
        """Parabolic SAR"""
        if len(closes) < 5:
            return None
        
        current_price = closes[-1]
        prev_high = max(highs[-5:])
        prev_low = min(lows[-5:])
        
        # Simplified SAR
        mid_point = (prev_high + prev_low) / 2
        sar = prev_low * 0.98 if current_price > mid_point else prev_high * 1.02
        trend = 'bullish' if current_price > sar else 'bearish'
        
        return {
            'sar': round(sar, 2),
            'trend': trend
        }
    
    @staticmethod
    def mfi(highs: List[float], 
            lows: List[float], 
            closes: List[float], 
            volumes: List[int], 
            period: int = 14) -> Optional[float]:
        """Money Flow Index"""
        if len(closes) < period:
            return None
        
        positive_flow = 0
        negative_flow = 0
        
        for i in range(1, min(period, len(closes))):
            typical_price = (highs[i] + lows[i] + closes[i]) / 3
            prev_typical = (highs[i-1] + lows[i-1] + closes[i-1]) / 3
            raw_flow = typical_price * volumes[i]
            
            if typical_price > prev_typical:
                positive_flow += raw_flow
            else:
                negative_flow += raw_flow
        
        if negative_flow == 0:
            return 100
        
        ratio = positive_flow / negative_flow
        return round(100 - (100 / (1 + ratio)), 2)
    
    @staticmethod
    def obv(closes: List[float], volumes: List[int]) -> float:
        """On-Balance Volume"""
        obv = 0
        for i in range(1, len(closes)):
            if closes[i] > closes[i-1]:
                obv += volumes[i]
            elif closes[i] < closes[i-1]:
                obv -= volumes[i]
        return obv
    
    @staticmethod
    def calculate_all(candles: List[Dict]) -> Dict:
        """Calculate all indicators from candle data"""
        if not candles or len(candles) < 2:
            return {}
        
        highs = [c['high'] for c in candles]
        lows = [c['low'] for c in candles]
        closes = [c['close'] for c in candles]
        volumes = [c['volume'] for c in candles]
        
        return {
            'rsi': TechnicalIndicators.rsi(closes),
            'macd': TechnicalIndicators.macd(closes),
            'bollinger': TechnicalIndicators.bollinger_bands(closes),
            'stochastic': TechnicalIndicators.stochastic(highs, lows, closes),
            'adx': TechnicalIndicators.adx(highs, lows, closes),
            'supertrend': TechnicalIndicators.supertrend(highs, lows, closes),
            'vwap': TechnicalIndicators.vwap(highs, lows, closes, volumes),
            'ichimoku': TechnicalIndicators.ichimoku(highs, lows, closes),
            'cci': TechnicalIndicators.cci(highs, lows, closes),
            'williams_r': TechnicalIndicators.williams_r(highs, lows, closes),
            'atr': TechnicalIndicators.atr(highs, lows, closes),
            'ema_20': TechnicalIndicators.ema(closes, 20),
            'ema_50': TechnicalIndicators.ema(closes, 50),
            'sma_20': TechnicalIndicators.sma(closes, 20),
            'psar': TechnicalIndicators.parabolic_sar(highs, lows, closes),
            'mfi': TechnicalIndicators.mfi(highs, lows, closes, volumes),
            'pivot_points': TechnicalIndicators.pivot_points(
                max(highs[-1:]) if highs else 0,
                min(lows[-1:]) if lows else 0,
                closes[-1] if closes else 0
            )
        }
