# Model Configuration

# LSTM Settings
LSTM_CONFIG = {
    'lookback_period': 60,
    'epochs': 20,
    'batch_size': 32,
    'learning_rate': 0.0005,
    'dropout': 0.3,
    'units': [100, 50],
    'conv_filters': [64, 32]
}

# XGBoost Settings
XGBOOST_CONFIG = {
    'n_estimators': 300,
    'max_depth': 8,
    'learning_rate': 0.05,
    'subsample': 0.9,
    'colsample_bytree': 0.85,
    'gamma': 1,
    'min_child_weight': 1,
    'early_stopping_rounds': 10
}

# Random Forest Settings
RANDOM_FOREST_CONFIG = {
    'n_estimators': 200,
    'max_depth': 10,
    'min_samples_split': 5,
    'min_samples_leaf': 2,
    'max_features': 'sqrt'
}

# Ensemble Weights
ENSEMBLE_WEIGHTS = {
    'lstm': 0.30,
    'xgboost': 0.50,
    'random_forest': 0.20
}

# Confidence threshold for signals
CONFIDENCE_THRESHOLD = 0.55
