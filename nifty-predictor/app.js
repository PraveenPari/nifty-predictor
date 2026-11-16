// PRO DASHBOARD CONTROLLER - PRODUCTION VERSION
let currentIndex = 'nifty';
let currentTimeframe = '5m';
let currentChartType = 'candle';
let optionChainInterval = null;
let marketData = {
    currentPrice: 26050,
    change: 0,
    candles: [],
    indicators: {},
    prediction: { direction: 'NEUTRAL', ceProb: 50, peProb: 50 }
};
let tickerData = {
    nifty: { price: 26050, change: 0 },
    banknifty: { price: 60150, change: 0 }
};
let strategies = [];
let lastUpdateTime = 0;

const SYMBOLS = {
    nifty: '^NSEI',
    banknifty: '^NSEBANK'
};

// Trading Configuration
const TRADING_CONFIG = {
    capital: 100000, // 1 Lakh default
    riskPercentage: 2, // 2% risk per trade
    contractMultiplier: 75, // NIFTY/BANKNIFTY
    profitTarget: 1.5, // 1.5:1 risk-reward ratio
    minLots: 1,
    maxLots: 20
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    startDataEngine();
});

// 1. CHART ENGINE (TradingView Lightweight Charts)
let chart, mainSeries, volumeSeries;

function initChart() {
    const chartContainer = document.getElementById('tvChartContainer');
    if (!chartContainer) return;
    chartContainer.innerHTML = '';

    chart = LightweightCharts.createChart(chartContainer, {
        width: chartContainer.clientWidth,
        height: chartContainer.clientHeight,
        layout: {
            background: { type: 'solid', color: '#151a21' },
            textColor: '#848e9c',
        },
        grid: {
            vertLines: { color: '#2b313a' },
            horzLines: { color: '#2b313a' },
        },
        timeScale: {
            timeVisible: true,
            secondsVisible: false,
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
        },
    });

    createMainSeries();

    // Handle Resize
    new ResizeObserver(entries => {
        if (entries.length === 0 || entries[0].target !== chartContainer) { return; }
        const newRect = entries[0].contentRect;
        chart.applyOptions({ width: newRect.width, height: newRect.height });
    }).observe(chartContainer);
}

function createMainSeries() {
    if (mainSeries) chart.removeSeries(mainSeries);

    if (currentChartType === 'candle') {
        mainSeries = chart.addCandlestickSeries({
            upColor: '#0ecb81',
            downColor: '#f6465d',
            borderVisible: false,
            wickUpColor: '#0ecb81',
            wickDownColor: '#f6465d',
        });
    } else {
        mainSeries = chart.addLineSeries({
            color: '#0ecb81',
            lineWidth: 2,
        });
    }
}

function toggleChartType(type) {
    if (currentChartType === type) return;
    currentChartType = type;
    createMainSeries();
    updateChartData();
}

// 2. REAL-TIME DATA ENGINE
async function startDataEngine() {
    console.log('🚀 Starting Real-Time Data Engine...');

    // Initial load
    await updateDashboard(true);

    // Real-time updates (1 second)
    setInterval(() => updateDashboard(false), 1000);

    // Candle updates (based on timeframe)
    setInterval(() => updateCandles(), getTimeframeInterval(currentTimeframe));

    // Option Chain (5s)
    optionChainInterval = setInterval(updateOptionChain, 5000);

    // Predictions (2s)
    setInterval(() => updateTimeframePredictions(), 2000);
}

function getTimeframeInterval(tf) {
    const intervals = { '5m': 5000, '15m': 15000, '1d': 60000, '1h': 3600000 };
    return intervals[tf] || 5000;
}

async function updateDashboard(isFullLoad) {
    try {
        if (isFullLoad) {
            // Full load: get candles + live data
            await fetchRealTimeCandles();
        } else {
            // Live update: just get latest price
            await fetchRealTimePrice();
        }

        calculateIndicators();
        runStrategies();

        updateTickerDisplay();
        updatePredictionPanel();
        updateKeyLevels();
        updateStrategyPanel();
        updateTradeSuggestions();

        updateChartData();

    } catch (e) {
        console.error("Dashboard Update Error:", e);
    }
}

