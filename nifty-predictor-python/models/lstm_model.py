"""
LSTM Model for Time Series Prediction
CNN-LSTM Architecture for Nifty/BankNifty prediction
"""

import numpy as np
import os
from typing import Tuple, Optional

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, Conv1D, Flatten, Input
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("WARNING: TensorFlow not installed. LSTM model disabled.")

from pro_config.model_config import LSTM_CONFIG


class LSTMModel:
    """CNN-LSTM model for price direction prediction"""
    
    def __init__(self, input_shape: Tuple[int, int] = None):
        self.model = None
        self.input_shape = input_shape or (LSTM_CONFIG['lookback_period'], 50)
        self.is_trained = False
        self.model_path = "models/lstm_model.h5"
        
        if TF_AVAILABLE:
            self._build_model()
            self._load_if_exists()
    
    def _build_model(self):
        """Build CNN-LSTM architecture"""
        if not TF_AVAILABLE:
            return
            
        self.model = Sequential([
            # Input
            Input(shape=self.input_shape),
            
            # Conv1D layers for feature extraction
            Conv1D(filters=LSTM_CONFIG['conv_filters'][0], kernel_size=3, 
                   activation='relu', padding='same'),
            Conv1D(filters=LSTM_CONFIG['conv_filters'][1], kernel_size=3, 
                   activation='relu', padding='same'),
            
            # LSTM layers
            LSTM(LSTM_CONFIG['units'][0], activation='relu', return_sequences=True),
            Dropout(LSTM_CONFIG['dropout']),
            LSTM(LSTM_CONFIG['units'][1], activation='relu'),
            Dropout(LSTM_CONFIG['dropout']),
            
            # Dense layers
            Dense(50, activation='relu'),
            Dense(25, activation='relu'),
            Dense(1, activation='sigmoid')
        ])
        
        self.model.compile(
            optimizer=Adam(learning_rate=LSTM_CONFIG['learning_rate']),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
    
    def _load_if_exists(self):
        """Load pre-trained model if exists"""
        if os.path.exists(self.model_path):
            try:
                self.model = load_model(self.model_path)
                self.is_trained = True
                print(f"LSTM model loaded from {self.model_path}")
            except Exception as e:
                print(f"Failed to load LSTM model: {e}")
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray, 
              X_val: np.ndarray = None, y_val: np.ndarray = None) -> dict:
        """Train the model"""
        if not TF_AVAILABLE or self.model is None:
            return {'accuracy': 0.5, 'loss': 1.0}
        
        callbacks = [
            EarlyStopping(patience=5, restore_best_weights=True)
        ]
        
        validation_data = (X_val, y_val) if X_val is not None else None
        
        history = self.model.fit(
            X_train, y_train,
            epochs=LSTM_CONFIG['epochs'],
            batch_size=LSTM_CONFIG['batch_size'],
            validation_data=validation_data,
            callbacks=callbacks,
            verbose=1
        )
        
        self.is_trained = True
        
        # Save model
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        self.model.save(self.model_path)
        
        return {
            'accuracy': history.history['accuracy'][-1],
            'loss': history.history['loss'][-1],
            'val_accuracy': history.history.get('val_accuracy', [0])[-1]
        }
    
    def predict(self, X: np.ndarray) -> Tuple[float, float]:
        """
        Predict direction
        Returns: (prediction, confidence)
        """
        if not TF_AVAILABLE or self.model is None:
            return 0.5, 0.5
        
        if len(X.shape) == 2:
            X = X.reshape(1, X.shape[0], X.shape[1])
        
        try:
            prob = self.model.predict(X, verbose=0)[0][0]
            prediction = 1 if prob > 0.5 else 0
            confidence = prob if prediction == 1 else (1 - prob)
            return prediction, confidence
        except Exception as e:
            print(f"LSTM prediction error: {e}")
            return 0.5, 0.5
    
    def predict_proba(self, X: np.ndarray) -> float:
        """Get raw probability for bullish signal"""
        if not TF_AVAILABLE or self.model is None:
            return 0.5
            
        if len(X.shape) == 2:
            X = X.reshape(1, X.shape[0], X.shape[1])
            
        try:
            return float(self.model.predict(X, verbose=0)[0][0])
        except:
            return 0.5


# Singleton instance
lstm_model = LSTMModel()
