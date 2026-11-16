"""
LSTM Neural Network Predictor
Deep learning model for sequential pattern recognition in price data
Uses TensorFlow/Keras (free, open-source)
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Try to import TensorFlow/Keras
try:
    import tensorflow as tf
    tf.get_logger().setLevel('ERROR')
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("INFO: TensorFlow not installed. LSTM predictions disabled.")
    print("      Install with: pip install tensorflow")

from sklearn.preprocessing import MinMaxScaler


class LSTMPredictor:
    """
    LSTM-based predictor for learning sequential patterns in price data.
    Analyzes last N candles to predict next direction.
    """
    
    def __init__(self, sequence_length: int = 30, 
                 lstm_units: int = 64,
                 epochs: int = 50):
        self.sequence_length = sequence_length
        self.lstm_units = lstm_units
        self.epochs = epochs
        self.model = None
        self.scaler = MinMaxScaler()
        self.is_trained = False
        self.training_history = None
        self.last_accuracy = 0
        
    def _build_model(self, n_features: int):
        """Build LSTM model architecture"""
        if not TENSORFLOW_AVAILABLE:
            return None
            
        model = Sequential([
            # First LSTM layer with return sequences
            LSTM(self.lstm_units, 
                 return_sequences=True, 
                 input_shape=(self.sequence_length, n_features)),
            BatchNormalization(),
            Dropout(0.2),
            
            # Second LSTM layer
            LSTM(self.lstm_units // 2, return_sequences=False),
            BatchNormalization(),
            Dropout(0.2),
            
            # Dense layers
            Dense(32, activation='relu'),
            Dropout(0.1),
            Dense(16, activation='relu'),
            
            # Output layer (probability of bullish)
            Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
        
    def _prepare_features(self, candles: List[Dict]) -> np.ndarray:
        """Prepare feature matrix from candles"""
        features = []
        
        for candle in candles:
            close = candle.get('close', candle.get('Close', 0))
            high = candle.get('high', candle.get('High', close))
            low = candle.get('low', candle.get('Low', close))
            open_ = candle.get('open', candle.get('Open', close))
            volume = candle.get('volume', candle.get('Volume', 1))
            
            # Feature engineering
            range_pct = (high - low) / close * 100 if close > 0 else 0
            body_pct = abs(close - open_) / close * 100 if close > 0 else 0
            upper_wick = (high - max(close, open_)) / close * 100 if close > 0 else 0
            lower_wick = (min(close, open_) - low) / close * 100 if close > 0 else 0
            is_bullish = 1 if close > open_ else 0
            
            features.append([
                close,
                high - low,  # Range
                range_pct,
                body_pct,
                upper_wick,
                lower_wick,
                is_bullish,
                np.log1p(volume)  # Log-scaled volume
            ])
            
        return np.array(features)
        
    def _create_sequences(self, data: np.ndarray, 
                          targets: np.ndarray = None) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Create sequences for LSTM training"""
        X = []
        y = [] if targets is not None else None
        
        for i in range(len(data) - self.sequence_length):
            X.append(data[i:i + self.sequence_length])
            if targets is not None:
                y.append(targets[i + self.sequence_length])
                
        X = np.array(X)
        y = np.array(y) if y is not None else None
        
        return X, y
        
    def train(self, candles: List[Dict], 
              prediction_horizon: int = 3) -> bool:
        """
        Train LSTM on historical candle data
        prediction_horizon: how many candles ahead to predict
        """
        if not TENSORFLOW_AVAILABLE:
            print("[LSTM] TensorFlow not available")
            return False
            
        if len(candles) < self.sequence_length + prediction_horizon + 50:
            print(f"[LSTM] Need at least {self.sequence_length + prediction_horizon + 50} candles")
            return False
            
        try:
            print(f"[LSTM] Training on {len(candles)} candles...")
            
            # Prepare features
            features = self._prepare_features(candles)
            
            # Scale features
            features_scaled = self.scaler.fit_transform(features)
            
            # Create targets (1 if price goes up in next N candles)
            closes = [c.get('close', c.get('Close', 0)) for c in candles]
            targets = []
            for i in range(len(closes) - prediction_horizon):
                future_price = closes[i + prediction_horizon]
                current_price = closes[i]
                # 1 if price increases by at least 0.1%
                targets.append(1 if future_price > current_price * 1.001 else 0)
            targets = np.array(targets)
            
            # Trim features to match targets
            features_scaled = features_scaled[:len(targets)]
            
            # Create sequences
            X, y = self._create_sequences(features_scaled, targets)
            
            if len(X) < 50:
                print("[LSTM] Not enough sequences for training")
                return False
                
            # Split data (time-series aware - no shuffling)
            split_idx = int(len(X) * 0.8)
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            # Build model
            n_features = X.shape[2]
            self.model = self._build_model(n_features)
            
            if self.model is None:
                return False
                
            # Early stopping to prevent overfitting
            early_stop = EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            )
            
            # Train
            self.training_history = self.model.fit(
                X_train, y_train,
                epochs=self.epochs,
                batch_size=32,
                validation_data=(X_val, y_val),
                callbacks=[early_stop],
                verbose=0
            )
            
            # Evaluate
            _, accuracy = self.model.evaluate(X_val, y_val, verbose=0)
            self.last_accuracy = accuracy
            self.is_trained = True
            
            print(f"[LSTM] Training complete! Validation accuracy: {accuracy:.1%}")
            
            return True
            
        except Exception as e:
            print(f"[LSTM] Training error: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def predict(self, candles: List[Dict]) -> Dict:
        """
        Predict direction using trained LSTM
        Returns prediction with confidence
        """
        if not TENSORFLOW_AVAILABLE:
            return self._neutral_prediction("TensorFlow not available")
            
        if not self.is_trained or self.model is None:
            return self._neutral_prediction("Model not trained")
            
        if len(candles) < self.sequence_length:
            return self._neutral_prediction("Insufficient data")
            
        try:
            # Prepare features for last sequence
            features = self._prepare_features(candles[-self.sequence_length:])
            features_scaled = self.scaler.transform(features)
            
            # Reshape for LSTM
            X = features_scaled.reshape(1, self.sequence_length, -1)
            
            # Predict
            prob = self.model.predict(X, verbose=0)[0][0]
            
            # Convert to direction and confidence
            if prob > 0.55:
                direction = 'BULLISH'
                confidence = round(prob * 100)
            elif prob < 0.45:
                direction = 'BEARISH'
                confidence = round((1 - prob) * 100)
            else:
                direction = 'NEUTRAL'
                confidence = 50
                
            return {
                'direction': direction,
                'confidence': confidence,
                'raw_probability': round(float(prob), 4),
                'model': 'LSTM',
                'model_accuracy': round(self.last_accuracy * 100, 1),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"[LSTM] Prediction error: {e}")
            return self._neutral_prediction(str(e))
            
    def _neutral_prediction(self, reason: str) -> Dict:
        """Return neutral prediction with reason"""
        return {
            'direction': 'NEUTRAL',
            'confidence': 0,
            'raw_probability': 0.5,
            'model': 'LSTM',
            'model_accuracy': 0,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
        
    def get_stats(self) -> Dict:
        """Get LSTM model statistics"""
        return {
            'available': TENSORFLOW_AVAILABLE,
            'is_trained': self.is_trained,
            'accuracy': round(self.last_accuracy * 100, 1) if self.last_accuracy else 0,
            'sequence_length': self.sequence_length,
            'lstm_units': self.lstm_units,
            'epochs_trained': len(self.training_history.history['loss']) if self.training_history else 0
        }


# Singleton instance
lstm_predictor = LSTMPredictor(sequence_length=30, lstm_units=64, epochs=50)


def train_lstm(candles: List[Dict]) -> bool:
    """Train the LSTM model"""
    return lstm_predictor.train(candles)


def get_lstm_prediction(candles: List[Dict]) -> Dict:
    """Get LSTM prediction"""
    return lstm_predictor.predict(candles)


def get_lstm_stats() -> Dict:
    """Get LSTM model statistics"""
    return lstm_predictor.get_stats()


def is_lstm_available() -> bool:
    """Check if LSTM is available"""
    return TENSORFLOW_AVAILABLE
