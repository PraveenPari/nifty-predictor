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
    def vwap(highs: List[float],
             lows: List[float],
             closes: List[float],
             volumes: List[float]) -> Optional[float]:
        """Volume Weighted Average Price (session-anchored)."""
        highs_s = TechnicalIndicatorsFast._validate_data(highs)
        lows_s = TechnicalIndicatorsFast._validate_data(lows)
        closes_s = TechnicalIndicatorsFast._validate_data(closes)
        vols_s = TechnicalIndicatorsFast._validate_data(volumes)
        if highs_s is None or vols_s is None or len(closes_s) < 2:
            return None
        typical = (highs_s + lows_s + closes_s) / 3
        cum_vol = vols_s.cumsum().replace(0, np.nan)
        vwap = (typical * vols_s).cumsum() / cum_vol
        val = vwap.iloc[-1]
        return round(float(val), 2) if not pd.isna(val) else None

    @staticmethod
    def cci(highs: List[float],
            lows: List[float],
            closes: List[float],
            period: int = 20) -> Optional[float]:
        """Commodity Channel Index."""
        highs_s = TechnicalIndicatorsFast._validate_data(highs)
        lows_s = TechnicalIndicatorsFast._validate_data(lows)
        closes_s = TechnicalIndicatorsFast._validate_data(closes)
        if highs_s is None or len(closes_s) < period:
            return None
        tp = (highs_s + lows_s + closes_s) / 3
        sma_tp = tp.rolling(window=period).mean()
        mad = (tp - sma_tp).abs().rolling(window=period).mean()
        cci = (tp - sma_tp) / (0.015 * mad.replace(0, np.nan))
        val = cci.iloc[-1]
        return round(float(val), 2) if not pd.isna(val) else None

    @staticmethod
    def williams_r(highs: List[float],
                   lows: List[float],
                   closes: List[float],
                   period: int = 14) -> Optional[float]:
        """Williams %R."""
        highs_s = TechnicalIndicatorsFast._validate_data(highs)
        lows_s = TechnicalIndicatorsFast._validate_data(lows)
        closes_s = TechnicalIndicatorsFast._validate_data(closes)
        if highs_s is None or len(closes_s) < period:
            return None
        hh = highs_s.rolling(window=period).max()
        ll = lows_s.rolling(window=period).min()
        wr = -100 * (hh - closes_s) / (hh - ll).replace(0, np.nan)
        val = wr.iloc[-1]
        return round(float(val), 2) if not pd.isna(val) else None

    @staticmethod
    def mfi(highs: List[float],
            lows: List[float],
            closes: List[float],
            volumes: List[float],
            period: int = 14) -> Optional[float]:
        """Money Flow Index."""
        highs_s = TechnicalIndicatorsFast._validate_data(highs)
        lows_s = TechnicalIndicatorsFast._validate_data(lows)
        closes_s = TechnicalIndicatorsFast._validate_data(closes)
        vols_s = TechnicalIndicatorsFast._validate_data(volumes)
        if highs_s is None or vols_s is None or len(closes_s) < period + 1:
            return None
        tp = (highs_s + lows_s + closes_s) / 3
        mf = tp * vols_s
        delta = tp.diff()
        pos_mf = mf.where(delta > 0, 0.0).rolling(window=period).sum()
        neg_mf = mf.where(delta < 0, 0.0).rolling(window=period).sum()
        mfr = pos_mf / neg_mf.replace(0, np.nan)
        mfi = 100 - (100 / (1 + mfr))
        val = mfi.iloc[-1]
        return round(float(val), 2) if not pd.isna(val) else 50.0

    @staticmethod
    def parabolic_sar(highs: List[float],
                      lows: List[float],
                      closes: List[float],
                      af_step: float = 0.02,
                      af_max: float = 0.2) -> Optional[Dict]:
        """Parabolic SAR (vectorised-friendly iterative core)."""
        highs_s = TechnicalIndicatorsFast._validate_data(highs)
        lows_s = TechnicalIndicatorsFast._validate_data(lows)
        closes_s = TechnicalIndicatorsFast._validate_data(closes)
        if highs_s is None or len(closes_s) < 5:
            return None
        h = highs_s.to_numpy(dtype=float)
        l = lows_s.to_numpy(dtype=float)
        c = closes_s.to_numpy(dtype=float)
        n = len(c)
        sar = np.zeros(n)
        uptrend = True
        sar[0] = l[0]
        ep = h[0]
        af = af_step
        for i in range(1, n):
            prev_sar = sar[i - 1]
            sar[i] = prev_sar + af * (ep - prev_sar)
            if uptrend:
                sar[i] = min(sar[i], l[i - 1], l[i])
                if c[i] < sar[i]:
                    uptrend = False
                    sar[i] = ep
                    ep = l[i]
                    af = af_step
                else:
                    if h[i] > ep:
                        ep = h[i]
                        af = min(af + af_step, af_max)
            else:
                sar[i] = max(sar[i], h[i - 1], h[i])
                if c[i] > sar[i]:
                    uptrend = True
                    sar[i] = ep
                    ep = h[i]
                    af = af_step
                else:
                    if l[i] < ep:
                        ep = l[i]
                        af = min(af + af_step, af_max)
        return {
            'sar': round(float(sar[-1]), 2),
            'trend': 'bullish' if uptrend else 'bearish',
        }

    @staticmethod
    def ichimoku(highs: List[float],
                 lows: List[float],
                 closes: List[float],
                 tenkan_period: int = 9,
                 kijun_period: int = 26,
                 senkou_period: int = 52) -> Optional[Dict]:
        """Ichimoku Cloud (shifted values aligned to current bar for live use)."""
        highs_s = TechnicalIndicatorsFast._validate_data(highs)
        lows_s = TechnicalIndicatorsFast._validate_data(lows)
        closes_s = TechnicalIndicatorsFast._validate_data(closes)
        if highs_s is None or len(closes_s) < senkou_period:
            return None
        tenkan = (highs_s.rolling(window=tenkan_period).max() +
                  lows_s.rolling(window=tenkan_period).min()) / 2
        kijun = (highs_s.rolling(window=kijun_period).max() +
                 lows_s.rolling(window=kijun_period).min()) / 2
        senkou_a = ((tenkan + kijun) / 2).shift(kijun_period)
        senkou_b = ((highs_s.rolling(window=senkou_period).max() +
                     lows_s.rolling(window=senkou_period).min()) / 2).shift(kijun_period)
        # Current-bar cloud edge (unshifted) for live signal evaluation
        cloud_a = float(((tenkan + kijun) / 2).iloc[-1])
        cloud_b = float(((highs_s.rolling(window=senkou_period).max() +
                          lows_s.rolling(window=senkou_period).min()) / 2).iloc[-1])
        price = float(closes_s.iloc[-1])
        cloud_top = max(cloud_a, cloud_b)
        cloud_bottom = min(cloud_a, cloud_b)
        if price > cloud_top:
            pos = 'above_cloud'
        elif price < cloud_bottom:
            pos = 'below_cloud'
        else:
            pos = 'inside_cloud'
        return {
            'tenkan': round(float(tenkan.iloc[-1]), 2),
            'kijun': round(float(kijun.iloc[-1]), 2),
            'senkou_a': round(cloud_a, 2),
            'senkou_b': round(cloud_b, 2),
            'cloud_top': round(cloud_top, 2),
            'cloud_bottom': round(cloud_bottom, 2),
            'position': pos,
            'current_price': round(price, 2),
        }

    @staticmethod
    def obv(closes: List[float], volumes: List[float]) -> Optional[float]:
        """On-Balance Volume."""
        closes_s = TechnicalIndicatorsFast._validate_data(closes)
        vols_s = TechnicalIndicatorsFast._validate_data(volumes)
        if closes_s is None or vols_s is None or len(closes_s) < 2:
            return None
        direction = np.sign(closes_s.diff().fillna(0))
        obv = (direction * vols_s).cumsum()
        return float(obv.iloc[-1])

    @staticmethod
    def donchian(highs: List[float],
                 lows: List[float],
                 period: int = 20) -> Optional[Dict]:
        """Donchian Channel (highest high / lowest low)."""
        highs_s = TechnicalIndicatorsFast._validate_data(highs)
        lows_s = TechnicalIndicatorsFast._validate_data(lows)
        if highs_s is None or len(highs_s) < period:
            return None
        upper = highs_s.rolling(window=period).max().iloc[-1]
        lower = lows_s.rolling(window=period).min().iloc[-1]
        return {
            'upper': round(float(upper), 2),
            'lower': round(float(lower), 2),
            'middle': round(float((upper + lower) / 2), 2),
        }

    @staticmethod
    def keltner(highs: List[float],
               lows: List[float],
               closes: List[float],
               period: int = 20,
               multiplier: float = 2.0) -> Optional[Dict]:
        """Keltner Channel (EMA ± ATR multiple)."""
        highs_s = TechnicalIndicatorsFast._validate_data(highs)
        lows_s = TechnicalIndicatorsFast._validate_data(lows)
        closes_s = TechnicalIndicatorsFast._validate_data(closes)
        if highs_s is None or len(closes_s) < period + 1:
            return None
        ema = closes_s.ewm(span=period, adjust=False).mean()
        prev_close = closes_s.shift(1)
        tr = pd.concat([highs_s - lows_s,
                        abs(highs_s - prev_close),
                        abs(lows_s - prev_close)], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        upper = ema + multiplier * atr
        lower = ema - multiplier * atr
        return {
            'upper': round(float(upper.iloc[-1]), 2),
            'middle': round(float(ema.iloc[-1]), 2),
            'lower': round(float(lower.iloc[-1]), 2),
        }

    @staticmethod
    def heikin_ashi(candles: List[Dict]) -> Optional[Dict]:
        """Heikin-Ashi trend of the last two candles."""
        if not candles or len(candles) < 3:
            return None
        ha_open_prev = (candles[-3]['open'] + candles[-3]['close']) / 2
        ha_close_prev = (candles[-2]['open'] + candles[-2]['high'] +
                         candles[-2]['low'] + candles[-2]['close']) / 4
        ha_open = (ha_open_prev + ha_close_prev) / 2
        c = candles[-1]
        ha_close = (c['open'] + c['high'] + c['low'] + c['close']) / 4
        ha_high = max(c['high'], ha_open, ha_close)
        ha_low = min(c['low'], ha_open, ha_close)
        if ha_close > ha_open and ha_low >= ha_open - (ha_high - ha_low) * 0.1:
            trend = 'strong_bullish'
        elif ha_close > ha_open:
            trend = 'bullish'
        elif ha_close < ha_open and ha_high <= ha_open + (ha_high - ha_low) * 0.1:
            trend = 'strong_bearish'
        else:
            trend = 'bearish' if ha_close < ha_open else 'doji'
        return {
            'open': round(ha_open, 2), 'high': round(ha_high, 2),
            'low': round(ha_low, 2), 'close': round(ha_close, 2),
            'trend': trend,
        }

    @staticmethod
    def rsi_series(prices: List[float], period: int = 14,
                   lookback: int = 30) -> List[float]:
        """Recent RSI values (for divergence detection)."""
        series = TechnicalIndicatorsFast._validate_data(prices)
        if series is None or len(series) < period + 2:
            return []
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rsi = 100 - (100 / (1 + avg_gain / avg_loss.replace(0, np.nan)))
        return [round(float(x), 2) for x in rsi.dropna().tolist()[-lookback:]]

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
        volumes = df['volume'] if 'volume' in df.columns else pd.Series([0] * len(df))

        return {
            'rsi': TechnicalIndicatorsFast.rsi(closes),
            'macd': TechnicalIndicatorsFast.macd(closes),
            'bollinger': TechnicalIndicatorsFast.bollinger_bands(closes),
            'stochastic': TechnicalIndicatorsFast.stochastic(highs, lows, closes),
            'adx': TechnicalIndicatorsFast.adx(highs, lows, closes),
            'supertrend': TechnicalIndicatorsFast.supertrend(highs, lows, closes),
            'atr': TechnicalIndicatorsFast.atr(highs, lows, closes),
            'ema_9': TechnicalIndicatorsFast.ema(closes, 9),
            'ema_21': TechnicalIndicatorsFast.ema(closes, 21),
            'ema_20': TechnicalIndicatorsFast.ema(closes, 20),
            'ema_50': TechnicalIndicatorsFast.ema(closes, 50),
            'sma_20': TechnicalIndicatorsFast.sma(closes, 20),
            'sma_50': TechnicalIndicatorsFast.sma(closes, 50),
            'pivot_points': TechnicalIndicatorsFast.pivot_points(highs, lows, closes),
            # Previously missing — 6 strategies silently returned "unavailable"
            'vwap': TechnicalIndicatorsFast.vwap(highs, lows, closes, volumes),
            'ichimoku': TechnicalIndicatorsFast.ichimoku(highs, lows, closes),
            'cci': TechnicalIndicatorsFast.cci(highs, lows, closes),
            'williams_r': TechnicalIndicatorsFast.williams_r(highs, lows, closes),
            'psar': TechnicalIndicatorsFast.parabolic_sar(highs, lows, closes),
            'mfi': TechnicalIndicatorsFast.mfi(highs, lows, closes, volumes),
            # Pro-strategy extras
            'obv': TechnicalIndicatorsFast.obv(closes, volumes),
            'donchian': TechnicalIndicatorsFast.donchian(highs, lows),
            'keltner': TechnicalIndicatorsFast.keltner(highs, lows, closes),
            'heikin_ashi': TechnicalIndicatorsFast.heikin_ashi(candles),
            'rsi_history': TechnicalIndicatorsFast.rsi_series(closes),
        }
