"""
Signal Confirmation Module
Filters ML predictions through multiple confirmation checks:
1. Multi-timeframe alignment
2. Volume confirmation
3. Support/Resistance proximity
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class SignalConfirmer:
    """
    Validates ML signals through multiple confirmation filters
    Only passes signals that meet strict confirmation criteria
    """
    
    def __init__(self):
        self.min_volume_ratio = 0.8  # Volume must be at least 80% of average
        self.sr_proximity_threshold = 0.3  # 0.3% from S/R level is too close
        
    def confirm_signal(self, 
                       prediction: Dict,
                       candles_15m: List[Dict],
                       candles_1h: List[Dict] = None,
                       indicators: Dict = None,
                       key_levels: Dict = None) -> Dict:
        """
        Run all confirmation checks on a prediction signal
        
        Returns:
            Dict with confirmed signal and confirmation details
        """
        confirmations = []
        rejections = []
        confidence_adjustment = 0
        
        original_direction = prediction.get('direction', 'NEUTRAL')
        original_confidence = prediction.get('confidence', 0)
        original_signal = prediction.get('signal', 'WAIT')
        
        # Skip confirmation for neutral/wait signals
        if original_direction == 'NEUTRAL' or original_signal == 'WAIT':
            return {
                **prediction,
                'confirmed': False,
                'confirmations': [],
                'rejections': ['No actionable signal']
            }
        
        # Check 1: Volume Confirmation
        vol_check = self._check_volume(candles_15m, original_direction)
        if vol_check['confirmed']:
            confirmations.append(vol_check['reason'])
            confidence_adjustment += vol_check.get('boost', 3)
        else:
            rejections.append(vol_check['reason'])
            confidence_adjustment -= 5
            
        # Check 2: Multi-timeframe Confirmation (if 1H data available)
        if candles_1h and len(candles_1h) >= 10:
            mtf_check = self._check_multi_timeframe(candles_15m, candles_1h, original_direction)
            if mtf_check['confirmed']:
                confirmations.append(mtf_check['reason'])
                confidence_adjustment += mtf_check.get('boost', 5)
            else:
                rejections.append(mtf_check['reason'])
                confidence_adjustment -= 8
                
        # Check 3: Support/Resistance Proximity
        if key_levels:
            sr_check = self._check_sr_proximity(candles_15m[-1], key_levels, original_direction)
            if sr_check['confirmed']:
                confirmations.append(sr_check['reason'])
                confidence_adjustment += sr_check.get('boost', 2)
            else:
                rejections.append(sr_check['reason'])
                confidence_adjustment -= 10
                
        # Check 4: Momentum Alignment
        mom_check = self._check_momentum(candles_15m, original_direction)
        if mom_check['confirmed']:
            confirmations.append(mom_check['reason'])
            confidence_adjustment += mom_check.get('boost', 3)
        else:
            rejections.append(mom_check['reason'])
            confidence_adjustment -= 5
            
        # Check 5: RSI Confirmation (not overbought for BULLISH, not oversold for BEARISH)
        if indicators:
            rsi_check = self._check_rsi(indicators, original_direction)
            if rsi_check['confirmed']:
                confirmations.append(rsi_check['reason'])
                confidence_adjustment += rsi_check.get('boost', 2)
            else:
                rejections.append(rsi_check['reason'])
                confidence_adjustment -= 3
        
        # Calculate final confidence
        adjusted_confidence = max(0, min(100, original_confidence + confidence_adjustment))
        
        # Determine if signal is confirmed
        is_confirmed = len(confirmations) >= 3 and adjusted_confidence >= 60
        
        # Adjust signal based on confirmation
        final_signal = original_signal if is_confirmed else 'WAIT'
        
        return {
            'direction': original_direction,
            'signal': final_signal,
            'confidence': adjusted_confidence,
            'original_confidence': original_confidence,
            'confirmed': is_confirmed,
            'confirmations': confirmations,
            'rejections': rejections,
            'confirmation_score': len(confirmations),
            'rejection_score': len(rejections),
            'timestamp': datetime.now().isoformat()
        }
        
    def _check_volume(self, candles: List[Dict], direction: str) -> Dict:
        """Check if volume supports the signal"""
        if len(candles) < 10:
            return {'confirmed': False, 'reason': 'Insufficient data for volume check'}
            
        volumes = [c.get('volume', c.get('Volume', 1)) for c in candles]
        current_vol = volumes[-1]
        avg_vol = np.mean(volumes[-20:]) if len(volumes) >= 20 else np.mean(volumes)
        
        vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1
        
        # For strong moves, we want above-average volume
        if vol_ratio >= self.min_volume_ratio:
            if vol_ratio >= 1.2:
                return {
                    'confirmed': True,
                    'reason': f'Strong volume ({vol_ratio:.1f}x avg)',
                    'boost': 5
                }
            else:
                return {
                    'confirmed': True,
                    'reason': f'Adequate volume ({vol_ratio:.1f}x avg)',
                    'boost': 2
                }
        else:
            return {
                'confirmed': False,
                'reason': f'Low volume ({vol_ratio:.1f}x avg)',
                'boost': 0
            }
            
    def _check_multi_timeframe(self, candles_15m: List[Dict], 
                                candles_1h: List[Dict], 
                                direction: str) -> Dict:
        """Check if higher timeframe agrees with signal"""
        # Get 15m trend
        closes_15m = [c.get('close', c.get('Close', 0)) for c in candles_15m[-10:]]
        trend_15m = 'BULLISH' if closes_15m[-1] > closes_15m[0] else 'BEARISH'
        
        # Get 1H trend
        closes_1h = [c.get('close', c.get('Close', 0)) for c in candles_1h[-5:]]
        trend_1h = 'BULLISH' if closes_1h[-1] > closes_1h[0] else 'BEARISH'
        
        # 1H SMA trend
        sma_1h = np.mean(closes_1h)
        sma_trend = 'BULLISH' if closes_1h[-1] > sma_1h else 'BEARISH'
        
        # Count alignments
        alignments = sum([
            trend_15m == direction,
            trend_1h == direction,
            sma_trend == direction
        ])
        
        if alignments >= 2:
            return {
                'confirmed': True,
                'reason': f'MTF aligned ({alignments}/3 timeframes)',
                'boost': 5 if alignments == 3 else 3
            }
        else:
            return {
                'confirmed': False,
                'reason': f'MTF divergence ({alignments}/3 aligned)',
                'boost': 0
            }
            
    def _check_sr_proximity(self, current_candle: Dict, 
                            key_levels: Dict, 
                            direction: str) -> Dict:
        """Check if price is too close to support/resistance"""
        current_price = current_candle.get('close', current_candle.get('Close', 0))
        
        supports = key_levels.get('supports', [])
        resistances = key_levels.get('resistances', [])
        
        if not supports and not resistances:
            return {'confirmed': True, 'reason': 'No key levels defined', 'boost': 0}
        
        # Check proximity to resistance (for BULLISH signals)
        if direction == 'BULLISH' and resistances:
            nearest_resistance = min(resistances, key=lambda x: abs(x - current_price) if x > current_price else float('inf'))
            if nearest_resistance > current_price:
                distance_pct = ((nearest_resistance - current_price) / current_price) * 100
                if distance_pct < self.sr_proximity_threshold:
                    return {
                        'confirmed': False,
                        'reason': f'Too close to resistance ({distance_pct:.2f}%)',
                        'boost': 0
                    }
                    
        # Check proximity to support (for BEARISH signals)
        if direction == 'BEARISH' and supports:
            nearest_support = max(supports, key=lambda x: x if x < current_price else 0)
            if nearest_support < current_price:
                distance_pct = ((current_price - nearest_support) / current_price) * 100
                if distance_pct < self.sr_proximity_threshold:
                    return {
                        'confirmed': False,
                        'reason': f'Too close to support ({distance_pct:.2f}%)',
                        'boost': 0
                    }
                    
        return {
            'confirmed': True,
            'reason': 'Good distance from S/R levels',
            'boost': 2
        }
        
    def _check_momentum(self, candles: List[Dict], direction: str) -> Dict:
        """Check if short-term momentum aligns with signal"""
        if len(candles) < 5:
            return {'confirmed': False, 'reason': 'Insufficient data'}
            
        closes = [c.get('close', c.get('Close', 0)) for c in candles]
        
        # Calculate momentum (last 3 vs last 5)
        short_mom = (closes[-1] - closes[-3]) / closes[-3] * 100 if len(closes) >= 3 else 0
        
        if direction == 'BULLISH':
            if short_mom > 0.05:
                return {'confirmed': True, 'reason': f'Positive momentum ({short_mom:.2f}%)', 'boost': 3}
            elif short_mom < -0.1:
                return {'confirmed': False, 'reason': f'Negative momentum ({short_mom:.2f}%)', 'boost': 0}
        else:  # BEARISH
            if short_mom < -0.05:
                return {'confirmed': True, 'reason': f'Negative momentum ({short_mom:.2f}%)', 'boost': 3}
            elif short_mom > 0.1:
                return {'confirmed': False, 'reason': f'Positive momentum ({short_mom:.2f}%)', 'boost': 0}
                
        return {'confirmed': True, 'reason': 'Neutral momentum', 'boost': 1}
        
    def _check_rsi(self, indicators: Dict, direction: str) -> Dict:
        """Check if RSI supports the signal"""
        rsi = indicators.get('rsi', 50)
        if rsi is None:
            rsi = 50
            
        if direction == 'BULLISH':
            if rsi >= 75:
                return {'confirmed': False, 'reason': f'Overbought RSI ({rsi:.0f})', 'boost': 0}
            elif rsi <= 35:
                return {'confirmed': True, 'reason': f'Oversold RSI bounce ({rsi:.0f})', 'boost': 4}
            else:
                return {'confirmed': True, 'reason': f'RSI in range ({rsi:.0f})', 'boost': 1}
        else:  # BEARISH
            if rsi <= 25:
                return {'confirmed': False, 'reason': f'Oversold RSI ({rsi:.0f})', 'boost': 0}
            elif rsi >= 65:
                return {'confirmed': True, 'reason': f'Overbought RSI drop ({rsi:.0f})', 'boost': 4}
            else:
                return {'confirmed': True, 'reason': f'RSI in range ({rsi:.0f})', 'boost': 1}


# Singleton instance
signal_confirmer = SignalConfirmer()


def confirm_signal(prediction: Dict, 
                   candles_15m: List[Dict],
                   candles_1h: List[Dict] = None,
                   indicators: Dict = None,
                   key_levels: Dict = None) -> Dict:
    """Confirm a prediction signal through multiple filters"""
    return signal_confirmer.confirm_signal(
        prediction, candles_15m, candles_1h, indicators, key_levels
    )
