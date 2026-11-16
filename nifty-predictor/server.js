/**
 * Nifty Predictor — Node bridge / Angel One proxy
 *
 * - Serves the static dashboard in this folder
 * - Proxies /angel-api/* to Angel One SmartAPI (avoids browser CORS issues)
 * - Proxies /api/* to the Python Flask backend (or serves local fallback data)
 *
 * Env:
 *   PORT            default 3001 (hosts inject their own)
 *   FLASK_BACKEND   default http://127.0.0.1:5000
 */
const express = require('express');
const cors = require('cors');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const PORT = parseInt(process.env.PORT || '3001', 10);
const FLASK_BACKEND = process.env.FLASK_BACKEND || 'http://127.0.0.1:5000';

app.use(cors());
app.use(express.json({ limit: '256kb' }));

// Request log (single line, no spam)
app.use((req, res, next) => {
    const start = Date.now();
    res.on('finish', () => {
        console.log(`${req.method} ${req.originalUrl} -> ${res.statusCode} (${Date.now() - start}ms)`);
    });
    next();
});

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------
app.get('/healthz', (_req, res) => {
    res.json({ status: 'ok', service: 'nifty-predictor-node', timestamp: new Date().toISOString() });
});

// ---------------------------------------------------------------------------
// Angel One API proxy
// ---------------------------------------------------------------------------
const angelProxy = createProxyMiddleware({
    target: 'https://apiconnect.angelone.in',
    changeOrigin: true,
    pathRewrite: { '^/angel-api': '' },
    onProxyReq: (proxyReq) => {
        proxyReq.setHeader('X-UserType', 'USER');
        proxyReq.setHeader('X-SourceID', 'WEB');
        proxyReq.removeHeader('Origin');
        proxyReq.removeHeader('Referer');
    },
    onError: (err, _req, res) => {
        console.error('Angel proxy error:', err.message);
        if (!res.headersSent) res.status(502).json({ error: 'ANGEL_PROXY_ERROR' });
    },
});
app.use('/angel-api', angelProxy);

// ---------------------------------------------------------------------------
// Flask backend proxy — real ML data when Python server is running.
// Falls back to clearly-labeled simulated data when it is not.
// ---------------------------------------------------------------------------
const flaskProxy = createProxyMiddleware({
    target: FLASK_BACKEND,
    changeOrigin: true,
    logLevel: 'warn',
    onError: (err, _req, res) => {
        console.error('Flask backend unreachable:', err.message);
        if (!res.headersSent) {
            res.status(503).json({
                error: 'BACKEND_UNAVAILABLE',
                message: `Python backend not reachable at ${FLASK_BACKEND}. Start it with: cd nifty-predictor-python && python app.py`,
            });
        }
    },
});
app.use('/flask-api', flaskProxy);

// ---------------------------------------------------------------------------
// Local fallback endpoints (SIMULATED — labeled as such)
// ---------------------------------------------------------------------------
app.get('/api/realtime-data', (_req, res) => {
    res.json({
        timestamp: new Date().toISOString(),
        marketOpen: isMarketOpen(),
        simulated: true,
        nifty: generatePrice(niftyBase, 26000),
        banknifty: generatePrice(bankNiftyBase, 60100),
    });
});

app.get('/api/candles', (req, res) => {
    const symbol = req.query.symbol || '^NSEI';
    const timeframe = req.query.tf || '1d';
    res.json({
        symbol, timeframe,
        simulated: true,
        candles: generateCandles(symbol, timeframe),
        lastUpdate: new Date().toISOString(),
    });
});

