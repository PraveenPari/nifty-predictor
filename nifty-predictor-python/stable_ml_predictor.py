"""
Stable ML Prediction System (Enhanced)
Integrates: Market Regime Detection, Wavelet Analysis, Sentiment Analysis, Enhanced Features
Provides high-confidence predictions for 15-minute trading
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from indicators_fast import TechnicalIndicatorsFast as TechnicalIndicators
from advanced_ensemble import get_advanced_model

# Import new enhanced modules
try:
    from market_regime_detector import detect_market_regime, fit_regime_detector, get_trading_bias
    REGIME_AVAILABLE = True
except ImportError:
    REGIME_AVAILABLE = False
    print("INFO: Market Regime Detector not available")

try:
    from wavelet_analyzer import get_wavelet_features, get_wavelet_signals
    WAVELET_AVAILABLE = True
except ImportError:
    WAVELET_AVAILABLE = False
    print("INFO: Wavelet Analyzer not available")

try:
    from sentiment_analyzer import get_combined_sentiment
    SENTIMENT_AVAILABLE = True
except ImportError:
    SENTIMENT_AVAILABLE = False
    print("INFO: Sentiment Analyzer not available")

try:
    from enhanced_features import get_enhanced_features
    ENHANCED_FEATURES_AVAILABLE = True
except ImportError:
    ENHANCED_FEATURES_AVAILABLE = False
    print("INFO: Enhanced Features not available")

# Import new accuracy improvement modules
try:
    from accuracy_tracker import log_prediction, validate_predictions as validate_accuracy, get_accuracy_stats
    ACCURACY_TRACKER_AVAILABLE = True
except ImportError:
    ACCURACY_TRACKER_AVAILABLE = False
    print("INFO: Accuracy Tracker not available")

try:
    from signal_confirmer import confirm_signal
    SIGNAL_CONFIRMER_AVAILABLE = True
except ImportError:
    SIGNAL_CONFIRMER_AVAILABLE = False
    print("INFO: Signal Confirmer not available")

try:
    from lstm_predictor import train_lstm, get_lstm_prediction, is_lstm_available
    LSTM_AVAILABLE = is_lstm_available()
except ImportError:
    LSTM_AVAILABLE = False
    print("INFO: LSTM Predictor not available")


class StableMLPredictor:
    """
    Enhanced Stable ML Predictor with:
    - Market Regime Awareness
    - Wavelet-based Signal Analysis
    - Multi-source Sentiment Integration
    - 100+ Enhanced Features
    """
    
    def __init__(self, prediction_interval_minutes=15):
        # Advanced Ensemble Model
        self.model = get_advanced_model()
        
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = []
        
        # Stability features
        self.last_prediction = None
        self.last_prediction_time = None
        self.prediction_interval = timedelta(minutes=prediction_interval_minutes)
        self.prediction_history = []
        self.confidence_threshold = 60  # Lowered slightly with more data sources
        
        # Training metadata
        self.training_accuracy = {'ensemble': 0}
        self.last_train_time = None
        
        # Enhanced analysis results cache
        self.last_regime = None
        self.last_wavelet = None
        self.last_sentiment = None
        
    def validate_predictions(self, current_price: float) -> int:
        """
        Validate past predictions against current price (REAL-TIME)
        Returns number of newly validated predictions
        """
        if not self.prediction_history:
            return 0
            
        validated_count = 0
        now = datetime.now()
        
        for pred in self.prediction_history:
            # Skip if already validated or not enough time passed
            if pred.get('validated', False):
                continue
                
            # Check if prediction time window has passed (wait 15 mins for outcome)
            pred_time = datetime.fromisoformat(pred['timestamp'])
            validation_time = pred_time + self.prediction_interval
            
            if now >= validation_time:
                # Validate this prediction
                direction = pred['direction']
                entry_price = pred.get('entry_price', current_price) # Fallback if not saved
                
                # Check outcome
                result = 'NEUTRAL'
                percent_change = ((current_price - entry_price) / entry_price) * 100
                
                # IMPROVED: Use 0.2% threshold for meaningful wins (was 0.05%)
                WIN_THRESHOLD = 0.2  # 0.2% = ~44 points on NIFTY 22000
                
                if direction == 'BULLISH':
                    if percent_change >= WIN_THRESHOLD:
                        result = 'WIN'
                    elif percent_change <= -WIN_THRESHOLD:
                        result = 'LOSS'
                    else:
                        result = 'FLAT'
                elif direction == 'BEARISH':
                    if percent_change <= -WIN_THRESHOLD:
                        result = 'WIN'
                    elif percent_change >= WIN_THRESHOLD:
                        result = 'LOSS'
                    else:
                        result = 'FLAT'
                
                pred['validated'] = True
                pred['validation_price'] = current_price
                pred['validation_time'] = now.isoformat()
                pred['result'] = result
                pred['actual_change'] = round(percent_change, 2)
                
                validated_count += 1
                
        return validated_count
        
    def _should_update_prediction(self) -> bool:
        """Check if we should generate a new prediction"""
        if self.last_prediction_time is None:
            return True
        
        time_since_last = datetime.now() - self.last_prediction_time
        return time_since_last >= self.prediction_interval
    
    def _prepare_features(self, candles: List[Dict], indicators: Dict, 
                          option_data: Dict = None) -> Optional[np.ndarray]:
        """Prepare comprehensive feature vector with all enhancements"""
        if len(candles) < 30:
            return None
        
        # Try enhanced features first
        if ENHANCED_FEATURES_AVAILABLE:
            try:
                features_array, feature_names = get_enhanced_features(candles, indicators, option_data)
                if len(features_array) > 10:
                    self.feature_names = feature_names
                    return features_array.reshape(1, -1)
            except Exception as e:
                print(f"Enhanced features error: {e}")
        
        # Fallback to basic features
        features = []
        
        # Price features
        closes = [c.get('close', c.get('Close', 0)) for c in candles[-30:]]
        volumes = [c.get('volume', c.get('Volume', 1)) for c in candles[-30:]]
        
        # Returns analysis
        returns = [(closes[i] - closes[i-1]) / closes[i-1] * 100 for i in range(1, len(closes))]
        features.extend([
            np.mean(returns),
            np.std(returns),
            returns[-1] if returns else 0,
            np.mean(returns[-5:]) if len(returns) >= 5 else 0,
            np.mean(returns[-15:]) if len(returns) >= 15 else 0,
        ])
        
        # Price position features
        avg_price = np.mean(closes)
        max_price = max(closes)
        min_price = min(closes)
        features.extend([
            (closes[-1] - avg_price) / avg_price * 100,
            (closes[-1] - closes[0]) / closes[0] * 100,
            (closes[-1] - min_price) / (max_price - min_price) * 100 if max_price != min_price else 50,
        ])
        
        # Volume analysis
        avg_volume = np.mean(volumes)
        features.extend([
            volumes[-1] / avg_volume if avg_volume > 0 else 1,
            np.std(volumes) / avg_volume if avg_volume > 0 else 0,
        ])
        
        # Technical Indicators
        features.append(indicators.get('rsi', 50) or 50)
        
        macd_data = indicators.get('macd', {})
        features.extend([
            macd_data.get('histogram', 0) / 10 if macd_data else 0,
            macd_data.get('macd', 0) / 10 if macd_data else 0,
            macd_data.get('signal', 0) / 10 if macd_data else 0,
        ])
        
        stoch = indicators.get('stochastic', {})
        features.extend([
            stoch.get('k', 50) if stoch else 50,
            stoch.get('d', 50) if stoch else 50,
        ])
        
        adx_data = indicators.get('adx', {})
        features.extend([
            adx_data.get('adx', 25) if adx_data else 25,
            (adx_data.get('plus_di', 25) - adx_data.get('minus_di', 25)) if adx_data else 0,
        ])
        
        bb = indicators.get('bollinger', {})
        if bb:
            upper = bb.get('upper', closes[-1])
            lower = bb.get('lower', closes[-1])
            if upper != lower:
                bb_pos = (closes[-1] - lower) / (upper - lower)
            else:
                bb_pos = 0.5
            bb_pos = max(0, min(1, bb_pos)) * 100
            features.append(bb_pos)
            features.append(bb.get('bandwidth', 0))
        else:
            features.extend([50, 0])
        
        features.append((indicators.get('cci', 0) or 0) / 100)
        features.append((indicators.get('williams_r', -50) or -50) + 100)
        
        atr = indicators.get('atr', 0) or 0
        features.append(atr / closes[-1] * 100 if closes[-1] > 0 else 0)
        
        supertrend = indicators.get('supertrend', {})
        if supertrend:
            trend = supertrend.get('trend', '')
            features.append(1 if trend == 'UP' or trend == 'bullish' else -1)
        else:
            features.append(0)
        
        vwap = indicators.get('vwap')
        if vwap is None or vwap == 0:
            vwap = closes[-1]
        features.append((closes[-1] - vwap) / vwap * 100 if vwap and vwap > 0 else 0)
        
        # EMA crossovers
        try:
            ema12 = TechnicalIndicators.ema(closes, 12) or closes[-1]
            ema26 = TechnicalIndicators.ema(closes, 26) or closes[-1]
            features.append((ema12 - ema26) / ema26 * 100 if ema26 > 0 else 0)
        except:
            features.append(0)
        
        # Add regime features if available
        if REGIME_AVAILABLE and self.last_regime:
            regime_score = {
                'BULLISH': 1, 'BEARISH': -1, 'SIDEWAYS': 0, 
                'HIGH_VOLATILITY': 0, 'LOW_VOLATILITY': 0
            }.get(self.last_regime.get('regime', 'NEUTRAL'), 0)
            features.append(regime_score)
            features.append(self.last_regime.get('confidence', 0.5))
        else:
            features.extend([0, 0.5])
        
        # Add wavelet features if available
        if WAVELET_AVAILABLE and self.last_wavelet:
            features.append(self.last_wavelet.get('trend_slope', 0))
            features.append(self.last_wavelet.get('snr', 1))
        else:
            features.extend([0, 1])
        
        # Add sentiment features if available
        if SENTIMENT_AVAILABLE and self.last_sentiment:
            features.append(self.last_sentiment.get('combined_score', 0))
        else:
            features.append(0)
        
        self.feature_names = [
            'avg_return', 'volatility', 'latest_return', 'short_momentum', 'medium_momentum',
            'price_vs_avg', 'period_return', 'price_position',
            'rel_volume', 'vol_volatility',
            'rsi', 'macd_hist', 'macd', 'macd_signal',
            'stoch_k', 'stoch_d',
            'adx', 'di_diff',
            'bb_position', 'bb_width',
            'cci', 'williams_r', 'atr_pct',
            'supertrend', 'vwap_pos', 'ema_cross',
            'regime_score', 'regime_confidence',
            'wavelet_slope', 'wavelet_snr',
            'sentiment_score'
        ]
        
        return np.array(features).reshape(1, -1)
    
    def _generate_training_data(self, candles: List[Dict], indicators: Dict, lookback: int = 50) -> Tuple[np.ndarray, np.ndarray]:
        """Generate training data with enhanced features"""
        X = []
        y = []
        
        min_candles = lookback + 20
        if len(candles) < min_candles:
            return np.array([]), np.array([])
        
        for i in range(lookback, len(candles) - 5):
            subset_candles = candles[max(0, i-lookback):i]
            if len(subset_candles) < 30: 
                continue
            
            closes = [c.get('close', c.get('Close', 0)) for c in subset_candles]
            volumes = [c.get('volume', c.get('Volume', 1)) for c in subset_candles]
            
            returns = [(closes[j] - closes[j-1]) / closes[j-1] * 100 for j in range(1, len(closes))]
            
            features = [
                np.mean(returns), np.std(returns), returns[-1] if returns else 0,
                np.mean(returns[-5:]) if len(returns) >= 5 else 0,
                np.mean(returns[-15:]) if len(returns) >= 15 else 0,
            ]
            
            avg_price = np.mean(closes)
            max_price = max(closes)
            min_price = min(closes)
            features.extend([
                (closes[-1] - avg_price) / avg_price * 100,
                (closes[-1] - closes[0]) / closes[0] * 100,
                (closes[-1] - min_price) / (max_price - min_price) * 100 if max_price != min_price else 50,
            ])
            
            avg_volume = np.mean(volumes)
            features.extend([
                volumes[-1] / avg_volume if avg_volume > 0 else 1,
                np.std(volumes) / avg_volume if avg_volume > 0 else 0,
            ])
            
            # RSI
            rsi = TechnicalIndicators.rsi(closes) or 50
            features.append(rsi)
            
            # Placeholders for other indicators
            features.extend([0] * 20)  # Fill to match prediction features
            
            X.append(features)
            
            # Target: price direction in next 3-5 candles
            future_idx = min(i + 3, len(candles) - 1)
            future_price = candles[future_idx].get('close', candles[future_idx].get('Close', 0))
            current_price = candles[i].get('close', candles[i].get('Close', 0))
            
            price_change = (future_price - current_price) / current_price * 100 if current_price > 0 else 0
            # Target 1 (Bullish) if price goes up by more than 0.05% (~12 points Nifty)
            y.append(1 if price_change > 0.05 else 0)
        
        return np.array(X), np.array(y)
    
    def _run_enhanced_analysis(self, candles: List[Dict], indicators: Dict, option_data: Dict = None):
        """Run all enhanced analysis modules"""
        closes = [c.get('close', c.get('Close', 0)) for c in candles]
        
        # Market Regime Detection
        if REGIME_AVAILABLE:
            try:
                self.last_regime = detect_market_regime(candles, indicators)
            except Exception as e:
                print(f"Regime detection error: {e}")
                self.last_regime = None
        
        # Wavelet Analysis
        if WAVELET_AVAILABLE:
            try:
                self.last_wavelet = get_wavelet_features(closes)
            except Exception as e:
                print(f"Wavelet analysis error: {e}")
                self.last_wavelet = None
        
        # Sentiment Analysis
        if SENTIMENT_AVAILABLE:
            try:
                self.last_sentiment = get_combined_sentiment(
                    news=None,  # Would need external news feed
                    options=option_data,
                    indicators=indicators
                )
            except Exception as e:
                print(f"Sentiment analysis error: {e}")
                self.last_sentiment = None
    
    def train(self, candles: List[Dict], indicators: Dict) -> bool:
        """Train the Enhanced Advanced Ensemble"""
        try:
            if len(candles) < 100:
                print(f"[WARNING] Need at least 100 candles. Got {len(candles)}")
                return False
            
            print(f"[TRAIN] Training Enhanced ML Ensemble on {len(candles)} candles...")
            
            # Run enhanced analysis first
            self._run_enhanced_analysis(candles, indicators)
            
            # Fit regime detector
            if REGIME_AVAILABLE:
                try:
                    fit_regime_detector(candles)
                except:
                    pass
            
            X, y = self._generate_training_data(candles, indicators)
            
            if len(X) < 50:
                print("[WARNING] Not enough training samples")
                return False
            
            # Check class balance
            unique, counts = np.unique(y, return_counts=True)
            print(f"[INFO] Class distribution: {dict(zip(unique, counts))}")
            
            # Scale
            X_scaled = self.scaler.fit_transform(X)
            
            # Split with stratification
            try:
                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled, y, test_size=0.25, random_state=42, stratify=y
                )
            except ValueError:
                # If stratification fails, do regular split
                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled, y, test_size=0.25, random_state=42
                )
            
            # Train Ensemble
            self.model.fit(X_train, y_train)
            
            # Assess
            score = self.model.score(X_test, y_test)
            self.training_accuracy['ensemble'] = score
            
            self.is_trained = True
            self.last_train_time = datetime.now()
            
            print(f"[SUCCESS] Enhanced ML Ensemble Trained! Accuracy: {score:.1%}")
            
            # Print model info
            try:
                model_info = self.model.get_model_info()
                print(f"   Models: {model_info.get('estimators', [])}")
                print(f"   Regime: {self.last_regime.get('regime', 'N/A') if self.last_regime else 'N/A'}")
            except:
                pass
            
            # AUTO-TRAIN LSTM (integrated)
            if LSTM_AVAILABLE:
                try:
                    lstm_success = train_lstm(candles)
                    if lstm_success:
                        print("[SUCCESS] LSTM Neural Network also trained!")
                except Exception as lstm_err:
                    print(f"[INFO] LSTM training skipped: {lstm_err}")
                
            return True
            
        except Exception as e:
            print(f"[ERROR] Training error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def predict(self, candles: List[Dict], indicators: Dict, 
                force_update: bool = False, option_data: Dict = None) -> Dict:
        """Make enhanced stable prediction"""
        try:
            if not force_update and not self._should_update_prediction():
                if self.last_prediction:
                    return {**self.last_prediction, 'cached': True}
            
            # Run enhanced analysis
            self._run_enhanced_analysis(candles, indicators, option_data)
            
            if not self.is_trained:
                self.train(candles, indicators)
            
            features = self._prepare_features(candles, indicators, option_data)
            if features is None:
                return {'direction': 'NEUTRAL', 'signal': 'WAIT', 'confidence': 0}
            
            # Ensure feature dimensions match
            if features.shape[1] != self.scaler.n_features_in_:
                # Pad or truncate features
                expected = self.scaler.n_features_in_
                if features.shape[1] < expected:
                    padding = np.zeros((1, expected - features.shape[1]))
                    features = np.hstack([features, padding])
                else:
                    features = features[:, :expected]
            
            features_scaled = self.scaler.transform(features)
            
            # Get probability from ensemble
            probs = self.model.predict_proba(features_scaled)[0]
            
            # Handle different probability shapes
            if len(probs) == 2:
                bearish_prob = probs[0] * 100
                bullish_prob = probs[1] * 100
            else:
                bullish_prob = probs[0] * 100 if probs[0] > 0.5 else (1 - probs[0]) * 100
                bearish_prob = 100 - bullish_prob
            
            # Determine direction
            if bullish_prob > bearish_prob:
                direction = 'BULLISH'
                confidence = round(bullish_prob)
            elif bearish_prob > bullish_prob:
                direction = 'BEARISH'
                confidence = round(bearish_prob)
            else:
                direction = 'NEUTRAL'
                confidence = 50
            
            # Adjust confidence based on additional signals
            signal = 'WAIT'
            reason = []
            
            # Regime adjustment
            if self.last_regime:
                regime = self.last_regime.get('regime', '')
                regime_conf = self.last_regime.get('confidence', 0)
                
                if regime == 'BULLISH' and direction == 'BULLISH':
                    confidence = min(100, confidence + 5)
                    reason.append("Bullish regime confirmed")
                elif regime == 'BEARISH' and direction == 'BEARISH':
                    confidence = min(100, confidence + 5)
                    reason.append("Bearish regime confirmed")
                elif regime == 'HIGH_VOLATILITY':
                    confidence = max(confidence - 10, 40)
                    reason.append("High volatility - reduced confidence")
                elif regime == 'SIDEWAYS':
                    confidence = max(confidence - 5, 45)
                    reason.append("Sideways market detected")
            
            # Wavelet signal adjustment
            if self.last_wavelet:
                trend_slope = self.last_wavelet.get('trend_slope', 0)
                if trend_slope > 0 and direction == 'BULLISH':
                    confidence = min(100, confidence + 3)
                elif trend_slope < 0 and direction == 'BEARISH':
                    confidence = min(100, confidence + 3)
            
            # Sentiment adjustment
            if self.last_sentiment:
                sent_score = self.last_sentiment.get('combined_score', 0)
                if sent_score > 0.2 and direction == 'BULLISH':
                    confidence = min(100, confidence + 2)
                    reason.append("Positive sentiment")
                elif sent_score < -0.2 and direction == 'BEARISH':
                    confidence = min(100, confidence + 2)
                    reason.append("Negative sentiment")
            
            # Generate signal
            if confidence >= self.confidence_threshold:
                if direction == 'BULLISH':
                    signal = 'BUY CALL'
                    reason.append("Strong bullish signal")
                else:
                    signal = 'BUY PUT'
                    reason.append("Strong bearish signal")
            else:
                reason.append(f"Confidence {confidence}% below threshold {self.confidence_threshold}%")
            
            prediction = {
                'direction': direction,
                'signal': signal,
                'confidence': confidence,
                'bullish_prob': round(bullish_prob, 1),
                'bearish_prob': round(bearish_prob, 1),
                'model_agreement': round(confidence),
                'models': self.model.get_model_info() if hasattr(self.model, 'get_model_info') else {},
                'regime': self.last_regime.get('regime', 'N/A') if self.last_regime else 'N/A',
                'regime_confidence': self.last_regime.get('confidence', 0) if self.last_regime else 0,
                'wavelet_signal': self.last_wavelet.get('trend_slope', 0) if self.last_wavelet else 0,
                'sentiment': self.last_sentiment.get('combined_score', 0) if self.last_sentiment else 0,
                'reason': ' | '.join(reason),
                'timestamp': datetime.now().isoformat(),
                'next_update': (datetime.now() + self.prediction_interval).isoformat(),
                'cached': False,
                'entry_price': candles[-1].get('close', candles[-1].get('Close', 0)),
                'enhanced': True
            }
            
            # AUTO-INTEGRATE: LSTM Prediction (combine with ensemble)
            if LSTM_AVAILABLE:
                try:
                    lstm_pred = get_lstm_prediction(candles)
                    prediction['lstm_direction'] = lstm_pred.get('direction', 'NEUTRAL')
                    prediction['lstm_confidence'] = lstm_pred.get('confidence', 0)
                    
                    # Boost confidence if LSTM agrees with ensemble
                    if lstm_pred.get('direction') == direction and lstm_pred.get('confidence', 0) > 50:
                        prediction['confidence'] = min(100, prediction['confidence'] + 5)
                        reason.append('LSTM confirms')
                        prediction['reason'] = ' | '.join(reason)
                except Exception as lstm_err:
                    prediction['lstm_direction'] = 'N/A'
                    prediction['lstm_confidence'] = 0
            
            # AUTO-INTEGRATE: Signal Confirmation
            if SIGNAL_CONFIRMER_AVAILABLE and signal != 'WAIT':
                try:
                    confirmed = confirm_signal(
                        prediction,
                        candles_15m=candles,
                        indicators=indicators
                    )
                    prediction['signal_confirmed'] = confirmed.get('confirmed', False)
                    prediction['confirmations'] = confirmed.get('confirmations', [])
                    prediction['rejections'] = confirmed.get('rejections', [])
                    prediction['confirmation_score'] = confirmed.get('confirmation_score', 0)
                    
                    # Override signal if not confirmed (safer trading)
                    if not confirmed.get('confirmed', False):
                        prediction['original_signal'] = prediction['signal']
                        prediction['signal'] = 'WAIT (unconfirmed)'
                        signal = 'WAIT (unconfirmed)'
                except Exception as conf_err:
                    prediction['signal_confirmed'] = True  # Allow through on error
            
            # AUTO-INTEGRATE: Persistent Accuracy Logging
            if ACCURACY_TRACKER_AVAILABLE and direction != 'NEUTRAL':
                try:
                    pred_id = log_prediction(prediction, prediction['entry_price'])
                    prediction['tracking_id'] = pred_id
                except:
                    pass
            
            self.last_prediction = prediction
            self.last_prediction_time = datetime.now()
            self.prediction_history.append(prediction)
            
            # Keep only last 100 predictions
            if len(self.prediction_history) > 100:
                self.prediction_history = self.prediction_history[-100:]
            
            return prediction
            
        except Exception as e:
            print(f"[ERROR] Prediction error: {e}")
            import traceback
            traceback.print_exc()
            return {'direction': 'NEUTRAL', 'signal': 'WAIT', 'confidence': 0, 'error': str(e)}

    def _get_top_features(self) -> List[Dict]:
        """Get top important features"""
        try:
            top_features = self.model.get_top_features(10)
            return [{'index': idx, 'importance': imp, 'name': self.feature_names[idx] if idx < len(self.feature_names) else f'feature_{idx}'} 
                    for idx, imp in top_features]
        except:
            return []

    def get_stats(self) -> Dict:
        """Get comprehensive model statistics"""
        return {
            'is_trained': self.is_trained,
            'accuracy': self.training_accuracy.get('ensemble', 0),
            'model_info': self.model.get_model_info() if hasattr(self.model, 'get_model_info') else {},
            'last_train_time': self.last_train_time.isoformat() if self.last_train_time else None,
            'predictions_made': len(self.prediction_history),
            'current_regime': self.last_regime.get('regime', 'N/A') if self.last_regime else 'N/A',
            'enhancements': {
                'regime_detection': REGIME_AVAILABLE,
                'wavelet_analysis': WAVELET_AVAILABLE,
                'sentiment_analysis': SENTIMENT_AVAILABLE,
                'enhanced_features': ENHANCED_FEATURES_AVAILABLE,
                'lstm_predictor': LSTM_AVAILABLE,
                'signal_confirmer': SIGNAL_CONFIRMER_AVAILABLE,
                'accuracy_tracker': ACCURACY_TRACKER_AVAILABLE
            }
        }
        
    def get_live_stats(self) -> Dict:
        """Get live validation statistics"""
        losses = sum(1 for p in self.prediction_history if p.get('result') == 'LOSS')
        wins = sum(1 for p in self.prediction_history if p.get('result') == 'WIN')
        total_validated = wins + losses
        
        recent_results = [
            {'time': p['timestamp'], 'result': p['result'], 'direction': p['direction']} 
            for p in self.prediction_history if p.get('validated')
        ][-5:] # Last 5 results
        
        return {
            'live_win_rate': round((wins / total_validated * 100), 1) if total_validated > 0 else 0,
            'total_validated': total_validated,
            'wins': wins,
            'losses': losses,
            'recent_results': recent_results
        }
    
    def get_analysis_summary(self) -> Dict:
        """Get summary of all enhanced analysis"""
        return {
            'regime': self.last_regime,
            'wavelet': self.last_wavelet,
            'sentiment': self.last_sentiment,
            'trading_bias': get_trading_bias() if REGIME_AVAILABLE else None
        }


# Singleton instance (15-minute stable predictions)
stable_ml_predictor = StableMLPredictor(prediction_interval_minutes=15)


def get_stable_prediction(candles: List[Dict], indicators: Dict, 
                          force_update: bool = False, option_data: Dict = None) -> Dict:
    """Get stable ML prediction with enhanced analysis"""
    return stable_ml_predictor.predict(candles, indicators, force_update, option_data)


def train_stable_model(candles: List[Dict], indicators: Dict) -> bool:
    """Train the stable ML model"""
    return stable_ml_predictor.train(candles, indicators)


def get_ml_stats() -> Dict:
    """Get ML model statistics"""
    stats = stable_ml_predictor.get_stats()
    stats.update(stable_ml_predictor.get_live_stats())
    return stats


def validate_past_predictions(current_price: float) -> int:
    """Validate past predictions against current price"""
    return stable_ml_predictor.validate_predictions(current_price)


def get_analysis_summary() -> Dict:
    """Get enhanced analysis summary"""
    return stable_ml_predictor.get_analysis_summary()