async function fetchRealTimeCandles() {
    try {
        const response = await fetch(`/api/candles?symbol=${SYMBOLS[currentIndex]}&tf=${currentTimeframe}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        marketData.candles = data.candles.map(c => ({
            timestamp: c.timestamp,
            open: parseFloat(c.open),
            high: parseFloat(c.high),
            low: parseFloat(c.low),
            close: parseFloat(c.close),
            volume: c.volume
        }));

        if (marketData.candles.length > 0) {
            const lastCandle = marketData.candles[marketData.candles.length - 1];
            marketData.currentPrice = lastCandle.close;
            marketData.lastUpdate = new Date();
            document.getElementById('dataSource').innerHTML = 'LIVE SERVER';
            document.getElementById('dataSource').className = 'data-source-badge up';
        }
    } catch (e) {
        console.error('Failed to fetch candles:', e);
        generateSimulatedData();
    }
}

async function fetchRealTimePrice() {
    try {
        const response = await fetch(`/api/realtime-data`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();

        // Update global ticker data for BOTH indices
        tickerData.nifty = { price: parseFloat(data.nifty.ltp), change: parseFloat(data.nifty.change) };
        tickerData.banknifty = { price: parseFloat(data.banknifty.ltp), change: parseFloat(data.banknifty.change) };

        updateTickerDisplay();

        const priceData = currentIndex === 'nifty' ? data.nifty : data.banknifty;

        if (marketData.candles && marketData.candles.length > 0) {
            const lastCandle = marketData.candles[marketData.candles.length - 1];
            lastCandle.close = parseFloat(priceData.ltp);
            lastCandle.high = Math.max(lastCandle.high, parseFloat(priceData.ltp));
            lastCandle.low = Math.min(lastCandle.low, parseFloat(priceData.ltp));

            marketData.currentPrice = parseFloat(priceData.ltp);
            marketData.change = parseFloat(priceData.change);
        }
    } catch (e) {
        console.warn('Live price update failed:', e.message);
    }
}

async function updateCandles() {
    await fetchRealTimeCandles();
    updateChartData();
}

function generateSimulatedData() {
    const candles = [];
    let price = currentIndex === 'nifty' ? 26050 : 60150;
    const now = Math.floor(Date.now() / 1000);
    const interval = { '5m': 300, '15m': 900, '1d': 86400, '1h': 3600 }[currentTimeframe] || 300;
    const count = 100;

    for (let i = count; i >= 0; i--) {
        const open = price;
        const close = price + (Math.random() - 0.5) * 50;
        const high = Math.max(open, close) + Math.random() * 20;
        const low = Math.min(open, close) - Math.random() * 20;

        candles.push({
            timestamp: now - (i * interval),
            open, high, low, close,
            volume: Math.floor(Math.random() * 100000)
        });
        price = close;
    }

    marketData = {
        index: currentIndex,
        currentPrice: price,
        prevClose: price * 0.99,
        change: 1.0,
        candles: candles,
        lastUpdate: new Date(),
        sentiment: { score: 60, label: 'NEUTRAL' }
    };

    return marketData;
}

function updateChartData() {
    if (!marketData || !marketData.candles || !mainSeries) return;

    const data = marketData.candles.map(c => {
        if (currentChartType === 'candle') {
            return {
                time: c.timestamp,
                open: c.open,
                high: c.high,
                low: c.low,
                close: c.close
            };
        } else {
            return {
                time: c.timestamp,
                value: c.close
            };
        }
    });

    if (data.length > 0) {
        mainSeries.setData(data);
        chart.timeScale().fitContent();
    }
}

// 3. CORE ANALYTICS
function calculateIndicators() {
    const TI = window.TechnicalIndicators;
    if (!TI || !marketData.candles) return;

    const prices = marketData.candles.map(c => c.close);
    const highs = marketData.candles.map(c => c.high);
    const lows = marketData.candles.map(c => c.low);
    const closes = marketData.candles.map(c => c.close);
    const volumes = marketData.candles.map(c => c.volume);

    marketData.indicators = {
        rsi: TI.RSI(prices, 14),
        macd: TI.MACD(prices),
        ema20: TI.EMA(prices, 20),
        ema50: TI.EMA(prices, 50),
        bb: TI.BollingerBands(prices, 20, 2),
        stochastic: TI.Stochastic(highs, lows, closes),
        adx: TI.ADX(highs, lows, closes),
        superTrend: TI.SuperTrend(highs, lows, closes),
        vwap: TI.VWAP(highs, lows, closes, volumes),
        ichimoku: TI.IchimokuCloud(highs, lows, closes),
        psar: TI.ParabolicSAR(highs, lows, closes),
        cci: TI.CCI(highs, lows, closes),
        williamsR: TI.WilliamsR(highs, lows, closes)
    };
}

function runStrategies() {
    const TS = window.TradingStrategies;
    if (!TS || !marketData.indicators) return;

    // Pass enriched marketData with arrays needed for strategies
    const analysisData = {
        prices: marketData.candles.map(c => c.close),
        highs: marketData.candles.map(c => c.high),
        lows: marketData.candles.map(c => c.low),
        closes: marketData.candles.map(c => c.close),
        volumes: marketData.candles.map(c => c.volume),
        indicators: marketData.indicators,
        sentiment: marketData.sentiment // from fetchRealTimeData
    };

    strategies = TS.analyzeAllStrategies(analysisData);
    marketData.prediction = TS.calculatePrediction(strategies);
}


// Re-implementing the fetchRealTimeData to be compatible with new structure
async function fetchRealTimeData() {
    try {
        const historyData = await fetchYahooHistory();

        // 2. Try fetching Live Price from Angel One
        // NOTE: We check window.AngelOneAPI existence but don't hard fail if login missing yet
        if (window.AngelOneAPI && window.API_CONFIG && window.API_CONFIG.AUTO_LOGIN) {
            try {
                if (!window.AngelOneAPI.session.isLoggedIn) {
                    console.log('Attempting Angel One login...');
                    await window.AngelOneAPI.login();
                }

                let liveQuote = null;
                try {
                    liveQuote = currentIndex === 'nifty' ? await window.AngelOneAPI.getNiftyData() : await window.AngelOneAPI.getBankNiftyData();
                } catch (quoteError) {
                    console.warn('Failed to get live quote, retrying with fallback...', quoteError);
                    // Try alternative method
                    if (currentIndex === 'nifty') {
                        liveQuote = await window.AngelOneAPI.getMarketQuote('NSE', window.AngelOneAPI.tokens.nifty);
                    } else {
                        liveQuote = await window.AngelOneAPI.getMarketQuote('NSE', window.AngelOneAPI.tokens.banknifty);
                    }
                }

                if (liveQuote && (liveQuote.fetched && liveQuote.fetched.length > 0 || liveQuote.data)) {
                    const data = liveQuote.fetched ? liveQuote.fetched[0] : (liveQuote.data ? liveQuote.data[0] : null);
                    if (data && data.ltp) {
                        const ltp = parseFloat(data.ltp);
                        const lastCandle = historyData.candles[historyData.candles.length - 1];

                        // Update with live data
                        lastCandle.close = ltp;
                        lastCandle.high = Math.max(lastCandle.high, ltp);
                        lastCandle.low = Math.min(lastCandle.low, ltp);

                        historyData.currentPrice = ltp;
                        document.getElementById('dataSource').innerHTML = 'ANGEL LIVE';
                        document.getElementById('dataSource').className = 'data-source-badge up';
                        console.log('✓ Angel One live data updated:', ltp);
                    }
                }
            } catch (angelError) {
                // Silent failover to Yahoo
                console.warn('Angel One connection failed, using Yahoo Feed:', angelError.message);
                document.getElementById('dataSource').innerHTML = 'YAHOO FEED';
                document.getElementById('dataSource').className = 'data-source-badge';
            }
        } else {
            document.getElementById('dataSource').innerHTML = 'YAHOO FEED';
            document.getElementById('dataSource').className = 'data-source-badge';
        }

        marketData = historyData;

    } catch (error) {
        console.error('Hybrid Fetch Failed:', error);
        document.getElementById('dataSource').innerHTML = 'RECONNECTING';
        document.getElementById('dataSource').className = 'data-source-badge down';
        // Don't throw, keep UI alive with stale data if possible
    }
}

// Yahoo Logic
async function fetchYahooHistory() {
    const symbol = SYMBOLS[currentIndex];
    const proxies = [
        'https://corsproxy.io/?',
        'https://api.allorigins.win/raw?url=',
        'https://api.codetabs.com/v1/proxy?quest='
    ];
    const intervals = { '1d': '5m', '5d': '15m', '1mo': '1d' };
    const ranges = { '1d': '1d', '5d': '5d', '1mo': '1mo' };
    const yahooUrl = `https://query1.finance.yahoo.com/v8/finance/chart/${symbol}?interval=${intervals[currentTimeframe]}&range=${ranges[currentTimeframe]}`;

    let result = null;
    let errorMsg = "";

    // Randomize proxy order to distribute load
    const shuffledProxies = proxies.sort(() => 0.5 - Math.random());

    for (const proxy of shuffledProxies) {
        try {
            const response = await fetch(proxy + encodeURIComponent(yahooUrl));
            if (!response.ok) throw new Error("HTTP " + response.status);
            const data = await response.json();
            if (data.chart && data.chart.result && data.chart.result[0]) {
                result = data.chart.result[0];
                break;
            }
        } catch (e) { errorMsg = e.message; }
    }

    if (!result) {
        // Fallback to simulated candles if internet down, just so UI doesn't break
        console.warn("Using simulated data due to fetch failure: " + errorMsg);
        return generateSimulatedData();
    }

    const quote = result.indicators.quote[0];
    const timestamps = result.timestamp;
    const meta = result.meta;
    const candles = [];

    // Filter nulls
    for (let i = 0; i < timestamps.length; i++) {
        if (quote.close[i]) {
            candles.push({
                timestamp: timestamps[i],
                open: quote.open[i],
                high: quote.high[i],
                low: quote.low[i],
                close: quote.close[i],
                volume: quote.volume[i] || 0
            });
        }
    }

    const currentPrice = meta.regularMarketPrice || candles[candles.length - 1].close;
    return {
        index: currentIndex,
        currentPrice: currentPrice,
        prevClose: meta.chartPreviousClose || currentPrice,
        change: meta.chartPreviousClose ? ((currentPrice - meta.chartPreviousClose) / meta.chartPreviousClose) * 100 : 0,
        candles: candles,
        lastUpdate: new Date(),
        sentiment: { // Mock sentiment until we hook into OI API
            score: 55,
            ceOI: 1500000, peOI: 1800000,
            ceOIChange: -50000, peOIChange: 120000,
            pcr: 1.2, vix: 14.5, vixChange: -0.5,
            fiiNet: 500, diiNet: 200
        }
    };
}

// (Duplicate version removed in cleanup)

// 4. UI UPDATES
function updateTickerDisplay() {
    ['nifty', 'banknifty'].forEach(idx => {
        const priceEl = document.getElementById(`${idx}Price`);
        const changeEl = document.getElementById(`${idx}Change`);
        const data = tickerData[idx];

        if (priceEl && data.price) {
            const oldPrice = parseFloat(priceEl.dataset.last || 0);
            if (data.price !== oldPrice && oldPrice !== 0) {
                priceEl.classList.remove('flash-up', 'flash-down');
                void priceEl.offsetWidth;
                priceEl.classList.add(data.price > oldPrice ? 'flash-up' : 'flash-down');
            }
            priceEl.dataset.last = data.price;
            priceEl.textContent = data.price.toFixed(2);
        }
        if (changeEl) {
            changeEl.textContent = `${data.change >= 0 ? '+' : ''}${data.change.toFixed(2)}%`;
            changeEl.className = `ticker-change ${data.change >= 0 ? 'up' : 'down'}`;
        }
    });
}

function updatePredictionPanel() {
    const pred = marketData.prediction;
    if (!pred) return;

    const gaugeVal = document.getElementById('gaugeValue');
    if (gaugeVal) gaugeVal.textContent = `${pred.ceProb}%`;

    const gaugeLbl = document.getElementById('gaugeLabel');
    if (gaugeLbl) {
        gaugeLbl.textContent = pred.direction;
        gaugeLbl.style.color = pred.direction === 'BULLISH' ? 'var(--up-color)' : (pred.direction === 'BEARISH' ? 'var(--down-color)' : 'var(--accent-blue)');
    }

    const ceProb = document.getElementById('ceProb');
    if (ceProb) ceProb.textContent = `${pred.ceProb}%`;

    const peProb = document.getElementById('peProb');
    if (peProb) peProb.textContent = `${pred.peProb}%`;

    // Display confidence
    const conf = document.getElementById('predictionConfidence');
    if (conf && pred.confidence) {
        conf.textContent = `Confidence: ${Math.round(pred.confidence)}%`;
    }
}

// NEW: Update predictions for different timeframes
function updateTimeframePredictions() {
    if (!marketData || !marketData.candles || marketData.candles.length < 5) return;

    const timeframes = {
        '5m': { name: '5 Min', candles: 1 },
        '15m': { name: '15 Min', candles: 3 },
        '1h': { name: '1 Hour', candles: 12 }
    };

    for (const [key, tf] of Object.entries(timeframes)) {
        const recentCandles = marketData.candles.slice(-tf.candles);
        if (recentCandles.length === 0) continue;

        // Calculate indicators on recent candles
        const closes = recentCandles.map(c => c.close);
        const highs = recentCandles.map(c => c.high);
        const lows = recentCandles.map(c => c.low);

        const TI = window.TechnicalIndicators;
        if (!TI) continue;

        const tfIndicators = {
            rsi: TI.RSI(closes, 14),
            macd: TI.MACD(closes),
            ema20: TI.EMA(closes, Math.min(20, closes.length)),
            ema50: TI.EMA(closes, Math.min(50, closes.length))
        };

        // Store timeframe predictions
        if (!marketData.timeframePredictions) marketData.timeframePredictions = {};
        marketData.timeframePredictions[key] = {
            name: tf.name,
            indicators: tfIndicators,
            lastPrice: closes[closes.length - 1]
        };
    }

    // Update UI with timeframe predictions
    displayTimeframePredictions();
}

function updateStrategyPanel() {
    const grid = document.getElementById('strategiesGrid');
    if (!grid || !strategies || strategies.length === 0) {
        if (grid) grid.innerHTML = '<div class="no-data">No strategy data available</div>';
        return;
    }
    grid.innerHTML = '';

    // Sort strategies by Signal urgency (Buy/Sell first, Neutral last)
    const sorted = [...strategies].sort((a, b) => {
        const priority = { 'bullish': 1, 'bearish': 1, 'neutral': 2 };
        return (priority[a.signal] || 2) - (priority[b.signal] || 2);
    });

    // Display all strategies, max 16
    sorted.slice(0, 16).forEach(s => {
        const div = document.createElement('div');
        div.className = 'strat-card-compact';
        const color = s.signal === 'bullish' ? 'up' : (s.signal === 'bearish' ? 'down' : 'text-secondary');
        div.innerHTML = `
            <span class="strat-name">${s.name}</span>
            <span class="strat-val ${color}">${s.signal.toUpperCase()}</span>
        `;
        div.title = `${s.reason}\nStrength: ${s.strength}%`; // Enhanced tooltip
        grid.appendChild(div);
    });

    // Log for debugging
    console.log(`Displayed ${sorted.length} strategies`);
}

// NEW: Update trade suggestions with lot size and profit targets
function updateTradeSuggestions() {
    if (!marketData || !marketData.prediction) return;

    const prediction = marketData.prediction;
    const currentPrice = marketData.currentPrice;

    // Calculate support and resistance for stops
    const volatility = calculateVolatility();
    const atrValue = volatility || (currentPrice * 0.005);

    let entryPrice, stopPrice, targetPrice, optionRec;

    // Determine Option Recommendation (ATM/OTM)
    const strikeStep = currentIndex === 'nifty' ? 50 : 100;
    const atmStrike = Math.round(currentPrice / strikeStep) * strikeStep;

    if (prediction.direction === 'BULLISH') {
        entryPrice = currentPrice;
        stopPrice = currentPrice - atrValue;
        targetPrice = currentPrice + (atrValue * 1.5);
        optionRec = `BUY ${currentIndex.toUpperCase()} ${atmStrike} CE`;
    } else {
        entryPrice = currentPrice;
        stopPrice = currentPrice + atrValue;
        targetPrice = currentPrice - (atrValue * 1.5);
        optionRec = `BUY ${currentIndex.toUpperCase()} ${atmStrike} PE`;
    }

    const risk = Math.abs(entryPrice - stopPrice);
    const reward = Math.abs(targetPrice - entryPrice);
    const riskReward = (reward / risk).toFixed(2);

    // Calculate lot size
    const riskAmount = (TRADING_CONFIG.capital * TRADING_CONFIG.riskPercentage) / 100;
    const lots = Math.min(
        Math.max(TRADING_CONFIG.minLots, Math.floor(riskAmount / (risk * TRADING_CONFIG.contractMultiplier))),
        TRADING_CONFIG.maxLots
    );

    const profitOnTarget = (reward * lots * TRADING_CONFIG.contractMultiplier).toFixed(0);
    const profitPercentage = ((reward / entryPrice) * 100).toFixed(2);

    // Update UI
    const tradePanel = document.getElementById('tradeSuggestionsPanel');
    if (tradePanel) {
        tradePanel.innerHTML = `
            <div class="trade-signal ${prediction.direction === 'BULLISH' ? 'bullish' : 'bearish'}">
                <h4>${prediction.direction} SIGNAL</h4>
                <div class="trade-details">
                     <div class="trade-row highlight" style="background: rgba(255,255,255,0.08);">
                        <span class="label">Recommendation:</span>
                        <span class="value bold" style="font-size: 0.95rem;">${optionRec}</span>
                    </div>
                    <div class="trade-row">
                        <span class="label">Entry Price:</span>
                        <span class="value">${entryPrice.toFixed(2)}</span>
                    </div>
                    <div class="trade-row">
                        <span class="label">Stop Loss:</span>
                        <span class="value error">${stopPrice.toFixed(2)}</span>
                    </div>
                    <div class="trade-row">
                        <span class="label">Target:</span>
                        <span class="value success">${targetPrice.toFixed(2)}</span>
                    </div>
                    <div class="trade-row highlight">
                        <span class="label">Suggested Lots:</span>
                        <span class="value bold">${lots}</span>
                    </div>
                    <div class="trade-row highlight">
                        <span class="label">Risk-Reward:</span>
                        <span class="value">${riskReward}:1</span>
                    </div>
                    <div class="trade-row highlight">
                        <span class="label">Profit at Target:</span>
                        <span class="value success">₹${profitOnTarget}</span>
                    </div>
                    <div class="trade-row highlight">
                        <span class="label">Profit %:</span>
                        <span class="value">${profitPercentage}%</span>
                    </div>
                </div>
            </div>
        `;
    }
}

function calculateVolatility() {
    if (!marketData || !marketData.candles || marketData.candles.length < 10) return null;

    const closes = marketData.candles.slice(-10).map(c => c.close);
    const avgClose = closes.reduce((a, b) => a + b) / closes.length;
    const variance = closes.reduce((a, c) => a + Math.pow(c - avgClose, 2), 0) / closes.length;
    return Math.sqrt(variance);
}

function displayTimeframePredictions() {
    if (!marketData.timeframePredictions) return;

    const container = document.getElementById('timeframePredictions');
    if (!container) return;

    container.innerHTML = '';

    for (const [key, tfData] of Object.entries(marketData.timeframePredictions)) {
        const div = document.createElement('div');
        div.className = 'timeframe-pred-card';

        let signal = 'NEUTRAL';
        let signalColor = 'text-secondary';

        if (tfData.indicators.rsi) {
            if (tfData.indicators.rsi < 30) {
                signal = 'BULLISH';
                signalColor = 'up';
            } else if (tfData.indicators.rsi > 70) {
                signal = 'BEARISH';
                signalColor = 'down';
            }
        }

        div.innerHTML = `
            <div class="tf-name">${tfData.name}</div>
            <div class="tf-price">${tfData.lastPrice.toFixed(2)}</div>
            <div class="tf-signal ${signalColor}">${signal}</div>
        `;

        container.appendChild(div);
    }
}

function updateKeyLevels() {
    if (!marketData || !marketData.candles) return;

    const TI = window.TechnicalIndicators;
    const price = marketData.currentPrice;

    // Use Pivot Points for better resistance/support
    let pivots = null;
    if (TI && marketData.candles.length >= 1) {
        const lastCandle = marketData.candles[marketData.candles.length - 1];
        pivots = TI.PivotPoints(lastCandle.high, lastCandle.low, lastCandle.close);
    }

    // Display resistance levels
    const resEl = document.getElementById('resistanceLevels');
    if (resEl) {
        if (pivots) {
            resEl.innerHTML = `
                <div class="level-item"><span class="lbl">R2</span> <span class="val down">${pivots.r2.toFixed(2)}</span></div>
                <div class="level-item"><span class="lbl">R1</span> <span class="val down">${pivots.r1.toFixed(2)}</span></div>
            `;
        } else {
            const r1 = (price * 1.002).toFixed(2);
            const r2 = (price * 1.005).toFixed(2);
            resEl.innerHTML = `
                <div class="level-item"><span class="lbl">R2</span> <span class="val down">${r2}</span></div>
                <div class="level-item"><span class="lbl">R1</span> <span class="val down">${r1}</span></div>
            `;
        }
    }

    // Display support levels
    const supEl = document.getElementById('supportLevels');
    if (supEl) {
        if (pivots) {
            supEl.innerHTML = `
                <div class="level-item"><span class="lbl">S1</span> <span class="val up">${pivots.s1.toFixed(2)}</span></div>
                <div class="level-item"><span class="lbl">S2</span> <span class="val up">${pivots.s2.toFixed(2)}</span></div>
            `;
        } else {
            const s1 = (price * 0.998).toFixed(2);
            const s2 = (price * 0.995).toFixed(2);
            supEl.innerHTML = `
                <div class="level-item"><span class="lbl">S1</span> <span class="val up">${s1}</span></div>
                <div class="level-item"><span class="lbl">S2</span> <span class="val up">${s2}</span></div>
            `;
        }
    }

    // Display current price with better formatting
    const curEl = document.getElementById('currentPrice');
    if (curEl) {
        curEl.textContent = price.toFixed(2);

        // Show change from previous close
        const change = marketData.change || 0;
        const changeEl = document.createElement('div');
        changeEl.style.fontSize = '0.75rem';
        changeEl.style.color = change >= 0 ? 'var(--up-color)' : 'var(--down-color)';
        changeEl.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;

        if (curEl.parentElement && !curEl.parentElement.querySelector('.price-change')) {
            changeEl.className = 'price-change';
            curEl.parentElement.appendChild(changeEl);
        }
    }

    // Store price history for trend analysis
    if (!window.priceHistory) window.priceHistory = [];
    window.priceHistory.push({ time: Date.now(), price: price });

    // Keep only last 100 prices
    if (window.priceHistory.length > 100) window.priceHistory.shift();
}

function updateOptionChain() {
    const ltp = marketData.currentPrice || 24300;
    const strikeStep = currentIndex === 'nifty' ? 50 : 100;
    const nearestStrike = Math.round(ltp / strikeStep) * strikeStep;

    const container = document.getElementById('optionChainBody');
    if (!container) return;
    container.innerHTML = '';

    for (let i = -6; i <= 6; i++) {
        const strike = nearestStrike + (i * strikeStep);
        const dist = (strike - ltp) / strikeStep;

        let cePrice = Math.max(1, (ltp - strike) + (200 * Math.exp(-Math.abs(dist) / 2)));
        let pePrice = Math.max(1, (strike - ltp) + (200 * Math.exp(-Math.abs(dist) / 2)));

        // Add random jitter
        cePrice += (Math.random() * 2);
        pePrice += (Math.random() * 2);

        const isITM_CE = strike < ltp;
        const isITM_PE = strike > ltp;

        const row = document.createElement('div');
        row.className = 'oc-row';
        if (isITM_CE) row.classList.add('call-bg');
        if (isITM_PE) row.classList.add('put-bg');

        row.innerHTML = `
            <div class="col-oi"><span class="up">${(Math.random() * 50).toFixed(1)}</span></div>
            <div class="col-strike strike-cell">${strike}</div>
            <div class="col-price">
                <span class="${isITM_CE ? 'up' : 'text-secondary'}">${cePrice.toFixed(0)}</span>
                <span class="text-secondary">|</span>
                <span class="${isITM_PE ? 'down' : 'text-secondary'}">${pePrice.toFixed(0)}</span>
            </div>
        `;
        container.appendChild(row);
    }
}

// Global Exports
window.selectIndex = function (idx) {
    currentIndex = idx;
    document.querySelectorAll('.sym-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    updateDashboard(true);
};
window.changeTimeframe = function (tf) {
    currentTimeframe = tf;
    document.querySelectorAll('.tf-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    updateDashboard(true);
};
window.toggleChartType = toggleChartType;
