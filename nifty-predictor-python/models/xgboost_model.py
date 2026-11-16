"""
XGBoost Model for Classification
High-performance gradient boosting for trading signals
"""

import numpy as np
import os
import pickle
from typing import Tuple, Optional

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    print("WARNING: XGBoost not installed.")

from pro_config.model_config import XGBOOST_CONFIG


class XGBoostModel:
    """XGBoost classifier for trading signals"""
    
    def __init__(self):
        self.model = None
        self.is_trained = False
        self.model_path = "models/xgboost_model.pkl"
        self.feature_importance = {}
        
        self._load_if_exists()
    
    def _load_if_exists(self):
        """Load pre-trained model if exists"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                self.is_trained = True
                print(f"XGBoost model loaded from {self.model_path}")
            except Exception as e:
                print(f"Failed to load XGBoost model: {e}")
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: np.ndarray = None, y_val: np.ndarray = None,
              feature_names: list = None) -> dict:
        """Train XGBoost model"""
        if not XGB_AVAILABLE:
            return {'accuracy': 0.5}
        
        eval_set = [(X_train, y_train)]
        if X_val is not None:
            eval_set.append((X_val, y_val))
        
        self.model = xgb.XGBClassifier(
            n_estimators=XGBOOST_CONFIG['n_estimators'],
            max_depth=XGBOOST_CONFIG['max_depth'],
            learning_rate=XGBOOST_CONFIG['learning_rate'],
            subsample=XGBOOST_CONFIG['subsample'],
            colsample_bytree=XGBOOST_CONFIG['colsample_bytree'],
            gamma=XGBOOST_CONFIG['gamma'],
            min_child_weight=XGBOOST_CONFIG['min_child_weight'],
            eval_metric='logloss',
            early_stopping_rounds=XGBOOST_CONFIG['early_stopping_rounds'],
            use_label_encoder=False,
            random_state=42
        )
        
        self.model.fit(
            X_train, y_train,
            eval_set=eval_set,
            verbose=False
        )
        
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
        if not XGB_AVAILABLE or self.model is None:
            return 0, 0.5
        
        if len(X.shape) == 1:
            X = X.reshape(1, -1)
        
        try:
            prediction = int(self.model.predict(X)[0])
            proba = self.model.predict_proba(X)[0]
            confidence = proba[prediction]
            return prediction, confidence
        except Exception as e:
            print(f"XGBoost prediction error: {e}")
            return 0, 0.5
    
    def predict_proba(self, X: np.ndarray) -> float:
        """Get probability for bullish signal (class 1)"""
        if not XGB_AVAILABLE or self.model is None:
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
xgboost_model = XGBoostModel()
