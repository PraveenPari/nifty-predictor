# Nifty Predictor Suite

Professional algorithmic market prediction and trade analysis system for NIFTY 50 and BANK NIFTY, powered by Python Machine Learning models and Node.js proxy server.

---

## 📁 Repository Structure

```
.
├── nifty-predictor-python/     # Python Flask Server & ML Prediction Engine
│   ├── app.py                  # Main Flask application & API routes
│   ├── breeze_manager.py       # ICICI Direct Breeze API integration
│   ├── trade_analytics.py      # Trade signal generation, validation & win rate calculation
│   ├── ml_predictor.py         # ML model training and inference
│   ├── templates/              # HTML UI templates
│   └── static/                 # TradingView charts, JavaScript and CSS
└── nifty-predictor/            # Node.js Express Proxy & Bridge
    ├── server.js               # Express server on port 3001
    └── package.json            # Node dependencies
```

---

## 🚀 Quick Start

### 1. Python ML Server (`nifty-predictor-python`)
```bash
cd nifty-predictor-python
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Fill in your BREEZE_API_KEY, BREEZE_SECRET_KEY, and BREEZE_SESSION_TOKEN

# Start Flask server (port 5000)
python app.py
```

### 2. Node.js Proxy (`nifty-predictor`)
```bash
cd nifty-predictor
npm install
node server.js
```

---

## 🛡️ Security Note
All sensitive API keys and session tokens are excluded via `.gitignore`. Never commit `.env` files with active API credentials to public repositories.
