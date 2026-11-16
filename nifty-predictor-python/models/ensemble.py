"""
Ensemble Model
Weighted voting system combining LSTM + XGBoost + RandomForest
"""

import numpy as np
from typing import Dict, Tuple, Optional

from pro_config.model_config import ENSEMBLE_WEIGHTS, CONFIDENCE_THRESHOLD
from .lstm_model import lstm_model
from .xgboost_model import xgboost_model
from .random_forest_model import random_forest_model


class EnsembleModel:
    """Weighted voting ensemble for trading signals"""
    
    def __init__(self):
        self.weights = ENSEMBLE_WEIGHTS
        self.confidence_threshold = CONFIDENCE_THRESHOLD
        self.last_prediction = None
        self.model_predictions = {}
    
    def predict(self, X_sequence: np.ndarray, X_features: np.ndarray) -> Dict:
        """
        Get ensemble prediction from all models
        
        Args:
            X_sequence: Sequence data for LSTM (shape: lookback x features)
            X_features: Feature vector for XGBoost/RF (shape: features)
        
        Returns:
            Dict with signal, confidence, and individual model predictions
        """
        predictions = {}
        probabilities = {}
        
        # LSTM prediction (needs sequence data)
        if lstm_model.is_trained or lstm_model.model is not None:
            lstm_prob = lstm_model.predict_proba(X_sequence)
            predictions['lstm'] = 1 if lstm_prob > 0.5 else 0
            probabilities['lstm'] = lstm_prob
        else:
            probabilities['lstm'] = 0.5
            predictions['lstm'] = 0
        
        # XGBoost prediction
        if xgboost_model.is_trained or xgboost_model.model is not None:
            xgb_prob = xgboost_model.predict_proba(X_features)
            predictions['xgboost'] = 1 if xgb_prob > 0.5 else 0
            probabilities['xgboost'] = xgb_prob
        else:
            probabilities['xgboost'] = 0.5
            predictions['xgboost'] = 0
        
        # Random Forest prediction
        if random_forest_model.is_trained or random_forest_model.model is not None:
            rf_prob = random_forest_model.predict_proba(X_features)
            predictions['random_forest'] = 1 if rf_prob > 0.5 else 0
            probabilities['random_forest'] = rf_prob
        else:
            probabilities['random_forest'] = 0.5
            predictions['random_forest'] = 0
        
        # Weighted ensemble
        ensemble_prob = (
            probabilities['lstm'] * self.weights['lstm'] +
            probabilities['xgboost'] * self.weights['xgboost'] +
            probabilities['random_forest'] * self.weights['random_forest']
        )
        
        # Determine signal type
        signal = self._determine_signal(ensemble_prob, predictions)
        
        # All models agreement
        all_agree = len(set(predictions.values())) == 1
        
        result = {
            'ensemble_probability': round(ensemble_prob, 4),
            'ensemble_signal': 1 if ensemble_prob > 0.5 else 0,
            'signal_type': signal,
            'confidence': round(abs(ensemble_prob - 0.5) * 2, 4),
            'bullish_prob': round(ensemble_prob * 100, 2),
            'bearish_prob': round((1 - ensemble_prob) * 100, 2),
            'model_predictions': predictions,
            'model_probabilities': {k: round(v, 4) for k, v in probabilities.items()},
            'models_agree': all_agree,
            'direction': 'BULLISH' if ensemble_prob > 0.5 else 'BEARISH'
        }
        
        self.last_prediction = result
        self.model_predictions = predictions
        
        return result
    
    def _determine_signal(self, prob: float, predictions: Dict) -> str:
        """Determine signal type based on probability and model agreement"""
        all_bullish = all(p == 1 for p in predictions.values())
        all_bearish = all(p == 0 for p in predictions.values())
        
        if prob > 0.70 and all_bullish:
            return "STRONG_BUY"
        elif prob > self.confidence_threshold:
            return "BUY"
        elif prob < 0.30 and all_bearish:
            return "STRONG_SELL"
        elif prob < (1 - self.confidence_threshold):
            return "SELL"
        else:
            return "HOLD"
    
    def get_model_status(self) -> Dict:
        """Get status of all models"""
        return {
            'lstm': {
                'available': lstm_model.model is not None,
                'trained': lstm_model.is_trained,
                'weight': self.weights['lstm']
            },
            'xgboost': {
                'available': xgboost_model.model is not None,
                'trained': xgboost_model.is_trained,
                'weight': self.weights['xgboost']
            },
            'random_forest': {
                'available': random_forest_model.model is not None,
                'trained': random_forest_model.is_trained,
                'weight': self.weights['random_forest']
            }
        }
    
    def get_feature_importance(self) -> Dict:
        """Get combined feature importance from tree models"""
        xgb_importance = xgboost_model.get_top_features(20)
        rf_importance = random_forest_model.get_top_features(20)
        
        # Combine and average
        combined = {}
        all_features = set(xgb_importance.keys()) | set(rf_importance.keys())
        
        for feature in all_features:
            xgb_val = xgb_importance.get(feature, 0)
            rf_val = rf_importance.get(feature, 0)
            combined[feature] = (xgb_val * 0.7 + rf_val * 0.3)
        
        sorted_combined = sorted(combined.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_combined[:15])


# Singleton instance
ensemble_model = EnsembleModel()
