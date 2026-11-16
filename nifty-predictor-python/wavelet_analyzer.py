"""
Wavelet Analyzer Module
Multi-scale analysis using Wavelet Transform for noise reduction and trend extraction
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Try to import PyWavelets
try:
    import pywt
    PYWT_AVAILABLE = True
except ImportError:
    PYWT_AVAILABLE = False
    print("WARNING: PyWavelets not installed. Using simple moving average filtering.")


class WaveletAnalyzer:
    """
    Wavelet-based signal analysis for financial time series:
    1. Multi-scale decomposition
    2. Noise reduction / denoising
    3. Trend extraction
    4. Volatility estimation at different scales
    """
    
    def __init__(self, wavelet: str = 'db4', levels: int = 4):
        """
        Initialize wavelet analyzer
        
        Args:
            wavelet: Wavelet type ('db4' works well for financial data)
            levels: Number of decomposition levels
        """
        self.wavelet = wavelet
        self.levels = levels
        self.last_decomposition = None
        self.trend_signal = None
        self.noise_signal = None
        
    def decompose(self, prices: np.ndarray) -> Dict:
        """
        Perform wavelet decomposition on price series
        
        Returns:
            Dict with approximation (trend) and detail (noise) coefficients
        """
        if not PYWT_AVAILABLE:
            return self._simple_decompose(prices)
            
        if len(prices) < 2 ** self.levels:
            # Not enough data for decomposition
            return self._simple_decompose(prices)
            
        try:
            # Perform wavelet decomposition
            coeffs = pywt.wavedec(prices, self.wavelet, level=self.levels)
            
            # coeffs[0] is approximation (low frequency / trend)
            # coeffs[1:] are details (high frequency / noise)
            
            self.last_decomposition = coeffs
            
            # Reconstruct trend (using only approximation)
            trend_coeffs = [coeffs[0]] + [np.zeros_like(c) for c in coeffs[1:]]
            trend = pywt.waverec(trend_coeffs, self.wavelet)[:len(prices)]
            
            # Reconstruct noise (using only details)
            noise_coeffs = [np.zeros_like(coeffs[0])] + coeffs[1:]
            noise = pywt.waverec(noise_coeffs, self.wavelet)[:len(prices)]
            
            self.trend_signal = trend
            self.noise_signal = noise
            
            return {
                'trend': trend,
                'noise': noise,
                'coefficients': coeffs,
                'levels': self.levels,
                'wavelet': self.wavelet
            }
            
        except Exception as e:
            print(f"Wavelet decomposition error: {e}")
            return self._simple_decompose(prices)
            
    def _simple_decompose(self, prices: np.ndarray) -> Dict:
        """Simple fallback decomposition using moving averages"""
        if len(prices) < 5:
            return {
                'trend': prices,
                'noise': np.zeros_like(prices),
                'levels': 0,
                'wavelet': 'simple_ma'
            }
            
        # Use EMA for trend
        alpha = 2 / (min(20, len(prices)) + 1)
        trend = np.zeros_like(prices, dtype=float)
        trend[0] = prices[0]
        for i in range(1, len(prices)):
            trend[i] = alpha * prices[i] + (1 - alpha) * trend[i-1]
            
        noise = prices - trend
        
        self.trend_signal = trend
        self.noise_signal = noise
        
        return {
            'trend': trend,
            'noise': noise,
            'levels': 0,
            'wavelet': 'simple_ma'
        }
        
    def denoise(self, prices: np.ndarray, threshold_mode: str = 'soft') -> np.ndarray:
        """
        Denoise price series using wavelet thresholding
        
        Args:
            prices: Input price array
            threshold_mode: 'soft' or 'hard' thresholding
            
        Returns:
            Denoised price array
        """
        if not PYWT_AVAILABLE:
            return self._simple_denoise(prices)
            
        if len(prices) < 2 ** self.levels:
            return self._simple_denoise(prices)
            
        try:
            # Decompose
            coeffs = pywt.wavedec(prices, self.wavelet, level=self.levels)
            
            # Calculate universal threshold
            # sigma = median(|detail coefficients|) / 0.6745
            detail = coeffs[-1]
            sigma = np.median(np.abs(detail)) / 0.6745
            threshold = sigma * np.sqrt(2 * np.log(len(prices)))
            
            # Apply threshold to detail coefficients
            denoised_coeffs = [coeffs[0]]  # Keep approximation unchanged
            for i, c in enumerate(coeffs[1:]):
                if threshold_mode == 'soft':
                    denoised = pywt.threshold(c, threshold, mode='soft')
                else:
                    denoised = pywt.threshold(c, threshold, mode='hard')
                denoised_coeffs.append(denoised)
                
            # Reconstruct
            denoised_signal = pywt.waverec(denoised_coeffs, self.wavelet)[:len(prices)]
            
            return denoised_signal
            
        except Exception as e:
            print(f"Wavelet denoising error: {e}")
            return self._simple_denoise(prices)
            
    def _simple_denoise(self, prices: np.ndarray) -> np.ndarray:
        """Simple fallback denoising using moving average"""
        if len(prices) < 5:
            return prices
            
        window = min(5, len(prices))
        kernel = np.ones(window) / window
        denoised = np.convolve(prices, kernel, mode='same')
        
        # Fix edges
        denoised[:window//2] = prices[:window//2]
        denoised[-window//2:] = prices[-window//2:]
        
        return denoised
        
    def get_multi_scale_features(self, prices: np.ndarray) -> Dict:
        """
        Extract features at multiple scales for ML models
        
        Returns:
            Dict with features at different scales
        """
        if len(prices) < 20:
            return self._default_features()
            
        try:
            decomp = self.decompose(prices)
            trend = decomp['trend']
            noise = decomp['noise']
            
            # Trend features
            trend_slope = (trend[-1] - trend[-10]) / 10 if len(trend) >= 10 else 0
            trend_acceleration = 0
            if len(trend) >= 20:
                slope_now = (trend[-1] - trend[-10]) / 10
                slope_prev = (trend[-10] - trend[-20]) / 10
                trend_acceleration = slope_now - slope_prev
                
            # Noise features (volatility indicators)
            noise_std = np.std(noise[-20:]) if len(noise) >= 20 else np.std(noise)
            noise_mean = np.mean(np.abs(noise[-20:])) if len(noise) >= 20 else np.mean(np.abs(noise))
            
            # Signal-to-noise ratio
            signal_power = np.var(trend[-20:]) if len(trend) >= 20 else np.var(trend)
            noise_power = np.var(noise[-20:]) if len(noise) >= 20 else np.var(noise)
            snr = signal_power / (noise_power + 0.001)
            
            # Trend reversals
            trend_diff = np.diff(trend[-20:]) if len(trend) >= 20 else np.diff(trend)
            zero_crossings = np.sum(np.diff(np.sign(trend_diff)) != 0)
            
            return {
                'trend_slope': round(trend_slope, 6),
                'trend_acceleration': round(trend_acceleration, 6),
                'noise_std': round(noise_std, 4),
                'noise_mean': round(noise_mean, 4),
                'snr': round(snr, 4),
                'trend_reversals': zero_crossings,
                'denoised_price': round(trend[-1], 2) if len(trend) > 0 else prices[-1],
                'noise_level': round(abs(noise[-1]) if len(noise) > 0 else 0, 4)
            }
            
        except Exception as e:
            print(f"Multi-scale feature error: {e}")
            return self._default_features()
            
    def _default_features(self) -> Dict:
        """Return default features when calculation fails"""
        return {
            'trend_slope': 0,
            'trend_acceleration': 0,
            'noise_std': 0,
            'noise_mean': 0,
            'snr': 1,
            'trend_reversals': 0,
            'denoised_price': 0,
            'noise_level': 0
        }
        
    def get_trading_signals(self, prices: np.ndarray) -> Dict:
        """
        Generate trading signals from wavelet analysis
        """
        if len(prices) < 20:
            return {'signal': 'NEUTRAL', 'strength': 0.5, 'reason': 'Insufficient data'}
            
        features = self.get_multi_scale_features(prices)
        
        # Signal logic
        signal = 'NEUTRAL'
        strength = 0.5
        reasons = []
        
        # Trend-based signal
        if features['trend_slope'] > 0.1:
            signal = 'BULLISH'
            strength += 0.1
            reasons.append('Upward trend')
        elif features['trend_slope'] < -0.1:
            signal = 'BEARISH'
            strength += 0.1
            reasons.append('Downward trend')
            
        # Acceleration-based confirmation
        if signal == 'BULLISH' and features['trend_acceleration'] > 0:
            strength += 0.1
            reasons.append('Accelerating uptrend')
        elif signal == 'BEARISH' and features['trend_acceleration'] < 0:
            strength += 0.1
            reasons.append('Accelerating downtrend')
            
        # Noise-based confidence
        if features['snr'] > 2:
            strength += 0.1
            reasons.append('Strong signal-to-noise')
        elif features['snr'] < 0.5:
            strength -= 0.2
            reasons.append('Noisy market')
            
        strength = min(max(strength, 0), 1)
        
        return {
            'signal': signal,
            'strength': round(strength, 2),
            'features': features,
            'reason': ', '.join(reasons) if reasons else 'No strong signals'
        }


# Singleton instance
wavelet_analyzer = WaveletAnalyzer()


def analyze_wavelet(prices: List[float]) -> Dict:
    """Perform wavelet analysis on price series"""
    return wavelet_analyzer.decompose(np.array(prices))


def denoise_prices(prices: List[float]) -> np.ndarray:
    """Denoise price series"""
    return wavelet_analyzer.denoise(np.array(prices))


def get_wavelet_features(prices: List[float]) -> Dict:
    """Get multi-scale features from wavelet analysis"""
    return wavelet_analyzer.get_multi_scale_features(np.array(prices))


def get_wavelet_signals(prices: List[float]) -> Dict:
    """Get trading signals from wavelet analysis"""
    return wavelet_analyzer.get_trading_signals(np.array(prices))
