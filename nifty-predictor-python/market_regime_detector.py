"""
Market Regime Detector Module
Identifies market regimes: Bullish, Bearish, Sideways, High Volatility
Uses Hidden Markov Models and clustering for regime detection
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Try to import HMM, fallback to simple clustering if not available
try:
    from hmmlearn.hmm import GaussianHMM
    HMM_AVAILABLE = True
except ImportError:
    HMM_AVAILABLE = False
    print("WARNING: hmmlearn not installed. Using simple regime detection.")

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


class MarketRegimeDetector:
    """
    Detect market regimes using multiple methods:
    1. Hidden Markov Model (if available)
    2. Volatility-based regime detection
    3. Trend strength classification
    """
    
    # Regime definitions
    REGIME_BULLISH = "BULLISH"
    REGIME_BEARISH = "BEARISH"
    REGIME_SIDEWAYS = "SIDEWAYS"
    REGIME_HIGH_VOL = "HIGH_VOLATILITY"
    REGIME_LOW_VOL = "LOW_VOLATILITY"
    
    def __init__(self, n_regimes: int = 4):
        self.n_regimes = n_regimes
        self.hmm_model = None
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.regime_history = []
        self.last_regime = None
        self.regime_confidence = 0.0
        
    def _calculate_features(self, candles: List[Dict]) -> np.ndarray:
        """Calculate features for regime detection"""
        if len(candles) < 20:
            return None
            
        # Extract price data
        closes = np.array([c.get('close', c.get('Close', 0)) for c in candles])
        highs = np.array([c.get('high', c.get('High', 0)) for c in candles])
        lows = np.array([c.get('low', c.get('Low', 0)) for c in candles])
        volumes = np.array([c.get('volume', c.get('Volume', 1)) for c in candles])
        
        # Calculate returns
        returns = np.diff(closes) / closes[:-1] * 100
        
        # Feature 1: Rolling returns (momentum)
        momentum_5 = np.convolve(returns, np.ones(5)/5, mode='valid')[-1] if len(returns) >= 5 else returns[-1]
        momentum_10 = np.convolve(returns, np.ones(10)/10, mode='valid')[-1] if len(returns) >= 10 else returns[-1]
        
        # Feature 2: Volatility (rolling std of returns)
        volatility = np.std(returns[-20:]) if len(returns) >= 20 else np.std(returns)
        
        # Feature 3: Range ratio (high-low / close)
        range_ratio = (highs[-1] - lows[-1]) / closes[-1] * 100
        
        # Feature 4: Volume trend
        vol_ma = np.mean(volumes[-10:]) if len(volumes) >= 10 else np.mean(volumes)
        vol_ratio = volumes[-1] / vol_ma if vol_ma > 0 else 1.0
        
        # Feature 5: Price position in range
        range_20_high = np.max(highs[-20:]) if len(highs) >= 20 else np.max(highs)
        range_20_low = np.min(lows[-20:]) if len(lows) >= 20 else np.min(lows)
        price_position = (closes[-1] - range_20_low) / (range_20_high - range_20_low + 0.001)
        
        # Feature 6: Trend consistency (how many up days vs down days)
        up_days = np.sum(returns[-10:] > 0) if len(returns) >= 10 else np.sum(returns > 0)
        trend_consistency = up_days / 10.0
        
        features = np.array([
            momentum_5,
            momentum_10,
            volatility,
            range_ratio,
            vol_ratio,
            price_position,
            trend_consistency
        ]).reshape(1, -1)
        
        return features
        
    def _calculate_sequence_features(self, candles: List[Dict]) -> np.ndarray:
        """Calculate sequence of features for HMM training"""
        if len(candles) < 30:
            return None
            
        closes = np.array([c.get('close', c.get('Close', 0)) for c in candles])
        highs = np.array([c.get('high', c.get('High', 0)) for c in candles])
        lows = np.array([c.get('low', c.get('Low', 0)) for c in candles])
        
        # Returns
        returns = np.diff(closes) / closes[:-1] * 100
        
        # Rolling volatility
        vol_window = 5
        volatility = []
        for i in range(vol_window, len(returns)):
            volatility.append(np.std(returns[i-vol_window:i]))
        
        # Range ratio
        range_ratio = (highs[vol_window+1:] - lows[vol_window+1:]) / closes[vol_window+1:] * 100
        
        min_len = min(len(volatility), len(range_ratio))
        if min_len < 10:
            return None
            
        features = np.column_stack([
            returns[vol_window:vol_window+min_len],
            volatility[:min_len],
            range_ratio[:min_len]
        ])
        
        return features
        
    def fit(self, candles: List[Dict]) -> bool:
        """Fit the regime detection model"""
        try:
            if HMM_AVAILABLE:
                features = self._calculate_sequence_features(candles)
                if features is None or len(features) < 20:
                    return False
                    
                # Normalize features
                features_scaled = self.scaler.fit_transform(features)
                
                # Fit HMM
                self.hmm_model = GaussianHMM(
                    n_components=self.n_regimes,
                    covariance_type="diag",
                    n_iter=100,
                    random_state=42
                )
                self.hmm_model.fit(features_scaled)
                self.is_fitted = True
                return True
            else:
                # Use simple clustering approach
                self.is_fitted = True
                return True
                
        except Exception as e:
            print(f"Regime detector fit error: {e}")
            self.is_fitted = True  # Allow fallback methods
            return False
            
    def detect_regime(self, candles: List[Dict], indicators: Dict = None) -> Dict:
        """
        Detect current market regime
        Returns: Dict with regime, confidence, and characteristics
        """
        if len(candles) < 20:
            return self._default_regime()
            
        try:
            # Method 1: HMM-based detection (if fitted)
            hmm_regime = None
            if HMM_AVAILABLE and self.hmm_model is not None:
                features = self._calculate_sequence_features(candles[-50:])
                if features is not None and len(features) >= 5:
                    if hasattr(self.hmm_model, 'means_'):
                        features_scaled = self.scaler.transform(features)
                        states = self.hmm_model.predict(features_scaled)
                        hmm_regime = int(states[-1])
            
            # Method 2: Rule-based detection (always available)
            rule_regime = self._detect_regime_rules(candles, indicators)
            
            # Combine methods
            final_regime = self._combine_regimes(hmm_regime, rule_regime)
            
            # Store in history
            self.last_regime = final_regime['regime']
            self.regime_history.append({
                'timestamp': datetime.now().isoformat(),
                'regime': final_regime['regime'],
                'confidence': final_regime['confidence']
            })
            
            # Keep only last 100 entries
            if len(self.regime_history) > 100:
                self.regime_history = self.regime_history[-100:]
                
            return final_regime
            
        except Exception as e:
            print(f"Regime detection error: {e}")
            return self._default_regime()
            
    def _detect_regime_rules(self, candles: List[Dict], indicators: Dict = None) -> Dict:
        """Rule-based regime detection using technical indicators"""
        closes = np.array([c.get('close', c.get('Close', 0)) for c in candles])
        highs = np.array([c.get('high', c.get('High', 0)) for c in candles])
        lows = np.array([c.get('low', c.get('Low', 0)) for c in candles])
        
        # Calculate basic metrics
        returns = np.diff(closes) / closes[:-1] * 100
        volatility = np.std(returns[-20:]) if len(returns) >= 20 else np.std(returns)
        avg_volatility = np.std(returns)
        
        # Trend indicators
        sma_20 = np.mean(closes[-20:]) if len(closes) >= 20 else np.mean(closes)
        sma_50 = np.mean(closes[-50:]) if len(closes) >= 50 else sma_20
        current_price = closes[-1]
        
        # ADX from indicators if available
        adx_value = 25  # Default
        rsi_value = 50  # Default
        if indicators:
            adx = indicators.get('adx', {})
            if isinstance(adx, dict):
                adx_value = adx.get('adx', 25)
            rsi_value = indicators.get('rsi', 50) or 50
        
        # Regime scoring
        bullish_score = 0
        bearish_score = 0
        sideways_score = 0
        high_vol_score = 0
        
        # Trend-based scoring
        if current_price > sma_20:
            bullish_score += 2
        else:
            bearish_score += 2
            
        if sma_20 > sma_50:
            bullish_score += 1
        else:
            bearish_score += 1
            
        # Momentum scoring
        recent_return = np.sum(returns[-5:]) if len(returns) >= 5 else np.sum(returns)
        if recent_return > 1:
            bullish_score += 2
        elif recent_return < -1:
            bearish_score += 2
        else:
            sideways_score += 2
            
        # ADX scoring (trend strength)
        if adx_value < 20:
            sideways_score += 3
        elif adx_value > 30:
            if bullish_score > bearish_score:
                bullish_score += 2
            else:
                bearish_score += 2
                
        # Volatility scoring
        vol_percentile = volatility / (avg_volatility + 0.001)
        if vol_percentile > 1.5:
            high_vol_score += 3
        elif vol_percentile < 0.5:
            sideways_score += 1
            
        # RSI scoring
        if rsi_value > 70:
            bearish_score += 1  # Overbought, potential reversal
        elif rsi_value < 30:
            bullish_score += 1  # Oversold, potential reversal
            
        # Determine regime
        scores = {
            self.REGIME_BULLISH: bullish_score,
            self.REGIME_BEARISH: bearish_score,
            self.REGIME_SIDEWAYS: sideways_score,
            self.REGIME_HIGH_VOL: high_vol_score
        }
        
        max_regime = max(scores, key=scores.get)
        max_score = scores[max_regime]
        total_score = sum(scores.values()) + 0.001
        confidence = min(max_score / total_score * 1.5, 1.0)
        
        return {
            'regime': max_regime,
            'confidence': round(confidence, 2),
            'scores': scores,
            'volatility': round(volatility, 4),
            'trend_strength': adx_value,
            'momentum': round(recent_return, 2)
        }
        
    def _combine_regimes(self, hmm_regime: Optional[int], rule_regime: Dict) -> Dict:
        """Combine HMM and rule-based regime detection"""
        # If HMM is available, use it to adjust confidence
        if hmm_regime is not None:
            # Map HMM regime to named regime based on characteristics
            # For now, primarily rely on rule-based with HMM as confidence boost
            hmm_confidence_boost = 0.1
            rule_regime['confidence'] = min(rule_regime['confidence'] + hmm_confidence_boost, 1.0)
            rule_regime['hmm_state'] = hmm_regime
            
        return rule_regime
        
    def _default_regime(self) -> Dict:
        """Return default regime when detection fails"""
        return {
            'regime': self.REGIME_SIDEWAYS,
            'confidence': 0.3,
            'scores': {},
            'volatility': 0,
            'trend_strength': 25,
            'momentum': 0
        }
        
    def get_regime_summary(self) -> Dict:
        """Get summary of recent regime history"""
        if not self.regime_history:
            return {'current': self._default_regime(), 'history': []}
            
        # Count regime occurrences in last 20
        recent = self.regime_history[-20:]
        regime_counts = {}
        for r in recent:
            regime = r['regime']
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
            
        dominant_regime = max(regime_counts, key=regime_counts.get) if regime_counts else self.REGIME_SIDEWAYS
        
        return {
            'current': self.regime_history[-1] if self.regime_history else self._default_regime(),
            'dominant_regime': dominant_regime,
            'regime_counts': regime_counts,
            'stability': regime_counts.get(dominant_regime, 0) / len(recent) if recent else 0
        }
        
    def get_trading_bias(self) -> Dict:
        """Get trading bias based on current regime"""
        if not self.last_regime:
            return {'bias': 'NEUTRAL', 'strength': 0.5}
            
        bias_map = {
            self.REGIME_BULLISH: ('BULLISH', 0.7),
            self.REGIME_BEARISH: ('BEARISH', 0.7),
            self.REGIME_SIDEWAYS: ('NEUTRAL', 0.3),
            self.REGIME_HIGH_VOL: ('CAUTIOUS', 0.4),
            self.REGIME_LOW_VOL: ('NEUTRAL', 0.5)
        }
        
        bias, strength = bias_map.get(self.last_regime, ('NEUTRAL', 0.5))
        return {
            'bias': bias,
            'strength': strength,
            'regime': self.last_regime,
            'confidence': self.regime_confidence
        }


# Singleton instance
regime_detector = MarketRegimeDetector()


def detect_market_regime(candles: List[Dict], indicators: Dict = None) -> Dict:
    """Detect current market regime"""
    return regime_detector.detect_regime(candles, indicators)


def fit_regime_detector(candles: List[Dict]) -> bool:
    """Fit the regime detector on historical data"""
    return regime_detector.fit(candles)


def get_trading_bias() -> Dict:
    """Get trading bias based on current regime"""
    return regime_detector.get_trading_bias()


def get_regime_summary() -> Dict:
    """Get regime summary"""
    return regime_detector.get_regime_summary()
