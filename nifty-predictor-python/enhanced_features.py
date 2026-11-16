"""
Enhanced Features Module
Advanced feature engineering for ML models
Includes: Lag features, cross-asset correlations, time-based features, volume profile
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Try to import pandas-ta for additional indicators
try:
    import pandas_ta as pta
    PANDAS_TA_AVAILABLE = True
except ImportError:
    PANDAS_TA_AVAILABLE = False
    print("WARNING: pandas-ta not installed. Using basic indicators.")

# Try to import ta library
try:
    import ta
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False
    print("WARNING: ta library not installed. Using basic indicators.")


class EnhancedFeatureEngineer:
    """
    Advanced feature engineering for ML models
    Generates 100+ features for high-accuracy prediction
    """
    
    def __init__(self):
        self.feature_names = []
        self.last_features = None
        
    def calculate_all_features(self, candles: List[Dict], 
                                indicators: Dict = None,
                                option_data: Dict = None) -> Tuple[np.ndarray, List[str]]:
        """
        Calculate comprehensive feature set for ML models
        
        Returns:
            Tuple of (feature_array, feature_names)
        """
        if len(candles) < 30:
            return self._default_features()
            
        # Convert to DataFrame
        df = self._candles_to_df(candles)
        
        features = {}
        
        # 1. Price-based features (15)
        features.update(self._price_features(df))
        
        # 2. Returns features (12)
        features.update(self._returns_features(df))
        
        # 3. Volatility features (10)
        features.update(self._volatility_features(df))
        
        # 4. Volume features (8)
        features.update(self._volume_features(df))
        
        # 5. Momentum features (15)
        features.update(self._momentum_features(df))
        
        # 6. Trend features (10)
        features.update(self._trend_features(df))
        
        # 7. Time-based features (8)
        features.update(self._time_features(df))
        
        # 8. Pattern features (5)
        features.update(self._pattern_features(df))
        
        # 9. Indicator-derived features (if provided)
        if indicators:
            features.update(self._indicator_features(indicators))
            
        # 10. Option-derived features (if provided)
        if option_data:
            features.update(self._option_features(option_data))
            
        # Convert to arrays
        feature_names = list(features.keys())
        feature_values = np.array([features[k] for k in feature_names])
        
        # Handle NaN/Inf
        feature_values = np.nan_to_num(feature_values, nan=0, posinf=0, neginf=0)
        
        self.feature_names = feature_names
        self.last_features = features
        
        return feature_values, feature_names
        
    def _candles_to_df(self, candles: List[Dict]) -> pd.DataFrame:
        """Convert candles to DataFrame"""
        df = pd.DataFrame(candles)
        
        # Standardize column names
        column_map = {
            'open': 'Open', 'high': 'High', 'low': 'Low', 
            'close': 'Close', 'volume': 'Volume'
        }
        
        for old, new in column_map.items():
            if old in df.columns and new not in df.columns:
                df[new] = df[old]
                
        # Ensure numeric
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        # Fill NaN with forward fill
        df = df.ffill().bfill()
        
        return df
        
    def _price_features(self, df: pd.DataFrame) -> Dict:
        """Price-based features"""
        features = {}
        
        close = df['Close'].values
        high = df['High'].values
        low = df['Low'].values
        open_ = df['Open'].values
        
        # Current price position
        features['price_position_20'] = (close[-1] - low[-20:].min()) / (high[-20:].max() - low[-20:].min() + 0.001)
        features['price_position_50'] = (close[-1] - low[-50:].min()) / (high[-50:].max() - low[-50:].min() + 0.001) if len(close) >= 50 else features['price_position_20']
        
        # Distance from key MAs
        sma_20 = np.mean(close[-20:])
        sma_50 = np.mean(close[-50:]) if len(close) >= 50 else sma_20
        
        features['dist_from_sma20'] = (close[-1] - sma_20) / sma_20 * 100
        features['dist_from_sma50'] = (close[-1] - sma_50) / sma_50 * 100
        
        # Price range features
        features['daily_range'] = (high[-1] - low[-1]) / close[-1] * 100
        features['avg_range_5'] = np.mean((high[-5:] - low[-5:]) / close[-5:]) * 100
        features['range_expansion'] = features['daily_range'] / (features['avg_range_5'] + 0.001)
        
        # Gap features
        if len(close) >= 2:
            features['gap'] = (open_[-1] - close[-2]) / close[-2] * 100
        else:
            features['gap'] = 0
            
        # Candle body features
        body = close[-1] - open_[-1]
        full_range = high[-1] - low[-1] + 0.001
        features['body_ratio'] = abs(body) / full_range
        features['upper_shadow'] = (high[-1] - max(open_[-1], close[-1])) / full_range
        features['lower_shadow'] = (min(open_[-1], close[-1]) - low[-1]) / full_range
        
        # Higher highs / Lower lows
        features['hh_count'] = sum(1 for i in range(1, min(10, len(high))) if high[-i] > high[-i-1]) if len(high) > 10 else 0
        features['ll_count'] = sum(1 for i in range(1, min(10, len(low))) if low[-i] < low[-i-1]) if len(low) > 10 else 0
        
        return features
        
    def _returns_features(self, df: pd.DataFrame) -> Dict:
        """Returns-based features"""
        features = {}
        
        close = df['Close'].values
        returns = np.diff(close) / close[:-1] * 100
        
        # Various return periods
        features['return_1'] = returns[-1] if len(returns) >= 1 else 0
        features['return_3'] = np.sum(returns[-3:]) if len(returns) >= 3 else 0
        features['return_5'] = np.sum(returns[-5:]) if len(returns) >= 5 else 0
        features['return_10'] = np.sum(returns[-10:]) if len(returns) >= 10 else 0
        features['return_20'] = np.sum(returns[-20:]) if len(returns) >= 20 else 0
        
        # Return statistics
        features['return_mean_5'] = np.mean(returns[-5:]) if len(returns) >= 5 else 0
        features['return_std_5'] = np.std(returns[-5:]) if len(returns) >= 5 else 0
        features['return_skew'] = self._skewness(returns[-20:]) if len(returns) >= 20 else 0
        
        # Positive/Negative returns ratio
        pos_returns = sum(1 for r in returns[-10:] if r > 0) if len(returns) >= 10 else 0
        features['pos_return_ratio'] = pos_returns / 10
        
        # Max/Min returns
        features['max_return_10'] = max(returns[-10:]) if len(returns) >= 10 else 0
        features['min_return_10'] = min(returns[-10:]) if len(returns) >= 10 else 0
        
        return features
        
    def _volatility_features(self, df: pd.DataFrame) -> Dict:
        """Volatility-based features"""
        features = {}
        
        close = df['Close'].values
        high = df['High'].values
        low = df['Low'].values
        
        returns = np.diff(close) / close[:-1] * 100
        
        # Historical volatility
        features['volatility_5'] = np.std(returns[-5:]) if len(returns) >= 5 else 0
        features['volatility_10'] = np.std(returns[-10:]) if len(returns) >= 10 else 0
        features['volatility_20'] = np.std(returns[-20:]) if len(returns) >= 20 else 0
        
        # Volatility ratio
        features['vol_ratio_5_20'] = features['volatility_5'] / (features['volatility_20'] + 0.001)
        
        # ATR-based
        tr = []
        for i in range(1, len(close)):
            tr.append(max(
                high[i] - low[i],
                abs(high[i] - close[i-1]),
                abs(low[i] - close[i-1])
            ))
        features['atr_14'] = np.mean(tr[-14:]) if len(tr) >= 14 else np.mean(tr) if tr else 0
        features['atr_pct'] = features['atr_14'] / close[-1] * 100
        
        # Bollinger Band width
        sma_20 = np.mean(close[-20:])
        std_20 = np.std(close[-20:])
        features['bb_width'] = (2 * 2 * std_20) / sma_20 * 100
        
        # Parkinson volatility
        hl_ratio = np.log(high[-20:] / low[-20:])
        features['parkinson_vol'] = np.sqrt(np.sum(hl_ratio ** 2) / (4 * 20 * np.log(2)))
        
        return features
        
    def _volume_features(self, df: pd.DataFrame) -> Dict:
        """Volume-based features"""
        features = {}
        
        volume = df['Volume'].values
        close = df['Close'].values
        
        if np.sum(volume) == 0:
            # No volume data
            return {
                'volume_sma_ratio': 1, 'volume_trend': 0, 'volume_volatility': 0,
                'obv_slope': 0, 'volume_price_trend': 0, 'climax_volume': 0,
                'accumulation': 0, 'volume_breakout': 0
            }
        
        # Volume ratios
        vol_sma_20 = np.mean(volume[-20:])
        features['volume_sma_ratio'] = volume[-1] / (vol_sma_20 + 1)
        
        # Volume trend
        vol_sma_5 = np.mean(volume[-5:])
        vol_sma_10 = np.mean(volume[-10:]) if len(volume) >= 10 else vol_sma_5
        features['volume_trend'] = (vol_sma_5 - vol_sma_10) / (vol_sma_10 + 1)
        
        # Volume volatility
        features['volume_volatility'] = np.std(volume[-10:]) / (np.mean(volume[-10:]) + 1) if len(volume) >= 10 else 0
        
        # OBV slope
        obv = [0]
        for i in range(1, len(close)):
            if close[i] > close[i-1]:
                obv.append(obv[-1] + volume[i])
            elif close[i] < close[i-1]:
                obv.append(obv[-1] - volume[i])
            else:
                obv.append(obv[-1])
        features['obv_slope'] = (obv[-1] - obv[-5]) / (abs(obv[-5]) + 1) if len(obv) >= 5 else 0
        
        # Volume-price trend
        price_change = close[-1] - close[-5] if len(close) >= 5 else 0
        vol_change = volume[-1] - np.mean(volume[-5:]) if len(volume) >= 5 else 0
        features['volume_price_trend'] = 1 if (price_change > 0 and vol_change > 0) or (price_change < 0 and vol_change < 0) else -1
        
        # Climax volume detection
        features['climax_volume'] = 1 if volume[-1] > vol_sma_20 * 2 else 0
        
        # Accumulation/Distribution
        mfm = ((close[-1] - low[-1]) - (high[-1] - close[-1])) / (high[-1] - low[-1] + 0.001)
        features['accumulation'] = mfm * volume[-1] / (vol_sma_20 + 1)
        
        # Volume breakout
        features['volume_breakout'] = 1 if volume[-1] > max(volume[-20:-1]) else 0 if len(volume) > 20 else 0
        
        return features
        
    def _momentum_features(self, df: pd.DataFrame) -> Dict:
        """Momentum-based features"""
        features = {}
        
        close = df['Close'].values
        high = df['High'].values
        low = df['Low'].values
        
        # RSI
        features['rsi_14'] = self._calculate_rsi(close, 14)
        features['rsi_7'] = self._calculate_rsi(close, 7)
        features['rsi_divergence'] = features['rsi_14'] - features['rsi_7']
        
        # Stochastic
        stoch = self._calculate_stochastic(high, low, close)
        features['stoch_k'] = stoch['k']
        features['stoch_d'] = stoch['d']
        features['stoch_divergence'] = stoch['k'] - stoch['d']
        
        # Rate of Change
        features['roc_5'] = (close[-1] - close[-6]) / close[-6] * 100 if len(close) > 6 else 0
        features['roc_10'] = (close[-1] - close[-11]) / close[-11] * 100 if len(close) > 11 else 0
        
        # Momentum
        features['momentum_5'] = close[-1] - close[-6] if len(close) > 6 else 0
        features['momentum_10'] = close[-1] - close[-11] if len(close) > 11 else 0
        
        # Williams %R
        features['williams_r'] = self._calculate_williams_r(high, low, close)
        
        # CCI
        features['cci'] = self._calculate_cci(high, low, close)
        
        # MFI approximation
        features['mfi'] = self._approximate_mfi(high, low, close, df['Volume'].values)
        
        return features
        
    def _trend_features(self, df: pd.DataFrame) -> Dict:
        """Trend-based features"""
        features = {}
        
        close = df['Close'].values
        high = df['High'].values
        low = df['Low'].values
        
        # Moving average crossovers
        ema_9 = self._calculate_ema(close, 9)
        ema_21 = self._calculate_ema(close, 21)
        sma_50 = np.mean(close[-50:]) if len(close) >= 50 else np.mean(close)
        
        features['ema_cross'] = 1 if ema_9 > ema_21 else -1
        features['price_above_ema9'] = 1 if close[-1] > ema_9 else 0
        features['price_above_ema21'] = 1 if close[-1] > ema_21 else 0
        features['price_above_sma50'] = 1 if close[-1] > sma_50 else 0
        
        # MACD
        macd = self._calculate_macd(close)
        features['macd_line'] = macd['macd']
        features['macd_signal'] = macd['signal']
        features['macd_histogram'] = macd['histogram']
        
        # ADX approximation
        features['adx'] = self._approximate_adx(high, low, close)
        
        # Trend strength
        features['trend_strength'] = abs(features['ema_cross']) * features['adx'] / 100
        
        return features
        
    def _time_features(self, df: pd.DataFrame) -> Dict:
        """Time-based features"""
        features = {}
        
        now = datetime.now()
        
        # Hour of day (normalized)
        features['hour_sin'] = np.sin(2 * np.pi * now.hour / 24)
        features['hour_cos'] = np.cos(2 * np.pi * now.hour / 24)
        
        # Day of week (normalized)
        features['dow_sin'] = np.sin(2 * np.pi * now.weekday() / 5)
        features['dow_cos'] = np.cos(2 * np.pi * now.weekday() / 5)
        
        # Is market opening hour
        features['is_opening'] = 1 if 9 <= now.hour < 10 else 0
        
        # Is market closing hour
        features['is_closing'] = 1 if 15 <= now.hour < 16 else 0
        
        # Day of month (for expiry proximity)
        features['dom_normalized'] = now.day / 31
        
        # Is Thursday (expiry day)
        features['is_expiry_day'] = 1 if now.weekday() == 3 else 0
        
        return features
        
    def _pattern_features(self, df: pd.DataFrame) -> Dict:
        """Candlestick pattern features"""
        features = {}
        
        close = df['Close'].values
        open_ = df['Open'].values
        high = df['High'].values
        low = df['Low'].values
        
        # Doji detection
        body = abs(close[-1] - open_[-1])
        range_ = high[-1] - low[-1]
        features['is_doji'] = 1 if body / (range_ + 0.001) < 0.1 else 0
        
        # Hammer/Shooting Star
        upper_shadow = high[-1] - max(open_[-1], close[-1])
        lower_shadow = min(open_[-1], close[-1]) - low[-1]
        features['is_hammer'] = 1 if lower_shadow > body * 2 and upper_shadow < body else 0
        features['is_shooting_star'] = 1 if upper_shadow > body * 2 and lower_shadow < body else 0
        
        # Engulfing patterns (simplified)
        if len(close) >= 2:
            prev_body = close[-2] - open_[-2]
            curr_body = close[-1] - open_[-1]
            features['is_bullish_engulf'] = 1 if prev_body < 0 and curr_body > 0 and abs(curr_body) > abs(prev_body) else 0
            features['is_bearish_engulf'] = 1 if prev_body > 0 and curr_body < 0 and abs(curr_body) > abs(prev_body) else 0
        else:
            features['is_bullish_engulf'] = 0
            features['is_bearish_engulf'] = 0
            
        return features
        
    def _indicator_features(self, indicators: Dict) -> Dict:
        """Extract features from pre-computed indicators"""
        features = {}
        
        # RSI
        rsi = indicators.get('rsi')
        if rsi:
            features['ind_rsi'] = rsi
            features['ind_rsi_overbought'] = 1 if rsi > 70 else 0
            features['ind_rsi_oversold'] = 1 if rsi < 30 else 0
            
        # MACD
        macd = indicators.get('macd', {})
        if isinstance(macd, dict):
            features['ind_macd'] = macd.get('macd', 0)
            features['ind_macd_signal'] = macd.get('signal', 0)
            features['ind_macd_hist'] = macd.get('histogram', 0)
            
        # ADX
        adx = indicators.get('adx', {})
        if isinstance(adx, dict):
            features['ind_adx'] = adx.get('adx', 25)
            features['ind_plus_di'] = adx.get('plus_di', 25)
            features['ind_minus_di'] = adx.get('minus_di', 25)
            features['ind_di_diff'] = features.get('ind_plus_di', 25) - features.get('ind_minus_di', 25)
            
        # Supertrend
        supertrend = indicators.get('supertrend', {})
        if isinstance(supertrend, dict):
            features['ind_supertrend_signal'] = 1 if supertrend.get('trend') == 'UP' else -1
            
        # Bollinger Bands
        bb = indicators.get('bollinger', {})
        if isinstance(bb, dict):
            upper = bb.get('upper', 0)
            lower = bb.get('lower', 0)
            middle = bb.get('middle', 0)
            if upper and lower and middle:
                features['ind_bb_position'] = (indicators.get('current_price', middle) - lower) / (upper - lower + 0.001)
                
        return features
        
    def _option_features(self, option_data: Dict) -> Dict:
        """Extract features from option chain data"""
        features = {}
        
        features['opt_pcr'] = option_data.get('pcr', 1.0)
        features['opt_iv'] = option_data.get('iv', 15)
        features['opt_iv_percentile'] = option_data.get('iv_percentile', 50)
        
        # OI features
        features['opt_ce_oi'] = option_data.get('ce_oi', 0)
        features['opt_pe_oi'] = option_data.get('pe_oi', 0)
        features['opt_oi_ratio'] = features['opt_pe_oi'] / (features['opt_ce_oi'] + 1)
        
        # Max pain distance
        max_pain = option_data.get('max_pain', 0)
        current = option_data.get('current_price', max_pain)
        if max_pain > 0:
            features['opt_mp_distance'] = (current - max_pain) / max_pain * 100
        else:
            features['opt_mp_distance'] = 0
            
        return features
        
    # Helper calculation methods
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        if len(prices) < period + 1:
            return 50
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
        
    def _calculate_stochastic(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, k_period: int = 14, d_period: int = 3) -> Dict:
        if len(close) < k_period:
            return {'k': 50, 'd': 50}
        lowest_low = np.min(low[-k_period:])
        highest_high = np.max(high[-k_period:])
        k = (close[-1] - lowest_low) / (highest_high - lowest_low + 0.001) * 100
        # Simplified D
        d = k  # Would need smoothing for proper D
        return {'k': k, 'd': d}
        
    def _calculate_williams_r(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float:
        if len(close) < period:
            return -50
        highest_high = np.max(high[-period:])
        lowest_low = np.min(low[-period:])
        return (highest_high - close[-1]) / (highest_high - lowest_low + 0.001) * -100
        
    def _calculate_cci(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 20) -> float:
        if len(close) < period:
            return 0
        tp = (high + low + close) / 3
        sma_tp = np.mean(tp[-period:])
        mean_dev = np.mean(np.abs(tp[-period:] - sma_tp))
        return (tp[-1] - sma_tp) / (0.015 * mean_dev + 0.001)
        
    def _approximate_mfi(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, volume: np.ndarray, period: int = 14) -> float:
        if len(close) < period or np.sum(volume) == 0:
            return 50
        tp = (high + low + close) / 3
        mf = tp * volume
        pos_mf = sum(mf[i] for i in range(-period, 0) if tp[i] > tp[i-1])
        neg_mf = sum(mf[i] for i in range(-period, 0) if tp[i] < tp[i-1])
        if neg_mf == 0:
            return 100
        mfi = 100 - (100 / (1 + pos_mf / neg_mf))
        return mfi
        
    def _calculate_ema(self, prices: np.ndarray, period: int) -> float:
        if len(prices) < period:
            return prices[-1]
        alpha = 2 / (period + 1)
        ema = prices[-period]
        for i in range(-period + 1, 0):
            ema = alpha * prices[i] + (1 - alpha) * ema
        return ema
        
    def _calculate_macd(self, prices: np.ndarray) -> Dict:
        ema_12 = self._calculate_ema(prices, 12)
        ema_26 = self._calculate_ema(prices, 26)
        macd_line = ema_12 - ema_26
        signal = macd_line * 0.9  # Simplified
        return {
            'macd': macd_line,
            'signal': signal,
            'histogram': macd_line - signal
        }
        
    def _approximate_adx(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float:
        if len(close) < period + 1:
            return 25
        # Simplified ADX approximation
        tr = []
        plus_dm = []
        minus_dm = []
        for i in range(1, len(close)):
            tr.append(max(high[i] - low[i], abs(high[i] - close[i-1]), abs(low[i] - close[i-1])))
            up_move = high[i] - high[i-1]
            down_move = low[i-1] - low[i]
            plus_dm.append(up_move if up_move > down_move and up_move > 0 else 0)
            minus_dm.append(down_move if down_move > up_move and down_move > 0 else 0)
        
        atr = np.mean(tr[-period:])
        plus_di = np.mean(plus_dm[-period:]) / (atr + 0.001) * 100
        minus_di = np.mean(minus_dm[-period:]) / (atr + 0.001) * 100
        dx = abs(plus_di - minus_di) / (plus_di + minus_di + 0.001) * 100
        return dx
        
    def _skewness(self, data: np.ndarray) -> float:
        if len(data) < 3:
            return 0
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0
        return np.mean(((data - mean) / std) ** 3)
        
    def _default_features(self) -> Tuple[np.ndarray, List[str]]:
        """Return default features when calculation fails"""
        default_names = ['default_feature']
        default_values = np.array([0])
        return default_values, default_names
        
    def get_feature_importance_groups(self) -> Dict[str, List[str]]:
        """Return feature names grouped by category"""
        return {
            'price': [n for n in self.feature_names if n.startswith(('price', 'dist', 'gap', 'body', 'shadow'))],
            'returns': [n for n in self.feature_names if n.startswith('return')],
            'volatility': [n for n in self.feature_names if n.startswith(('vol', 'atr', 'bb', 'parkinson'))],
            'volume': [n for n in self.feature_names if n.startswith(('volume', 'obv', 'climax', 'accum'))],
            'momentum': [n for n in self.feature_names if n.startswith(('rsi', 'stoch', 'roc', 'momentum', 'williams', 'cci', 'mfi'))],
            'trend': [n for n in self.feature_names if n.startswith(('ema', 'macd', 'adx', 'trend'))],
            'time': [n for n in self.feature_names if n.startswith(('hour', 'dow', 'is_', 'dom'))],
            'pattern': [n for n in self.feature_names if n.startswith('is_')],
            'indicator': [n for n in self.feature_names if n.startswith('ind_')],
            'option': [n for n in self.feature_names if n.startswith('opt_')]
        }


# Singleton instance
enhanced_feature_engineer = EnhancedFeatureEngineer()


def get_enhanced_features(candles: List[Dict], 
                          indicators: Dict = None,
                          option_data: Dict = None) -> Tuple[np.ndarray, List[str]]:
    """Get enhanced feature set for ML models"""
    return enhanced_feature_engineer.calculate_all_features(candles, indicators, option_data)


def get_feature_names() -> List[str]:
    """Get list of feature names"""
    return enhanced_feature_engineer.feature_names
