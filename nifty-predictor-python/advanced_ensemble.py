"""
Advanced Ensemble Module (Enhanced)
Combines multiple ML models with regime-aware predictions
Includes: LightGBM, CatBoost, XGBoost, Random Forest, Gradient Boosting
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import warnings
import os
from datetime import datetime

warnings.filterwarnings('ignore')

# Import advanced classifiers with graceful fallbacks
try:
    from lightgbm import LGBMClassifier
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    print("INFO: LightGBM not installed. Using fallback models.")

try:
    from catboost import CatBoostClassifier
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False
    print("INFO: CatBoost not installed. Using fallback models.")

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("INFO: XGBoost not installed. Using fallback models.")

from sklearn.ensemble import (
    RandomForestClassifier, 
    VotingClassifier, 
    GradientBoostingClassifier,
    AdaBoostClassifier,
    ExtraTreesClassifier
)
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import TimeSeriesSplit


class AdvancedEnsemble(BaseEstimator, ClassifierMixin):
    """
    Advanced Voting Ensemble with regime-aware predictions
    Uses: LightGBM + CatBoost + XGBoost + Random Forest + Extra Trees + MLP
    """
    
    def __init__(self, regime: str = None):
        self.estimators = []
        self.voting_clf = None
        self.is_fitted = False
        self.scaler = StandardScaler()
        self.regime = regime
        self.model_weights = {}
        self.training_accuracy = 0
        self.feature_importance = {}
        self._build_model()
        
    def _build_model(self):
        """Initialize the constituent models with regime-aware parameters"""
        models = []
        
        # Adjust parameters based on regime
        n_estimators_base = 300
        if self.regime == 'HIGH_VOLATILITY':
            n_estimators_base = 500  # More trees for volatile markets
        elif self.regime == 'SIDEWAYS':
            n_estimators_base = 200  # Fewer trees for ranging markets
            
        # 1. LightGBM (Gradient Boosting - Fast & Accurate)
        if LIGHTGBM_AVAILABLE:
            lgbm = LGBMClassifier(
                n_estimators=n_estimators_base,
                learning_rate=0.03,
                num_leaves=31,
                max_depth=8,
                min_child_samples=20,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.1,
                reg_lambda=0.1,
                random_state=42,
                n_jobs=-1,
                verbose=-1,
                importance_type='gain'
            )
            models.append(('lgbm', lgbm))
            self.model_weights['lgbm'] = 0.25
            
        # 2. CatBoost (Categorical Boosting - Robust)
        if CATBOOST_AVAILABLE:
            cat = CatBoostClassifier(
                iterations=n_estimators_base,
                learning_rate=0.03,
                depth=7,
                l2_leaf_reg=3,
                random_seed=42,
                verbose=0,
                allow_writing_files=False,
                thread_count=-1
            )
            models.append(('cat', cat))
            self.model_weights['cat'] = 0.25
            
        # 3. XGBoost (Extreme Gradient Boosting)
        if XGBOOST_AVAILABLE:
            xgb = XGBClassifier(
                n_estimators=n_estimators_base,
                learning_rate=0.03,
                max_depth=7,
                min_child_weight=3,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.1,
                reg_lambda=0.1,
                random_state=42,
                n_jobs=-1,
                verbosity=0,
                use_label_encoder=False,
                eval_metric='logloss'
            )
            models.append(('xgb', xgb))
            self.model_weights['xgb'] = 0.2
            
        # 4. Random Forest (Bagging - Stability)
        rf = RandomForestClassifier(
            n_estimators=int(n_estimators_base * 0.7),
            max_depth=12,
            min_samples_split=5,
            min_samples_leaf=3,
            max_features='sqrt',
            random_state=42,
            n_jobs=None,
            class_weight='balanced'
        )
        models.append(('rf', rf))
        self.model_weights['rf'] = 0.15
        
        # 5. Extra Trees (More randomization)
        et = ExtraTreesClassifier(
            n_estimators=int(n_estimators_base * 0.5),
            max_depth=10,
            min_samples_split=4,
            random_state=42,
            n_jobs=None,
            class_weight='balanced'
        )
        models.append(('et', et))
        self.model_weights['et'] = 0.1
        
        # 6. MLP Neural Network (for non-linear patterns)
        mlp = MLPClassifier(
            hidden_layer_sizes=(100, 50, 25),
            activation='relu',
            solver='adam',
            alpha=0.01,
            learning_rate='adaptive',
            max_iter=500,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.1
        )
        models.append(('mlp', mlp))
        self.model_weights['mlp'] = 0.05
        
        self.estimators = models
        
        # Create Voting Classifier with soft voting (probability based)
        # Adjust n_jobs to avoid joblib/loky crash on Windows
        n_jobs = 1
        
        self.voting_clf = VotingClassifier(
            estimators=models,
            voting='soft',
            n_jobs=n_jobs
        )
        
    def fit(self, X, y, sample_weight=None, use_calibration=True, use_walkforward=True):
        """Train the ensemble with calibration and walk-forward validation"""
        if not self.voting_clf:
            self._build_model()
            
        # Scale features for MLP
        X_scaled = self.scaler.fit_transform(X)
        
        # Walk-forward validation scores
        walkforward_scores = []
        
        # Train voting classifier
        try:
            # Use time-series aware walk-forward validation
            if use_walkforward and len(X_scaled) >= 100:
                tscv = TimeSeriesSplit(n_splits=5)
                for train_idx, val_idx in tscv.split(X_scaled):
                    X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
                    y_train, y_val = y[train_idx], y[val_idx]
                    
                    # Temporarily fit on this fold
                    self.voting_clf.fit(X_train, y_train)
                    fold_score = self.voting_clf.score(X_val, y_val)
                    walkforward_scores.append(fold_score)
                    
                self.walkforward_accuracy = np.mean(walkforward_scores) if walkforward_scores else 0
                print(f"[ENSEMBLE] Walk-forward CV accuracy: {self.walkforward_accuracy:.1%}")
            
            # Final fit on all data
            self.voting_clf.fit(X_scaled, y)
            
            # Wrap with probability calibration for better confidence scores
            if use_calibration and len(X_scaled) >= 50:
                try:
                    self.calibrated_clf = CalibratedClassifierCV(
                        self.voting_clf, 
                        method='isotonic',
                        cv=3
                    )
                    self.calibrated_clf.fit(X_scaled, y)
                    self.use_calibrated = True
                    print("[ENSEMBLE] Probability calibration applied")
                except Exception as cal_error:
                    print(f"[ENSEMBLE] Calibration failed: {cal_error}")
                    self.use_calibrated = False
            else:
                self.use_calibrated = False
                
            self.is_fitted = True
            
            # Calculate training accuracy
            predictions = self.voting_clf.predict(X_scaled)
            self.training_accuracy = np.mean(predictions == y)
            
            # Extract feature importance from tree-based models
            self._extract_feature_importance()
            
        except Exception as e:
            print(f"Ensemble training error: {e}")
            # Fallback to just Random Forest
            rf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=None)
            rf.fit(X_scaled, y)
            self.voting_clf = rf
            self.is_fitted = True
            self.use_calibrated = False
            
        return self
        
    def _extract_feature_importance(self):
        """Extract and aggregate feature importance from tree models"""
        importance_sum = None
        count = 0
        
        for name, model in self.voting_clf.estimators_:
            try:
                if hasattr(model, 'feature_importances_'):
                    if importance_sum is None:
                        importance_sum = model.feature_importances_.copy()
                    else:
                        importance_sum += model.feature_importances_
                    count += 1
            except:
                pass
                
        if importance_sum is not None and count > 0:
            self.feature_importance = importance_sum / count
            
    def predict(self, X):
        """Predict class labels"""
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted yet")
            
        X_scaled = self.scaler.transform(X)
        return self.voting_clf.predict(X_scaled)
        
    def predict_proba(self, X):
        """Predict class probabilities (calibrated when available)"""
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted yet")
            
        X_scaled = self.scaler.transform(X)
        
        # Use calibrated classifier for more accurate probabilities
        if hasattr(self, 'use_calibrated') and self.use_calibrated and hasattr(self, 'calibrated_clf'):
            return self.calibrated_clf.predict_proba(X_scaled)
        return self.voting_clf.predict_proba(X_scaled)
        
    def predict_with_confidence(self, X) -> Tuple[np.ndarray, np.ndarray]:
        """Predict with confidence scores"""
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted yet")
            
        X_scaled = self.scaler.transform(X)
        probas = self.voting_clf.predict_proba(X_scaled)
        predictions = np.argmax(probas, axis=1)
        confidence = np.max(probas, axis=1)
        
        return predictions, confidence
        
    def get_individual_predictions(self, X) -> Dict[str, Tuple[int, float]]:
        """Get predictions from each individual model"""
        if not self.is_fitted:
            return {}
            
        X_scaled = self.scaler.transform(X)
        results = {}
        
        for name, model in self.voting_clf.estimators_:
            try:
                if hasattr(model, 'predict_proba'):
                    proba = model.predict_proba(X_scaled)
                    pred = np.argmax(proba, axis=1)[0]
                    conf = np.max(proba, axis=1)[0]
                    results[name] = (pred, conf)
            except Exception as e:
                results[name] = (0, 0)
                
        return results
        
    def get_model_info(self) -> Dict[str, Any]:
        """Get info about the internal models"""
        return {
            'lightgbm': LIGHTGBM_AVAILABLE,
            'catboost': CATBOOST_AVAILABLE,
            'xgboost': XGBOOST_AVAILABLE,
            'estimators': [name for name, _ in self.estimators],
            'weights': self.model_weights,
            'is_fitted': self.is_fitted,
            'training_accuracy': round(self.training_accuracy, 4),
            'regime': self.regime
        }
        
    def get_top_features(self, n: int = 10) -> List[Tuple[int, float]]:
        """Get top N important feature indices"""
        if len(self.feature_importance) == 0:
            return []
            
        indices = np.argsort(self.feature_importance)[::-1][:n]
        return [(int(i), float(self.feature_importance[i])) for i in indices]


class RegimeAwareEnsemble:
    """
    Ensemble that adapts based on detected market regime
    Maintains separate models for different market conditions
    """
    
    def __init__(self):
        self.regime_models = {}
        self.default_model = AdvancedEnsemble()
        self.current_regime = None
        self.scaler = StandardScaler()
        
    def fit(self, X, y, regime: str = None):
        """Fit model, optionally for a specific regime"""
        if regime:
            if regime not in self.regime_models:
                self.regime_models[regime] = AdvancedEnsemble(regime=regime)
            self.regime_models[regime].fit(X, y)
        else:
            self.default_model.fit(X, y)
            
        return self
        
    def predict(self, X, regime: str = None):
        """Predict using regime-appropriate model"""
        model = self.regime_models.get(regime, self.default_model)
        if not model.is_fitted:
            model = self.default_model
        return model.predict(X)
        
    def predict_proba(self, X, regime: str = None):
        """Predict probabilities using regime-appropriate model"""
        model = self.regime_models.get(regime, self.default_model)
        if not model.is_fitted:
            model = self.default_model
        return model.predict_proba(X)
        
    def get_model_for_regime(self, regime: str):
        """Get the model for a specific regime"""
        return self.regime_models.get(regime, self.default_model)


# Global instance factory
def get_advanced_model(regime: str = None) -> AdvancedEnsemble:
    """Create a new advanced ensemble model"""
    return AdvancedEnsemble(regime=regime)


def get_regime_aware_ensemble() -> RegimeAwareEnsemble:
    """Create a new regime-aware ensemble"""
    return RegimeAwareEnsemble()


# For backward compatibility
_default_model = None

def get_default_model() -> AdvancedEnsemble:
    """Get or create the default model instance"""
    global _default_model
    if _default_model is None:
        _default_model = AdvancedEnsemble()
    return _default_model
