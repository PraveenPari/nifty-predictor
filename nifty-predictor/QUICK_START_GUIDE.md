# Nifty Predictor - Quick Start & Troubleshooting Guide

## 🚀 Quick Start

### Running the Application
```bash
cd "e:\WORKOUT CODE\nifty-predictor"
npm install
node server.js
```

Then open: **http://localhost:3001** in your browser

## ✅ What Has Been Fixed

### 1. **Strategies Not Showing** ✓
- Fixed the strategies panel to properly display all 16+ strategies
- Added better error handling and logging
- Strategies now show with color coding (Green=Bullish, Red=Bearish, Gray=Neutral)
- Hover over any strategy to see its reason and strength percentage

### 2. **Angel One API Data Not Loading** ✓
- Implemented smart proxy fallback mechanism
- Auto-login system in config.js
- Graceful fallback to Yahoo Finance if Angel One fails
- Status indicator shows: "ANGEL LIVE" (Angel One) or "YAHOO FEED" (Yahoo Finance)

### 3. **10-15 Mins Prediction Missing** ✓
- Added new "TIMEFRAMES" panel in left sidebar
- Shows real-time predictions for:
  - **5 Min** - Short-term trend
  - **15 Min** - Medium-term trend  
  - **1 Hour** - Hourly trend
- Each shows current price and signal (BULLISH/BEARISH/NEUTRAL)

### 4. **Price Data Issues** ✓
- Integrated Pivot Points for accurate support/resistance levels
- Shows **R1, R2** (Resistance) and **S1, S2** (Support)
- Displays **% change** from previous close
- Stores price history for trend analysis

## 🎯 Key Panels Explained

### **AI PREDICTION** (Top Left)
- Large gauge showing bullish percentage
- Overall direction: BULLISH, BEARISH, or NEUTRAL
- Call (CE) and Put (PE) probabilities
- Based on analysis of 18+ trading strategies

### **TIMEFRAMES** (New - Left Sidebar)
- **5 Min**: Quick intraday trades (scalping)
- **15 Min**: Short-term swing trades
- **1 Hour**: Medium-term position trades
- Each shows price and trend signal

### **KEY LEVELS**
- **Resistance (R1, R2)**: Price levels to watch going DOWN
- **Support (S1, S2)**: Price levels to watch going UP
- **LTP**: Current Last Traded Price with % change

### **STRATEGIES** (Right Bottom)
Lists all active trading strategies:
- **RSI Analysis** - Overbought/Oversold
- **MACD Crossover** - Momentum
- **MA Crossover** - Trend direction
- **Bollinger Bands** - Volatility
- **Stochastic** - Momentum
- **ADX Trend** - Trend strength
- **SuperTrend** - Trend indicator
- **VWAP** - Volume-weighted average price
- **Ichimoku Cloud** - Comprehensive indicator
- **Parabolic SAR** - Trend reversals
- **CCI Analysis** - Overbought/Oversold
- **Williams %R** - Momentum
- **Open Interest** - Option market sentiment
- **PCR Analysis** - Put-Call Ratio sentiment
- **VIX Analysis** - Market fear gauge
- **FII/DII Flow** - Institutional activity
- Plus more...

## 🔧 Setting Up Angel One API

