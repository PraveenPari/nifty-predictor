"""
Random Forest Model for Classification
Ensemble tree-based model for trading signals
"""

import numpy as np
import os
import pickle
from typing import Tuple

try:
    from sklearn.ensemble import RandomForestClassifier
    RF_AVAILABLE = True
except ImportError:
    RF_AVAILABLE = False
    print("WARNING: scikit-learn not installed.")

from pro_config.model_config import RANDOM_FOREST_CONFIG


class RandomForestModel:
    """Random Forest classifier for trading signals"""
    
    def __init__(self):
        self.model = None
        self.is_trained = False
        self.model_path = "models/random_forest_model.pkl"
        self.feature_importance = {}
        
        self._load_if_exists()
    
    def _load_if_exists(self):
        """Load pre-trained model if exists"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                self.is_trained = True
                print(f"RandomForest model loaded from {self.model_path}")
            except Exception as e:
                print(f"Failed to load RandomForest model: {e}")
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: np.ndarray = None, y_val: np.ndarray = None,
              feature_names: list = None) -> dict:
        """Train Random Forest model"""
        if not RF_AVAILABLE:
            return {'accuracy': 0.5}
        
        self.model = RandomForestClassifier(
            n_estimators=RANDOM_FOREST_CONFIG['n_estimators'],
            max_depth=RANDOM_FOREST_CONFIG['max_depth'],
            min_samples_split=RANDOM_FOREST_CONFIG['min_samples_split'],
            min_samples_leaf=RANDOM_FOREST_CONFIG['min_samples_leaf'],
            max_features=RANDOM_FOREST_CONFIG['max_features'],
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Extract feature importance
        if feature_names:
            importance = self.model.feature_importances_
            self.feature_importance = dict(zip(feature_names, importance))
        
        # Save model
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
        
        # Calculate accuracy
        train_acc = self.model.score(X_train, y_train)
        val_acc = self.model.score(X_val, y_val) if X_val is not None else 0
        
        return {
            'accuracy': train_acc,
            'val_accuracy': val_acc
        }
    
    def predict(self, X: np.ndarray) -> Tuple[int, float]:
        """
        Predict direction
        Returns: (prediction, confidence)
        """
        if not RF_AVAILABLE or self.model is None:
            return 0, 0.5
        
        if len(X.shape) == 1:
            X = X.reshape(1, -1)
        
        try:
            prediction = int(self.model.predict(X)[0])
            proba = self.model.predict_proba(X)[0]
            confidence = proba[prediction]
            return prediction, confidence
        except Exception as e:
            print(f"RandomForest prediction error: {e}")
            return 0, 0.5
    
    def predict_proba(self, X: np.ndarray) -> float:
        """Get probability for bullish signal (class 1)"""
        if not RF_AVAILABLE or self.model is None:
            return 0.5
            
        if len(X.shape) == 1:
            X = X.reshape(1, -1)
            
        try:
            return float(self.model.predict_proba(X)[0][1])
        except:
            return 0.5
    
    def get_top_features(self, n: int = 10) -> dict:
        """Get top N most important features"""
        if not self.feature_importance:
            return {}
        sorted_features = sorted(self.feature_importance.items(), 
                                 key=lambda x: x[1], reverse=True)
        return dict(sorted_features[:n])


# Singleton instance
random_forest_model = RandomForestModel()
