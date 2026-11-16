# 🚀 Nifty Predictor Pro - Python ML Version

A professional-grade trading dashboard with **real-time data simulation** and **machine learning predictions** for NIFTY and Bank NIFTY.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![ML](https://img.shields.io/badge/ML-Scikit--Learn-orange)

## ✨ Features

### 🤖 Machine Learning Predictions
- **Ensemble ML Model**: Combines Random Forest and Gradient Boosting
- **Real-time Training**: Auto-trains on historical data
- **Feature Importance**: Shows which indicators drive predictions
- **Model Agreement**: Displays confidence when models agree

### 📊 18 Professional Trading Strategies
All strategies organized in **clickable tabs**:

| Category | Strategies |
|----------|------------|
| **Momentum** | RSI, MACD, Stochastic, CCI, Williams %R, MFI |
| **Trend** | MA Crossover, ADX, SuperTrend, Ichimoku, Parabolic SAR |
| **Volatility** | Bollinger Bands |
| **Volume** | VWAP, MFI |
| **Sentiment** | PCR, VIX, FII/DII Flow, Open Interest |

### 📈 Real-Time Data Simulator
- Realistic price movements with **volatility clustering**
- **Intraday patterns** (opening rush, lunch lull, closing volatility)
- Mean-reverting behavior
- Realistic volume profiles

### 🎯 Trade Recommendations
- Entry, Stop Loss, Target prices
- Risk-Reward ratio calculation
- Suggested lot size based on capital
- Profit projection at target

## 🚀 Quick Start

### Option 1: Using run.bat (Windows)
```bash
# Simply double-click run.bat or run:
.\run.bat
```

### Option 2: Manual Setup
```bash
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py
```

### Open Dashboard
Navigate to: **http://localhost:5000**

## 📁 Project Structure

```
nifty-predictor-python/
├── app.py              # Main Flask server
├── config.py           # Configuration settings
├── data_simulator.py   # Real-time market data simulator
├── indicators.py       # Technical indicators library
├── strategies.py       # 18 trading strategies
├── ml_predictor.py     # ML prediction engine
├── requirements.txt    # Python dependencies
├── run.bat            # Windows run script
├── templates/
│   └── index.html     # Main dashboard HTML
└── static/
    ├── styles.css     # Premium dark theme CSS
    └── app.js         # Frontend JavaScript
```

## 🔌 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/analysis` | Complete market analysis with ML predictions |
| `GET /api/candles` | Historical OHLCV candles |
| `GET /api/strategies` | All strategy signals |
| `GET /api/ml-prediction` | ML-only prediction |
| `GET /api/train-ml` | Trigger ML model retraining |
| `GET /api/option-chain` | Simulated option chain data |
| `GET /api/sentiment` | Market sentiment data |

## 🧠 How ML Prediction Works

1. **Feature Engineering**: Extracts 20+ features from price data and indicators
2. **Ensemble Prediction**: 
   - Random Forest (50% weight)
   - Gradient Boosting (50% weight)
3. **Confidence Scoring**: Higher when both models agree
4. **Auto-Retraining**: Retrains periodically on new data

## ⚙️ Configuration

Edit `config.py` to customize:

```python
TRADING_CONFIG = {
    'capital': 100000,      # Your trading capital
    'risk_percentage': 2,   # Risk per trade
    'min_lots': 1,
    'max_lots': 20
}
```

## 🎨 UI Features

- **Dark Theme**: Premium trading dashboard aesthetic
- **Live Updates**: WebSocket-based real-time data
- **Clickable Strategy Tabs**: Filter by category
- **Responsive Design**: Works on all screen sizes
- **Modal Details**: Click any strategy for full info

## ⚠️ Disclaimer

This tool is for **educational purposes only**. Trading involves significant risk. Always do your own research and never invest money you cannot afford to lose.

## 📝 License

MIT License - Feel free to use and modify!

---

Made with 💻 by Nifty Predictor Pro Team