### Step 1: Get Your Credentials
1. Login to Angel One account (https://www.angelone.in/)
2. Go to Settings → API
3. Get your:
   - **API Key** (apiKey)
   - **Client ID** (clientCode)
   - **Trading Password** (password)
   - **TOTP Secret** (for 2FA)

### Step 2: Update config.js
Open `config.js` and replace with your credentials:

```javascript
const API_CONFIG = {
    API_KEY: 'your_actual_api_key',
    SECRET_KEY: 'your_secret_key',
    CLIENT_CODE: 'your_client_code',
    PASSWORD: your_password,  // Just the number, no quotes
    TOTP_SECRET: 'your_totp_secret',
    AUTO_LOGIN: true  // Enable auto-login
};
```

### Step 3: Restart Server
```bash
node server.js
```

Check browser console (F12) to see:
```
✓ Angel One Login successful
✓ Angel One live data updated: 24550.25
```

## 🐛 Troubleshooting

### Problem: "YAHOO FEED" instead of "ANGEL LIVE"
**Solution:**
1. Check your credentials in `config.js`
2. Verify TOTP secret is correct
3. Open browser console (F12) to see error messages
4. Application works fine with Yahoo Finance - you get 95% functionality

### Problem: "No strategy data available"
**Solution:**
1. Wait 5-10 seconds for data to load
2. Check browser console for errors
3. Refresh the page
4. Make sure you can see price updates at the top

### Problem: Market prices not updating
**Solution:**
1. Check your internet connection
2. Open browser console (F12 → Console tab)
3. Look for error messages
4. Try refreshing page (Ctrl+R)
5. Try clearing browser cache

### Problem: Option chain not showing data
**Solution:**
1. Wait for initial data load (10-15 seconds)
2. This is normal - requires live market data
3. During market hours, data updates every 5 seconds

## 📊 How to Use

### View Different Markets
- **NIFTY 50**: Click "NIFTY" button (top left)
- **BANK NIFTY**: Click "BANKNIFTY" button

### Change Timeframe
- **5-minute chart**: Click "5m" button
- **15-minute chart**: Click "15m" button  
- **Daily chart**: Click "1D" button

### Read the Signals
1. Check **AI PREDICTION** gauge at top
2. Look at **TIMEFRAMES** panel for different timeframes
3. Review **STRATEGIES** list for confirmation
4. Check **KEY LEVELS** for support/resistance

### Make Trading Decisions
- **BULLISH Signal**: Green color, > 60% probability → Consider CALL options
- **BEARISH Signal**: Red color, > 60% probability → Consider PUT options
- **NEUTRAL Signal**: Gray color → Wait for confirmation

## 📈 Strategy Strength

Each strategy shows a **strength percentage**:
- **80-100%**: Very strong signal
- **60-80%**: Strong signal
- **40-60%**: Moderate signal
- **Below 40%**: Weak signal

Hover over any strategy to see:
- The reason for the signal
- The strength percentage
- The exact technical reason

## ⚠️ Important Notes

1. **This is Educational Only** - Not financial advice
2. **Always do your own research** before trading
3. **Validate signals with price action** - Don't trade on signals alone
4. **Risk management is crucial** - Never risk more than you can afford to lose
5. **Data source matters** - Angel One gives real-time, Yahoo gives delayed

## 🔍 Debug Console (F12)

Press **F12** in browser and go to **Console** tab to see:
- ✓ "Displayed X strategies" - how many strategies are active
- ✓ "Angel One Login successful" - API connection status
- ✓ "YAHOO FEED" - Current data source
- ✗ Any errors that need fixing

## 📞 Support

If you encounter issues:
1. **Check the console** (F12 → Console) for error messages
2. **Check your internet** - Make sure you're connected
3. **Check credentials** - If using Angel One API
4. **Restart server** - Close and rerun `node server.js`
5. **Refresh browser** - Ctrl+R or Cmd+R

## 🎓 Understanding the Analysis

### The AI Prediction uses:
- **Technical Indicators**: RSI, MACD, Moving Averages, Bollinger Bands, etc.
- **Trend Analysis**: SuperTrend, ADX, SAR
- **Volatility**: ATR, Bollinger Bands width
- **Momentum**: Stochastic, CCI, Williams %R
- **Market Sentiment**: PCR, VIX, FII/DII flows
- **Volume Analysis**: VWAP, OBV

### How it calculates:
1. All 18+ strategies vote (Bullish/Bearish/Neutral)
2. Each vote has a strength (0-100%)
3. Total bullish % vs bearish % determines direction
4. Confidence = how decisive the signal is

## 🔄 Update Frequency

- **Prices**: Every 1 second
- **Strategies**: Every 1 second  
- **Option Chain**: Every 5 seconds
- **Predictions**: Every 2 seconds for timeframes

## ✨ Features Summary

✅ Real-time market data (Yahoo Finance)  
✅ Optional Angel One live data  
✅ 18+ automated trading strategies  
✅ Multi-timeframe analysis (5m, 15m, 1h)  
✅ Support/Resistance levels (Pivot Points)  
✅ Option chain data  
✅ Automatic fallback if API fails  
✅ Browser console debugging  
✅ Responsive design  
✅ Real-time updates  

**Version**: 2.0 with all fixes applied  
**Last Updated**: January 2, 2026
