"""
Machine Learning Predictor Module
LSTM, Random Forest, and Gradient Boosting ensemble for price prediction
"""

print("  ml_predictor: Importing numpy...")
import numpy as np
from typing import List, Dict, Tuple, Optional
print("  ml_predictor: Importing sklearn...")
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

print("  ml_predictor: Importing constants...")
from global_constants import ML_CONFIG
from indicators_fast import TechnicalIndicatorsFast as TechnicalIndicators

print("  ml_predictor: Helper functions defined.")


class MLPredictor:
    """
    Machine Learning based price direction predictor
    Uses ensemble of multiple models for robust predictions
    """
    
    def __init__(self):
        self.rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=None,
            class_weight='balanced'
        )
        
        self.gb_model = GradientBoostingClassifier(
            n_estimators=50,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = []
        self.last_train_time = None
        self.training_history = []
        
    def _prepare_features(self, candles: List[Dict], indicators: Dict) -> np.ndarray:
        """Prepare feature vector from candles and indicators"""
        if len(candles) < 20:
            return None
        
        features = []
        
        # Price-based features
        closes = [c['close'] for c in candles[-20:]]
        highs = [c['high'] for c in candles[-20:]]
        lows = [c['low'] for c in candles[-20:]]
        volumes = [c['volume'] for c in candles[-20:]]
        
        # Returns
        returns = [(closes[i] - closes[i-1]) / closes[i-1] * 100 for i in range(1, len(closes))]
        features.extend([
            np.mean(returns),  # Average return
            np.std(returns),   # Volatility
            returns[-1] if returns else 0,  # Latest return
        ])
        
        # Price position
        avg_price = np.mean(closes)
        features.append((closes[-1] - avg_price) / avg_price * 100)  # Price vs average
        
        # Trend strength
        features.append((closes[-1] - closes[0]) / closes[0] * 100)  # Period return
        
        # Volume features
        avg_volume = np.mean(volumes)
        features.append(volumes[-1] / avg_volume if avg_volume > 0 else 1)  # Relative volume
        
        # Technical Indicators
        if indicators.get('rsi') is not None:
            features.append(indicators['rsi'])
        else:
            features.append(50)
        
        if indicators.get('macd') is not None:
            features.append(indicators['macd'].get('histogram', 0))
            features.append(indicators['macd'].get('macd', 0))
        else:
            features.extend([0, 0])
        
        if indicators.get('stochastic') is not None:
            features.append(indicators['stochastic'].get('k', 50))
            features.append(indicators['stochastic'].get('d', 50))
        else:
            features.extend([50, 50])
        
        if indicators.get('adx') is not None:
            features.append(indicators['adx'].get('adx', 0))
            features.append(indicators['adx'].get('plus_di', 0) - indicators['adx'].get('minus_di', 0))
        else:
            features.extend([0, 0])
        
        if indicators.get('bollinger') is not None:
            bb = indicators['bollinger']
            bb_pos = (closes[-1] - bb['lower']) / (bb['upper'] - bb['lower']) if bb['upper'] != bb['lower'] else 0.5
            features.append(bb_pos)
            features.append(bb['bandwidth'])
        else:
            features.extend([0.5, 0])
        
        if indicators.get('cci') is not None:
            features.append(indicators['cci'])
        else:
            features.append(0)
        
        if indicators.get('williams_r') is not None:
            features.append(indicators['williams_r'])
        else:
            features.append(-50)
        
        if indicators.get('atr') is not None:
            features.append(indicators['atr'] / closes[-1] * 100)  # ATR as percentage
        else:
            features.append(0)
        
        # SuperTrend
        if indicators.get('supertrend') is not None:
            features.append(1 if indicators['supertrend']['trend'] == 'bullish' else -1)
        else:
            features.append(0)
        
        # VWAP position
        if indicators.get('vwap') is not None:
            features.append((closes[-1] - indicators['vwap']) / indicators['vwap'] * 100)
        else:
            features.append(0)
        
        self.feature_names = [
            'avg_return', 'volatility', 'latest_return', 'price_vs_avg',
            'period_return', 'rel_volume', 'rsi', 'macd_hist', 'macd',
            'stoch_k', 'stoch_d', 'adx', 'di_diff', 'bb_position',
            'bb_width', 'cci', 'williams_r', 'atr_pct', 'supertrend', 'vwap_pos'
        ]
        
        return np.array(features).reshape(1, -1)
    
    def _generate_training_data(self, candles: List[Dict], indicators: Dict, lookback: int = 60) -> Tuple[np.ndarray, np.ndarray]:
        """Generate training data from historical candles"""
        X = []
        y = []
        
        for i in range(lookback, len(candles) - 5):
            # Get subset of candles and calculate features
            subset_candles = candles[i-lookback:i]
            
            # Calculate basic features
            closes = [c['close'] for c in subset_candles]
            highs = [c['high'] for c in subset_candles]
            lows = [c['low'] for c in subset_candles]
            volumes = [c['volume'] for c in subset_candles]
            
            features = []
            
            # Returns
            returns = [(closes[j] - closes[j-1]) / closes[j-1] * 100 for j in range(1, len(closes))]
            features.extend([np.mean(returns), np.std(returns), returns[-1] if returns else 0])
            
            # Price features
            avg_price = np.mean(closes)
            features.append((closes[-1] - avg_price) / avg_price * 100)
            features.append((closes[-1] - closes[0]) / closes[0] * 100)
            
            # Volume
            avg_volume = np.mean(volumes)
            features.append(volumes[-1] / avg_volume if avg_volume > 0 else 1)
            
            # Simplified indicators
            rsi = self._calculate_rsi(closes)
            features.append(rsi)
            
            # MACD
            ema12 = self._calculate_ema(closes, 12)
            ema26 = self._calculate_ema(closes, 26)
            macd = ema12 - ema26 if ema12 and ema26 else 0
            features.extend([macd * 0.1, macd])
            
            # Stochastic
            highest = max(highs[-14:])
            lowest = min(lows[-14:])
            stoch_k = ((closes[-1] - lowest) / (highest - lowest) * 100) if highest != lowest else 50
            features.extend([stoch_k, stoch_k * 0.9])
            
            # ADX (simplified)
            features.extend([25, 5])  # Placeholder
            
            # Bollinger
            sma = np.mean(closes[-20:])
            std = np.std(closes[-20:])
            bb_pos = (closes[-1] - (sma - 2*std)) / (4*std) if std > 0 else 0.5
            features.extend([bb_pos, (4*std/sma)*100 if sma > 0 else 0])
            
            # Other indicators (simplified)
            features.extend([0, -50, 1, 0, 0])  # CCI, Williams R, ATR%, SuperTrend, VWAP
            
            X.append(features)
            
            # Target 1 (Bullish) if price goes up by more than 0.05%
            future_price = candles[i + 5].get('close', candles[i + 5].get('Close', 0))
            current_price = candles[i].get('close', candles[i].get('Close', 0))
            price_change = ((future_price - current_price) / current_price * 100) if current_price > 0 else 0
            y.append(1 if price_change > 0.05 else 0)
        
        return np.array(X), np.array(y)
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI for training"""
        if len(prices) < period + 1:
            return 50
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            gains.append(max(change, 0))
            losses.append(abs(min(change, 0)))
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_ema(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate EMA for training"""
        if len(prices) < period:
            return None
        
        multiplier = 2 / (period + 1)
        ema = np.mean(prices[:period])
        
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def train(self, candles: List[Dict], indicators: Dict) -> bool:
        """Train the ML models on historical data"""
        try:
            if len(candles) < ML_CONFIG['min_training_samples']:
                print(f"Not enough data for training: {len(candles)} candles")
                return False
            
            X, y = self._generate_training_data(candles, indicators)
            
            if len(X) < 50:
                print("Not enough training samples generated")
                return False
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42
            )
            
            # Train models
            self.rf_model.fit(X_train, y_train)
            self.gb_model.fit(X_train, y_train)
            
            # Calculate accuracy
            rf_accuracy = self.rf_model.score(X_test, y_test)
            gb_accuracy = self.gb_model.score(X_test, y_test)
            
            self.is_trained = True
            self.last_train_time = np.datetime64('now')
            
            self.training_history.append({
                'rf_accuracy': rf_accuracy,
                'gb_accuracy': gb_accuracy,
                'samples': len(X),
                'timestamp': str(self.last_train_time)
            })
            
            print(f"ML Models trained: RF={rf_accuracy:.2%}, GB={gb_accuracy:.2%}")
            
            return True
            
        except Exception as e:
            print(f"Training error: {e}")
            return False
    
    def predict(self, candles: List[Dict], indicators: Dict) -> Dict:
        """Make prediction using ensemble of models"""
        try:
            if not self.is_trained:
                # Auto-train if not trained
                self.train(candles, indicators)
            
            features = self._prepare_features(candles, indicators)
            
            if features is None:
                return {
                    'direction': 'NEUTRAL',
                    'probability': 50,
                    'confidence': 0,
                    'model_agreement': 0
                }
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Get predictions from both models
            rf_prob = self.rf_model.predict_proba(features_scaled)[0]
            gb_prob = self.gb_model.predict_proba(features_scaled)[0]
            
            # Handle if model only learned one class
            rf_prob_bullish = rf_prob[1] if len(rf_prob) > 1 else (1.0 if self.rf_model.classes_[0] == 1 else 0.0)
            rf_prob_bearish = rf_prob[0] if len(rf_prob) > 1 else (1.0 if self.rf_model.classes_[0] == 0 else 0.0)
            
            gb_prob_bullish = gb_prob[1] if len(gb_prob) > 1 else (1.0 if self.gb_model.classes_[0] == 1 else 0.0)
            gb_prob_bearish = gb_prob[0] if len(gb_prob) > 1 else (1.0 if self.gb_model.classes_[0] == 0 else 0.0)
            
            # Ensemble prediction (weighted average)
            bullish_prob = (rf_prob_bullish * 0.5 + gb_prob_bullish * 0.5) * 100
            bearish_prob = (rf_prob_bearish * 0.5 + gb_prob_bearish * 0.5) * 100
            
            # Model agreement
            rf_pred = 1 if rf_prob_bullish > 0.5 else 0
            gb_pred = 1 if gb_prob_bullish > 0.5 else 0
            agreement = 100 if rf_pred == gb_pred else 50
            
            if bullish_prob > bearish_prob:
                direction = 'BULLISH'
            elif bearish_prob > bullish_prob:
                direction = 'BEARISH'
            else:
                direction = 'NEUTRAL'
            
            confidence = abs(bullish_prob - bearish_prob)
            
            # Feature importance (from Random Forest)
            top_features = self._get_top_features()
            
            return {
                'direction': direction,
                'bullish_prob': round(bullish_prob, 1),
                'bearish_prob': round(bearish_prob, 1),
                'confidence': round(confidence, 1),
                'model_agreement': agreement,
                'rf_prediction': 'BULLISH' if rf_pred == 1 else 'BEARISH',
                'gb_prediction': 'BULLISH' if gb_pred == 1 else 'BEARISH',
                'top_features': top_features
            }
            
        except Exception as e:
            print(f"Prediction error: {e}")
            return {
                'direction': 'NEUTRAL',
                'probability': 50,
                'confidence': 0,
                'error': str(e)
            }
    
    def _get_top_features(self) -> List[Dict]:
        """Get top important features from Random Forest"""
        if not self.is_trained or not self.feature_names:
            return []
        
        try:
            importances = self.rf_model.feature_importances_
            feature_importance = list(zip(self.feature_names, importances))
            feature_importance.sort(key=lambda x: x[1], reverse=True)
            
            return [
                {'name': name, 'importance': round(imp * 100, 1)}
                for name, imp in feature_importance[:5]
            ]
        except:
            return []
    
    def get_model_stats(self) -> Dict:
        """Get model training statistics"""
        return {
            'is_trained': self.is_trained,
            'last_train_time': str(self.last_train_time) if self.last_train_time else None,
            'training_history': self.training_history[-5:] if self.training_history else [],
            'feature_count': len(self.feature_names)
        }


# Singleton instance
ml_predictor = MLPredictor()


def get_ml_prediction(candles: List[Dict], indicators: Dict) -> Dict:
    """Get ML prediction for the given market data"""
    return ml_predictor.predict(candles, indicators)


def train_ml_model(candles: List[Dict], indicators: Dict) -> bool:
    """Train the ML model"""
    return ml_predictor.train(candles, indicators)


def get_model_stats() -> Dict:
    """Get ML model statistics"""
    return ml_predictor.get_model_stats()
