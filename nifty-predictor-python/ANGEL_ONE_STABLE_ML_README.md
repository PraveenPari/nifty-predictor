# Nifty Predictor with Angel One Integration & Stable ML

## 🚀 New Features

### 1. Angel One SmartAPI Integration
- **Real-time LTP**: Get live prices directly from Angel One
- **Historical Candles**: Fetch 5-minute candle data
- **Option Chain**: Access option chain data (with API limitations)
- **Primary Data Source**: Angel One is now the primary data source, with Breeze and Yahoo as fallbacks

### 2. Stable ML Prediction System
- **15-Minute Update Interval**: Predictions update every 15 minutes (not every second!)
- **High Confidence Threshold**: Only provides BUY/SELL signals when confidence ≥ 65%
- **Model Agreement**: Uses 3 ML models (Random Forest, Gradient Boosting, XGBoost) - signals only when 2+ models agree
- **Clear Reasoning**: Each prediction includes detailed reasoning and top influential factors
- **Cached Predictions**: Shows same prediction for 15 minutes to avoid confusion

## 📋 Setup Instructions

### Step 1: Update Credentials

Edit the `.env` file with your Angel One credentials:

```bash
# Angel One API Credentials
ANGEL_ONE_API_KEY=your_angel_api_key_here
ANGEL_ONE_CLIENT_ID=your_client_id_here
ANGEL_ONE_PASSWORD=your_password_here
ANGEL_ONE_TOTP_SECRET=your_totp_secret_here
```

**Note**: You need to get your TOTP secret from Angel One:
1. Log into Angel One SmartAPI portal
2. Go to Security Settings
3. Enable 2FA and note down the TOTP secret key

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Test the Integration

Run the test script to verify everything is working:

```bash
python test_angel_ml_integration.py
```

This will:
- ✅ Test Angel One login
- ✅ Fetch live prices (NIFTY, BANKNIFTY)
- ✅ Get historical candle data
- ✅ Attempt to fetch option chain
- ✅ Calculate technical indicators
- ✅ Train and test the stable ML prediction system

### Step 4: Run the Main Application

```bash
python app.py
```

Or use the batch file:

```bash
run.bat
```

The server will start at: **http://127.0.0.1:5000**

## 🎯 How the Stable ML System Works

### Problem Solved
**Before**: Predictions changed every second, making it impossible to trade with confidence.

**Now**: Predictions are stable for 15 minutes, giving you:
- Consistent signals
- Time to analyze
- Clear entry/exit points
- Confidence to execute trades

### Prediction Logic

```python
# Prediction is generated ONLY when:
1. 15 minutes have passed since last prediction    ✓
2. Confidence threshold ≥ 65%                       ✓
3. At least 2 out of 3 models agree                 ✓

# Otherwise:
- Returns "WAIT" signal
- Shows cached prediction
- Provides reasoning for why trade is not recommended
```

### Sample Output

```
📊 Direction: BULLISH
🎯 Signal: BUY CALL
💪 Confidence: 72%
🤝 Model Agreement: 100%

📈 Probabilities:
   Bullish: 72.3%
   Bearish: 27.7%

🤖 Individual Models:
   Random Forest: BULLISH
   Gradient Boost: BULLISH
   XGBoost: BULLISH

💡 Reasoning:
   3/3 models predict upward movement | Confidence: 72% | Model Agreement: 100%

🔑 Top Influential Features:
   1. Short Momentum: 24.5%
   2. RSI: 18.3%
   3. MACD Histogram: 15.7%
   4. Price Vs Avg: 12.1%
   5. ADX: 9.8%

⏰ Prediction Time: 2026-01-22 16:15:00
⏱️  Next Update: 2026-01-22 16:30:00
```

## 📡 API Endpoints

### 1. Status Check
```
GET /api/status
```
Returns connection status for all data sources + ML model stats

**Response:**
```json
{
  "angel_one_connected": true,
  "angel_one_client": "your_client_id",
  "breeze_connected": false,
  "market_open": true,
  "yahoo_available": true,
  "ml_trained": true,
  "ml_accuracy": {
    "rf": 0.68,
    "gb": 0.71,
    "xgb": 0.73
  }
}
```

### 2. Market Analysis (with Stable ML)
```
GET /api/analysis?index=nifty
```

