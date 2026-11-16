const express = require('express');
const cors = require('cors');
const { createProxyMiddleware } = require('http-proxy-middleware');
const path = require('path');

const app = express();
const PORT = 3001;

// Enable CORS for all requests
app.use(cors());

// Serve static files from current directory
app.use(express.static(__dirname));

// Logging Middleware
app.use((req, res, next) => {
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.originalUrl}`);
    next();
});

// Proxy Middleware for Angel One API
const angelProxy = createProxyMiddleware({
    target: 'https://apiconnect.angelone.in',
    changeOrigin: true,
    pathRewrite: {
        '^/angel-api': '',
    },
    onProxyReq: (proxyReq, req, res) => {
        proxyReq.setHeader('X-UserType', 'USER');
        proxyReq.setHeader('X-SourceID', 'WEB');
        proxyReq.removeHeader('Origin');
        proxyReq.removeHeader('Referer');
    },
    onProxyRes: (proxyRes, req, res) => {
        proxyRes.headers['Access-Control-Allow-Origin'] = '*';
    },
    onError: (err, req, res) => {
        console.error('Proxy Error:', err);
        res.status(500).send('Proxy Error');
    }
});

// Use the proxy for any request starting with /angel-api
app.use('/angel-api', angelProxy);

// Real-time data endpoint
app.get('/api/realtime-data', (req, res) => {
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/461e43d9-616c-43e9-8840-02688a788584',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'server.js:47',message:'realtime-data endpoint called',data:{timestamp:Date.now()},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
    // #endregion
    try {
        const marketOpen = isMarketOpen();
        // #region agent log
        fetch('http://127.0.0.1:7242/ingest/461e43d9-616c-43e9-8840-02688a788584',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'server.js:50',message:'marketOpen calculated',data:{marketOpen:marketOpen},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
        // #endregion
        const niftyPrice = generateNiftyPrice();
        // #region agent log
        fetch('http://127.0.0.1:7242/ingest/461e43d9-616c-43e9-8840-02688a788584',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'server.js:53',message:'niftyPrice generated',data:{ltp:niftyPrice.ltp,base:niftyBase},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
        // #endregion
        const bankNiftyPrice = generateBankNiftyPrice();
        // #region agent log
        fetch('http://127.0.0.1:7242/ingest/461e43d9-616c-43e9-8840-02688a788584',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'server.js:56',message:'bankNiftyPrice generated',data:{ltp:bankNiftyPrice.ltp,base:bankNiftyBase},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
        // #endregion
        const responseData = {
            timestamp: new Date().toISOString(),
            marketOpen: marketOpen,
            nifty: niftyPrice,
            banknifty: bankNiftyPrice,
            vix: (14.5 + (Math.random() - 0.5) * 2).toFixed(2),
            timeframe: req.query.tf || '1d'
        };
        // #region agent log
        fetch('http://127.0.0.1:7242/ingest/461e43d9-616c-43e9-8840-02688a788584',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'server.js:65',message:'response data prepared',data:{hasNifty:!!responseData.nifty,hasBankNifty:!!responseData.banknifty},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
        // #endregion
        res.json(responseData);
        // #region agent log
        fetch('http://127.0.0.1:7242/ingest/461e43d9-616c-43e9-8840-02688a788584',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'server.js:68',message:'response sent',data:{statusCode:200},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
        // #endregion
    } catch (error) {
        // #region agent log
        fetch('http://127.0.0.1:7242/ingest/461e43d9-616c-43e9-8840-02688a788584',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'server.js:71',message:'error in realtime-data endpoint',data:{error:error.message},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
        // #endregion
        res.status(500).json({ error: error.message });
    }
});

// Historical data endpoint
app.get('/api/candles', (req, res) => {
    const symbol = req.query.symbol || '^NSEI';
    const timeframe = req.query.tf || '1d';
    const candles = generateCandles(symbol, timeframe);

    res.json({
        symbol: symbol,
        timeframe: timeframe,
        candles: candles,
        lastUpdate: new Date().toISOString()
    });
});

// Trade signals endpoint
app.get('/api/trade-signals', (req, res) => {
    const signals = generateTradeSignals();
    res.json(signals);
});

// Lot size calculator endpoint
app.post('/api/calculate-lots', (req, res) => {
    const { capital, riskPercentage, entryPrice, stopPrice } = req.body;

    if (!capital || !riskPercentage || !entryPrice || !stopPrice) {
        return res.status(400).json({ error: 'Missing parameters' });
    }

    const riskAmount = (capital * riskPercentage) / 100;
    const pointsRisk = Math.abs(entryPrice - stopPrice);
    const lotSize = Math.floor(riskAmount / pointsRisk);
    const maxLots = Math.floor(capital / (entryPrice * 75)); // 75 is contract multiplier

    res.json({
        riskAmount: riskAmount.toFixed(2),
        pointsRisk: pointsRisk.toFixed(2),
        suggestedLots: Math.min(lotSize, maxLots),
        maxAllowedLots: maxLots,
        marginRequired: (entryPrice * 75 * Math.min(lotSize, maxLots)).toFixed(2)
    });
});

// Profit/Loss calculator endpoint
app.post('/api/calculate-pnl', (req, res) => {
    const { entryPrice, exitPrice, lots, entryTime, exitTime } = req.body;

    if (!entryPrice || !exitPrice || !lots) {
        return res.status(400).json({ error: 'Missing parameters' });
    }

    const pointsDifference = exitPrice - entryPrice;
    const multiplier = 75; // NIFTY/BANKNIFTY
    const profitLoss = pointsDifference * multiplier * lots;
    const percentage = ((pointsDifference / entryPrice) * 100).toFixed(2);

    res.json({
        entryPrice: entryPrice,
        exitPrice: exitPrice,
        pointsDifference: pointsDifference.toFixed(2),
        lots: lots,
        profitLoss: profitLoss.toFixed(2),
        percentage: percentage,
        profitLossPerLot: (pointsDifference * multiplier).toFixed(2),
        status: profitLoss >= 0 ? 'PROFIT' : 'LOSS'
    });
});

// Helper functions
function isMarketOpen() {
    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes();
    const day = now.getDay();

    // Market open: 9:15 AM to 3:30 PM IST on weekdays
    const timeInMinutes = hours * 60 + minutes;
    const marketOpenTime = 9 * 60 + 15; // 9:15 AM
    const marketCloseTime = 15 * 60 + 30; // 3:30 PM

    return day !== 0 && day !== 6 && timeInMinutes >= marketOpenTime && timeInMinutes <= marketCloseTime;
}

let niftyBase = 26050;
let bankNiftyBase = 60150;

function generateNiftyPrice() {
    // #region agent log
    const oldBase = niftyBase;
    // #endregion
    niftyBase += (Math.random() - 0.5) * 20;
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/461e43d9-616c-43e9-8840-02688a788584',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'server.js:151',message:'generateNiftyPrice base updated',data:{oldBase:oldBase,newBase:niftyBase},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
    // #endregion
    return {
        ltp: niftyBase.toFixed(2),
        open: 26000,
        high: Math.max(niftyBase, 26150),
        low: Math.min(niftyBase, 25950),
        close: niftyBase.toFixed(2),
        volume: Math.floor(Math.random() * 1000000),
        change: ((niftyBase - 26000) / 26000 * 100).toFixed(2)
    };
}

function generateBankNiftyPrice() {
    bankNiftyBase += (Math.random() - 0.5) * 50;
    return {
        ltp: bankNiftyBase.toFixed(2),
        open: 60100,
        high: Math.max(bankNiftyBase, 60400),
        low: Math.min(bankNiftyBase, 60000),
        close: bankNiftyBase.toFixed(2),
        volume: Math.floor(Math.random() * 500000),
        change: ((bankNiftyBase - 60100) / 60100 * 100).toFixed(2)
    };
}

function generateCandles(symbol, timeframe) {
    const candles = [];
    let basePrice = symbol === '^NSEI' ? 26050 : 60150;
    const now = Math.floor(Date.now() / 1000);

    const intervals = {
        '5m': 300,
        '15m': 900,
        '1d': 86400,
        '1h': 3600
    };

    const interval = intervals[timeframe] || 86400;
    const count = timeframe === '1d' ? 100 : (timeframe === '1h' ? 50 : 30);

    for (let i = count; i >= 0; i--) {
        const timestamp = now - (i * interval);
        const open = basePrice + (Math.random() - 0.5) * 50;
        const close = open + (Math.random() - 0.5) * 100;
        const high = Math.max(open, close) + Math.random() * 20;
        const low = Math.min(open, close) - Math.random() * 20;

        candles.push({
            timestamp: timestamp,
            open: open.toFixed(2),
            high: high.toFixed(2),
            low: low.toFixed(2),
            close: close.toFixed(2),
            volume: Math.floor(Math.random() * 100000)
        });

        basePrice = close;
    }

    return candles;
}

function generateTradeSignals() {
    const signals = [];
    const strategies = [
        { name: 'RSI (14)', signal: Math.random() > 0.5 ? 'BULLISH' : 'BEARISH', strength: Math.floor(Math.random() * 100) },
        { name: 'MACD', signal: Math.random() > 0.5 ? 'BULLISH' : 'BEARISH', strength: Math.floor(Math.random() * 100) },
        { name: 'Moving Averages', signal: Math.random() > 0.5 ? 'BULLISH' : 'BEARISH', strength: Math.floor(Math.random() * 100) },
        { name: 'Bollinger Bands', signal: Math.random() > 0.5 ? 'BULLISH' : 'BEARISH', strength: Math.floor(Math.random() * 100) },
        { name: 'Stochastic', signal: Math.random() > 0.5 ? 'BULLISH' : 'BEARISH', strength: Math.floor(Math.random() * 100) },
        { name: 'SuperTrend', signal: Math.random() > 0.5 ? 'BULLISH' : 'BEARISH', strength: Math.floor(Math.random() * 100) },
        { name: 'ADX Trend', signal: Math.random() > 0.5 ? 'BULLISH' : 'BEARISH', strength: Math.floor(Math.random() * 100) },
        { name: 'Ichimoku Cloud', signal: Math.random() > 0.5 ? 'BULLISH' : 'BEARISH', strength: Math.floor(Math.random() * 100) },
        { name: 'VWAP', signal: Math.random() > 0.5 ? 'BULLISH' : 'BEARISH', strength: Math.floor(Math.random() * 100) },
        { name: 'Volume Profile', signal: Math.random() > 0.5 ? 'BULLISH' : 'BEARISH', strength: Math.floor(Math.random() * 100) }
    ];

    return {
        timestamp: new Date().toISOString(),
        strategies: strategies,
        overallSignal: strategies.filter(s => s.signal === 'BULLISH').length > 5 ? 'BULLISH' : 'BEARISH',
        confidence: Math.floor(Math.random() * 100)
    };
}

// Start Server
app.listen(PORT, () => {
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/461e43d9-616c-43e9-8840-02688a788584',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'server.js:248',message:'server started',data:{port:PORT,status:'listening'},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
    // #endregion
    console.log(`\n-----------------------------------------------------------`);
    console.log(`🚀 PRO TRADING SERVER RUNNING AT http://localhost:${PORT}`);
    console.log(`📊 Real-time Data: http://localhost:${PORT}/api/realtime-data`);
    console.log(`📈 Candles API: http://localhost:${PORT}/api/candles?symbol=^NSEI&tf=5m`);
    console.log(`🎯 Trade Signals: http://localhost:${PORT}/api/trade-signals`);
    console.log(`⚡ Angel One Proxy Active at http://localhost:${PORT}/angel-api`);
    console.log(`-----------------------------------------------------------\n`);
});