app.post('/api/calculate-lots', (req, res) => {
    const { capital, riskPercentage, entryPrice, stopPrice, lotSize } = req.body || {};
    if (!capital || !riskPercentage || !entryPrice || !stopPrice) {
        return res.status(400).json({ error: 'Missing parameters: capital, riskPercentage, entryPrice, stopPrice' });
    }
    const multiplier = Number(lotSize) || 75; // NIFTY default; BSE/NSE revisions via param
    const riskAmount = (capital * riskPercentage) / 100;
    const pointsRisk = Math.abs(entryPrice - stopPrice);
    if (pointsRisk <= 0) return res.status(400).json({ error: 'entryPrice must differ from stopPrice' });
    const lotsByRisk = Math.floor(riskAmount / (pointsRisk * multiplier));
    const maxLots = Math.floor(capital / (entryPrice * multiplier));
    const suggested = Math.max(0, Math.min(lotsByRisk, maxLots));
    res.json({
        riskAmount: riskAmount.toFixed(2),
        pointsRisk: pointsRisk.toFixed(2),
        multiplier,
        suggestedLots: suggested,
        maxAllowedLots: maxLots,
        marginRequired: (entryPrice * multiplier * suggested).toFixed(2),
    });
});

app.post('/api/calculate-pnl', (req, res) => {
    const { entryPrice, exitPrice, lots, lotSize } = req.body || {};
    if (entryPrice == null || exitPrice == null || !lots) {
        return res.status(400).json({ error: 'Missing parameters: entryPrice, exitPrice, lots' });
    }
    const multiplier = Number(lotSize) || 75;
    const pointsDifference = exitPrice - entryPrice;
    const profitLoss = pointsDifference * multiplier * lots;
    res.json({
        entryPrice, exitPrice, lots, multiplier,
        pointsDifference: pointsDifference.toFixed(2),
        profitLoss: profitLoss.toFixed(2),
        percentage: ((pointsDifference / entryPrice) * 100).toFixed(2),
        profitLossPerLot: (pointsDifference * multiplier).toFixed(2),
        status: profitLoss >= 0 ? 'PROFIT' : 'LOSS',
    });
});

// Static dashboard (served after API routes so /api/* never hits the filesystem)
app.use(express.static(__dirname));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function isMarketOpen() {
    const now = new Date();
    const day = now.getDay();
    const mins = now.getHours() * 60 + now.getMinutes();
    return day !== 0 && day !== 6 && mins >= 9 * 60 + 15 && mins <= 15 * 60 + 30;
}

let niftyBase = 26050;
let bankNiftyBase = 60150;

function generatePrice(base, open) {
    base += (Math.random() - 0.5) * 20;
    if (open === 26000) niftyBase = base; else bankNiftyBase = base;
    return {
        ltp: base.toFixed(2), open,
        high: Math.max(base, open * 1.004).toFixed(2),
        low: Math.min(base, open * 0.996).toFixed(2),
        close: base.toFixed(2),
        volume: Math.floor(Math.random() * 1000000),
        change: (((base - open) / open) * 100).toFixed(2),
    };
}

function generateCandles(symbol, timeframe) {
    const candles = [];
    let basePrice = symbol === '^NSEI' ? 26050 : 60150;
    const now = Math.floor(Date.now() / 1000);
    const intervals = { '5m': 300, '15m': 900, '1h': 3600, '1d': 86400 };
    const interval = intervals[timeframe] || 86400;
    const count = timeframe === '1d' ? 100 : timeframe === '1h' ? 50 : 30;
    for (let i = count; i >= 0; i--) {
        const open = basePrice + (Math.random() - 0.5) * 50;
        const close = open + (Math.random() - 0.5) * 100;
        candles.push({
            timestamp: now - i * interval,
            open: open.toFixed(2),
            high: Math.max(open, close).toFixed(2),
            low: Math.min(open, close).toFixed(2),
            close: close.toFixed(2),
            volume: Math.floor(Math.random() * 100000),
        });
        basePrice = close;
    }
    return candles;
}

app.listen(PORT, '0.0.0.0', () => {
    console.log('-----------------------------------------------------------');
    console.log(`PRO TRADING BRIDGE RUNNING AT http://localhost:${PORT}`);
    console.log(`Health:        http://localhost:${PORT}/healthz`);
    console.log(`Flask backend: ${FLASK_BACKEND} (via /flask-api/*)`);
    console.log('Angel One proxy active at /angel-api');
    console.log('-----------------------------------------------------------');
});
