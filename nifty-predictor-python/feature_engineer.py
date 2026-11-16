"""
Feature Engineering Module
50+ Technical Indicators for ML Models
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple


class FeatureEngineer:
    """Calculate 50+ technical indicators for ML models"""
    
    def __init__(self):
        self.feature_names = []
    
    def calculate_all_features(self, candles: List[Dict]) -> Tuple[pd.DataFrame, List[str]]:
        """
        Calculate all features from OHLCV candle data
        Returns: (features_df, feature_names)
        """
        if not candles or len(candles) < 50:
            return pd.DataFrame(), []
        
        # Convert to DataFrame
        df = pd.DataFrame(candles)
        
        # Ensure proper column names
        if 'close' not in df.columns:
            df = df.rename(columns={
                'Close': 'close', 'Open': 'open', 
                'High': 'high', 'Low': 'low', 'Volume': 'volume'
            })
        
        # Calculate all indicators
        df = self._add_trend_indicators(df)
        df = self._add_momentum_indicators(df)
        df = self._add_volatility_indicators(df)
        df = self._add_volume_indicators(df)
        df = self._add_price_action_indicators(df)
        df = self._add_divergence_indicators(df)
        
        # Drop rows with NaN (from rolling calculations)
        df = df.dropna()
        
        # Get feature columns (exclude OHLCV and time)
        exclude_cols = ['time', 'open', 'high', 'low', 'close', 'volume', 'datetime']
        feature_cols = [c for c in df.columns if c not in exclude_cols]
        
        self.feature_names = feature_cols
        return df[feature_cols], feature_cols
    
    def _add_trend_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add trend indicators (8)"""
        close = df['close']
        
        # SMA - Simple Moving Averages
        df['sma_5'] = close.rolling(window=5).mean()
        df['sma_10'] = close.rolling(window=10).mean()
        df['sma_20'] = close.rolling(window=20).mean()
        df['sma_50'] = close.rolling(window=50).mean()
        df['sma_200'] = close.rolling(window=min(200, len(df))).mean()
        
        # EMA - Exponential Moving Averages
        df['ema_12'] = close.ewm(span=12, adjust=False).mean()
        df['ema_26'] = close.ewm(span=26, adjust=False).mean()
        df['ema_50'] = close.ewm(span=50, adjust=False).mean()
        
        # Trend strength
        df['trend_strength'] = (df['sma_5'] - df['sma_20']) / df['sma_20'] * 100
        
        return df
    
    def _add_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add momentum indicators (10)"""
        close = df['close']
        
        # MACD
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        df['macd'] = ema12 - ema26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, 0.0001)
        df['rsi'] = 100 - (100 / (1 + rs))
        df['rsi_overbought'] = (df['rsi'] > 70).astype(int)
        df['rsi_oversold'] = (df['rsi'] < 30).astype(int)
        
        # Stochastic RSI
        rsi = df['rsi']
        rsi_min = rsi.rolling(window=14).min()
        rsi_max = rsi.rolling(window=14).max()
        df['stoch_rsi'] = (rsi - rsi_min) / (rsi_max - rsi_min + 0.0001) * 100
        
        # Rate of Change
        df['roc_10'] = ((close - close.shift(10)) / close.shift(10)) * 100
        df['roc_20'] = ((close - close.shift(20)) / close.shift(20)) * 100
        
        # Momentum
        df['momentum'] = close - close.shift(10)
        
        return df
    
    def _add_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volatility indicators (8)"""
        close = df['close']
        high = df['high']
        low = df['low']
        
        # ATR - Average True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=14).mean()
        df['atr_percent'] = (df['atr'] / close) * 100
        
        # Bollinger Bands
        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        df['bb_upper'] = sma20 + (std20 * 2)
        df['bb_lower'] = sma20 - (std20 * 2)
        df['bb_middle'] = sma20
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (close - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'] + 0.0001)
        
        # Historical Volatility
        df['volatility'] = close.pct_change().rolling(window=20).std() * np.sqrt(252) * 100
        
        return df
    
    def _add_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volume indicators (6)"""
        close = df['close']
        volume = df['volume'] if 'volume' in df.columns else pd.Series([0] * len(df))
        
        # Volume SMA
        df['volume_sma'] = volume.rolling(window=20).mean()
        df['volume_ratio'] = volume / (df['volume_sma'] + 0.0001)
        
        # On-Balance Volume
        obv = [0]
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.append(obv[-1] + volume.iloc[i])
            elif close.iloc[i] < close.iloc[i-1]:
                obv.append(obv[-1] - volume.iloc[i])
            else:
                obv.append(obv[-1])
        df['obv'] = obv
        df['obv_sma'] = df['obv'].rolling(window=20).mean()
        
        # Volume signal
        df['volume_signal'] = (df['volume_ratio'] > 1.5).astype(int)
        
        # Price-Volume Trend
        df['pvt'] = ((close - close.shift(1)) / close.shift(1) * volume).cumsum()
        
        return df
    
    def _add_price_action_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add price action indicators (8)"""
        close = df['close']
        high = df['high']
        low = df['low']
        open_price = df['open']
        
        # High-Low Range
        df['hl_range'] = high - low
        df['hl_range_pct'] = df['hl_range'] / close * 100
        
        # Close position in range
        df['close_position'] = (close - low) / (high - low + 0.0001)
        
        # Candle body
        df['candle_body'] = abs(close - open_price)
        df['candle_body_pct'] = df['candle_body'] / close * 100
        
        # Support and Resistance (20-period)
        df['resistance'] = high.rolling(window=20).max()
        df['support'] = low.rolling(window=20).min()
        df['price_to_resistance'] = (df['resistance'] - close) / close * 100
        df['price_to_support'] = (close - df['support']) / close * 100
        
        return df
    
    def _add_divergence_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add divergence indicators (3)"""
        close = df['close']
        
        # Price trend (5-period)
        price_trend = (close - close.shift(5)) / close.shift(5)
        
        # MACD divergence
        macd_trend = (df['macd'] - df['macd'].shift(5)) / (abs(df['macd'].shift(5)) + 0.0001)
        df['macd_divergence'] = (np.sign(price_trend) != np.sign(macd_trend)).astype(int)
        
        # RSI divergence
        rsi_trend = (df['rsi'] - df['rsi'].shift(5)) / (df['rsi'].shift(5) + 0.0001)
        df['rsi_divergence'] = (np.sign(price_trend) != np.sign(rsi_trend)).astype(int)
        
        # Volume divergence
        if 'volume_ratio' in df.columns:
            df['volume_divergence'] = ((price_trend > 0) & (df['volume_ratio'] < 0.8)).astype(int)
        else:
            df['volume_divergence'] = 0
        
        return df
    
    def create_target_variable(self, df: pd.DataFrame, forward_days: int = 2) -> pd.Series:
        """
        Create binary target: 1 if price goes up, 0 if down
        """
        close = df['close'] if 'close' in df.columns else df.iloc[:, 0]
        future_return = (close.shift(-forward_days) - close) / close
        target = (future_return > 0).astype(int)
        return target
    
    def get_latest_features(self, candles: List[Dict]) -> np.ndarray:
        """Get features for the latest candle (for real-time prediction)"""
        features_df, _ = self.calculate_all_features(candles)
        if features_df.empty:
            return np.array([])
        return features_df.iloc[-1].values


# Singleton instance
feature_engineer = FeatureEngineer()
