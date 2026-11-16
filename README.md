# Nifty Predictor Suite

Professional algorithmic market prediction and trade analysis system for NIFTY 50 and BANK NIFTY — Python ML engine + Node.js bridge. 33 strategies (18 classic + 15 pro), live Breeze/Angel One/Yahoo data fusion, and one-command free hosting.

---

## 📁 Repository Structure

```
.
├── nifty-predictor-python/     # Python Flask Server & ML Prediction Engine
│   ├── app.py                  # Main Flask application & API routes
│   ├── secrets_manager.py      # SINGLE choke point for all secrets (env-only)
│   ├── breeze_manager.py       # ICICI Direct Breeze API integration
│   ├── strategies.py           # 18 classic indicator strategies
│   ├── pro_strategies.py       # 15 pro strategies + confluence verdict
│   ├── indicators_fast.py      # Vectorized indicator engine (25 indicators)
│   ├── trade_analytics.py      # Trade signal generation, validation & win rate
│   ├── ml_predictor.py         # ML model training and inference
│   ├── requirements.txt        # Slim deploy-ready deps (free hosts)
│   ├── requirements-full.txt   # Full local ML stack (TF/XGB/LGBM/...)
│   ├── Dockerfile / render.yaml / railway.json / gunicorn.conf.py
│   ├── DEPLOYMENT_GUIDE.md     # Free hosting walkthrough
│   ├── SECURITY.md             # Secrets handling policy
│   ├── templates/              # HTML UI templates
│   ├── static/                 # Charts, JavaScript and CSS
│   └── frontend/               # Optional React + Vite dashboard
└── nifty-predictor/            # Node.js Express Proxy & Bridge
    ├── server.js               # Bridge on $PORT (default 3001)
    └── package.json            # Node dependencies
```

---

## 🚀 Quick Start

### 1. Python ML Server (`nifty-predictor-python`)
```bash
cd nifty-predictor-python
python -m venv .venv
# Windows: .\.venv\Scripts\activate | Mac/Linux: source .venv/bin/activate

pip install -r requirements.txt          # slim (works everywhere)
# pip install -r requirements-full.txt  # optional heavy ML stack

cp .env.example .env
# Fill in BREEZE_API_KEY, BREEZE_SECRET_KEY, BREEZE_SESSION_TOKEN

python app.py                            # Dashboard: http://127.0.0.1:5000
```

Without Breeze secrets the app still runs on free Yahoo Finance data —
Breeze features enable automatically once secrets are set.

### 2. Node.js Bridge (`nifty-predictor`, optional)
```bash
cd nifty-predictor
npm install
node server.js   # or: PORT=3001 FLASK_BACKEND=http://127.0.0.1:5000 node server.js
```

---

## 🎯 Pro Strategies (15)

ORB-15 Breakout · VWAP Institutional Bias · EMA 9/21 Ribbon ·
SuperTrend × ADX Filter · Bollinger Squeeze Breakout · Donchian 20 ·
Keltner Volume Thrust · ATR Chandelier · OBV Smart-Money Check ·
RSI Divergence Pro · Max-OI Support/Resistance · Max-Pain Magnet ·
PCR Extreme + VIX Regime · Heikin-Ashi Trend State ·
Pivot + VWAP Confluence — every signal ships entry/SL/target, fused into a
**PRO CONFLUENCE verdict** (`GET /api/pro-strategies`).

## ☁️ Free Hosting

Render (`render.yaml`), Railway (`railway.json`), Fly.io (`Dockerfile`) —
free HTTPS domains included. Full steps: [`DEPLOYMENT_GUIDE.md`](nifty-predictor-python/DEPLOYMENT_GUIDE.md).

## 🛡️ Security

Secrets live **only** in environment variables / host Secrets dashboards —
never in code, logs, or API responses. See [`SECURITY.md`](nifty-predictor-python/SECURITY.md).
`.env` files are git-ignored. If you ever committed a real key, **rotate it**
immediately in the ICICI Direct portal.