**Response includes:**
- `prediction.stable_ml` - Stable 15-minute prediction
- `prediction.ml` - Legacy ML prediction (for comparison)
- Trade recommendations with reasoning
- Top influential features

### 3. Option Chain (Angel One Primary)
```
GET /api/option-chain?index=nifty
```

Tries Angel One first, then falls back to Breeze/Yahoo.

### 4. ML Statistics
```
GET /api/ml-stats
```

Returns:
- Training accuracy for all models
- Prediction interval (15 minutes)
- Confidence threshold (65%)
- Number of predictions made
- Last prediction time

## 🔥 Trading Workflow

### For 15-Minute Trades:

1. **Get Prediction** (every 15 mins)
   ```python
   GET /api/analysis?index=nifty
   ```

2. **Check Signal**
   - `BUY CALL` = Go long (Call options)
   - `BUY PUT` = Go short (Put options)
   - `WAIT` = No trade (low confidence or model disagreement)

3. **Review Reasoning**
   - Check why the signal was generated
   - Review top influential features
   - Confirm model agreement is high

4. **Execute Trade** (if confident)
   - Use recommended entry, stop-loss, and target from `trade_recommendation`
   - Use suggested lot size
   - Expected profit is calculated

5. **Monitor** (wait for next update)
   - Prediction remains stable for 15 minutes
   - No need to check every second
   - Next update time is provided

## 🎓 Understanding the Predictions

### Confidence Levels
- **65-75%**: Moderate confidence - Small position size
- **75-85%**: High confidence - Standard position size
- **85%+**: Very high confidence - Aggressive position size

### Model Agreement
- **100%**: All 3 models agree - Strongest signal
- **67%**: 2 out of 3 models agree - Good signal
- **Below 67%**: Models disagree - WAIT recommended

### Top Features
Shows which technical indicators are most influential for the current prediction:
- High RSI influence = Overbought/Oversold driving prediction
- High MACD influence = Momentum driving prediction
- High ADX influence = Trend strength driving prediction

## ⚠️ Important Notes

### Angel One API Limitations
- **Option Chain**: Angel One doesn't have a direct option chain API. The system searches for individual strikes, which is slower.
- **Rate Limits**: Too many API calls may trigger rate limiting
- **Session**: Login session expires after some time - the system auto-relogins

### Stable ML Behavior
- **First Run**: Model trains automatically on first prediction
- **Training Time**: Initial training takes 10-30 seconds
- **Updates**: Predictions update every 15 minutes ONLY
- **Cache**: Cached predictions are returned between updates

### Data Source Priority
1. **Angel One** (Primary for live prices & candles)
2. **Breeze API** (Fallback for all data types)
3. **Yahoo Finance** (Fallback for all data types)

## 🐛 Troubleshooting

### Issue: Angel One login fails
**Solution**: Check your credentials in `.env`:
- Verify API Key
- Verify Client ID
- Verify Password
- Get TOTP secret from Angel One portal

### Issue: Predictions are not updating
**Solution**: This is expected! Predictions update every 15 minutes.
- Check `next_update` time in response
- To force update, restart the server

### Issue: Always getting "WAIT" signal
**Possible Reasons:**
1. Confidence is below 65% - Market is unclear
2. Models disagree - Conflicting signals
3. Insufficient data - Need more candles

**Solution**: Wait for clearer market conditions or check technical indicators manually.

### Issue: Option chain is empty
**Expected**: Angel One option chain has limitations.
**Solution**: Use Yahoo Finance fallback for option chain data.

## 📈 Next Steps

1. **Test in Paper Trading**: Verify predictions with paper trades first
2. **Track Performance**: Monitor win rate and profit/loss
3. **Adjust Confidence**: You can modify `confidence_threshold` in `stable_ml_predictor.py` (default: 65%)
4. **Customize Interval**: Change `prediction_interval_minutes` in `stable_ml_predictor.py` (default: 15)

## 💡 Pro Tips

1. **Don't Over-trade**: Wait for high-confidence signals
2. **Use Stop-Loss**: Always use the recommended stop-loss
3. **Position Sizing**: Follow the suggested lot size based on your risk
4. **Track Results**: Keep a log of predictions vs actual outcomes
5. **Model Agreement**: Only trade when 2+ models agree

---

## Support

For issues or questions, check:
1. Test script output: `python test_angel_ml_integration.py`
2. Server logs when running `app.py`
3. API response errors in browser developer tools

Good luck with your trading! 🚀📊💰
