console.log("DEBUG: app.js LOADED (Pro Trading Version)");

/**

 * Nifty Predictor Pro - Frontend JavaScript

 * Real-time data with WebSocket + ML Predictions + Pro Trading Features

 */



// Global State

let currentIndex = 'nifty';

let currentTimeframe = '5m';

let currentChartType = 'candle';

let chart = null;

let mainSeries = null;

let socket = null;

let allStrategies = [];



// API Base URL

const API_BASE = '';



// ============================================

// INITIALIZATION

// ============================================

function initApp() {

    console.log("DEBUG: initApp called");

    initChart();

    initWebSocket();

    loadInitialData();

    loadStockPicks();  // Load stock picks

    loadMarketMovers(); // Load market movers

    startDataUpdates();

}



if (document.readyState === 'loading') {

    document.addEventListener('DOMContentLoaded', initApp);

} else {

    initApp();

}



// ============================================

// CHART INITIALIZATION

// ============================================

function initChart() {

    const container = document.getElementById('tvChartContainer');

    if (!container) {

        console.error("CRITICAL: Chart container not found!");

        return;

    }



    try {

        console.log("DEBUG: Creating chart...");

        if (typeof LightweightCharts === 'undefined') {

            console.error("CRITICAL: LightweightCharts is undefined!");

            container.innerHTML = `<div style="color: white; padding: 20px;">Error: Charting library not loaded!</div>`;

            return;

        }



        window.chart = LightweightCharts.createChart(container, {

            width: container.clientWidth,

            height: container.clientHeight,

            layout: {

                background: { type: 'solid', color: '#1a1f2e' },

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

        chart = window.chart;



        createMainSeries();



        new ResizeObserver(entries => {

            if (entries[0] && chart) {

                const { width, height } = entries[0].contentRect;

                chart.applyOptions({ width, height });

            }

        }).observe(container);



        window.addEventListener('resize', () => {

            if (chart) {

                chart.applyOptions({ width: container.clientWidth, height: container.clientHeight });

            }

        });



        console.log("DEBUG: Chart initialized successfully");

    } catch (e) {

        console.error("CRITICAL: Chart Init Failed", e);

        container.innerHTML = `<div style="color: white; padding: 20px;">Chart Error: ${e.message}</div>`;

    }

}



// ============================================

// WEBSOCKET CONNECTION

// ============================================

function initWebSocket() {

    console.log("DEBUG: Initializing WebSocket...");

    try {

        if (typeof io === 'undefined') {

            console.error("CRITICAL: 'io' is undefined. socket.io.min.js might not be loaded!");

            updateConnectionStatus("Script Error", false);

            return;

        }

        socket = io();

        console.log("DEBUG: socket created", socket);

    } catch (e) {

        console.error("CRITICAL: WebSocket Init Error:", e);

        updateConnectionStatus("Init Error", false);

        return;

    }



    socket.on('connect', () => {

        console.log('✅ WebSocket connected', socket.id);

        updateConnectionStatus('Connected', true);

        socket.emit('subscribe', { index: currentIndex });

    });



    socket.on('disconnect', () => {

        console.log('❌ WebSocket disconnected');

        updateConnectionStatus('Disconnected', false);

    });



    socket.on('price_update', (data) => {

        console.log('📡 Price Update:', data);

        updateTickerDisplay(data);

    });



    socket.on('analysis_update', (data) => {

        updateFullAnalysis(data);

    });

}



function updateConnectionStatus(text, isConnected) {

    const status = document.getElementById('marketStatus');

    if (status) {

        status.innerHTML = `

            <span class="dot" style="background: ${isConnected ? 'var(--up-color)' : 'var(--down-color)'}"></span>

            <span class="text">${text}</span>

        `;

    }

}



// ============================================

// DATA LOADING

// ============================================

async function loadInitialData() {

    console.log(`DEBUG: Loading data for index: ${currentIndex}`);

    await Promise.all([

        loadAnalysis(),

        loadCandles(),

        loadOptionChain(),

        loadMLStats(),

        loadRecentTrades()

    ]);

}



async function loadAnalysis() {

    try {

        const response = await fetch(`${API_BASE}/api/analysis?index=${currentIndex}`);

        const data = await response.json();

        console.log(`DEBUG: Analysis received for ${currentIndex}:`, data);

        updateFullAnalysis(data);

    } catch (error) {

        console.error('Failed to load analysis:', error);

    }

}



async function loadCandles() {

    try {

        const response = await fetch(`${API_BASE}/api/candles?index=${currentIndex}&tf=${currentTimeframe}`);

        const data = await response.json();

        if (window.updateChart) {

            window.updateChart(data.candles);

        }

    } catch (error) {

        console.error('Failed to load candles:', error);

    }

}



async function loadOptionChain() {

    try {

        const response = await fetch(`${API_BASE}/api/option-chain?index=${currentIndex}`);

        const data = await response.json();

        updateOptionChain(data);

    } catch (error) {

        console.error('Failed to load option chain:', error);

    }

}



function startDataUpdates() {

    // Update analysis every 2 seconds

    setInterval(loadAnalysis, 2000);



    // Update candles every 5 seconds

    setInterval(loadCandles, 5000);



    // Update option chain every 10 seconds

    setInterval(loadOptionChain, 10000);

    

    // Update ML stats every 15 seconds

    setInterval(loadMLStats, 15000);

    // Auto-update recent trades every 5s

    setInterval(loadRecentTrades, 15000);

}



async function loadMLStats() {

    try {

        const response = await fetch(`${API_BASE}/api/ml-stats`);

        const stats = await response.json();

        

        const winRateEl = document.getElementById('accWinRate');

        const validatedEl = document.getElementById('accValidated');

        const winsLossesEl = document.getElementById('accWinsLosses');

        

        if (winRateEl) {

            winRateEl.textContent = `${stats.live_win_rate || 0}%`;

            winRateEl.style.color = (stats.live_win_rate >= 50) ? 'var(--up-color)' : 'var(--down-color)';

        }

        if (validatedEl) validatedEl.textContent = stats.total_validated || 0;

        if (winsLossesEl) winsLossesEl.textContent = `${stats.wins || 0} / ${stats.losses || 0}`;

        

    } catch (error) {

        console.error('Failed to load ML stats:', error);

    }

}



// ============================================

// UI UPDATES

// ============================================

function updateTickerDisplay(data) {

    if (data.error) {

        ['nifty', 'banknifty'].forEach(idx => {

            const priceEl = document.getElementById(`${idx}Price`);

            const changeEl = document.getElementById(`${idx}Change`);

            if (priceEl) priceEl.textContent = 'OFFLINE';

            if (changeEl) changeEl.textContent = '--';

        });

        return;

    }



    ['nifty', 'banknifty'].forEach(idx => {

        const priceEl = document.getElementById(`${idx}Price`);

        const changeEl = document.getElementById(`${idx}Change`);

        const tickerData = data[idx];



        if (priceEl && tickerData && tickerData.ltp) {

            const oldPrice = parseFloat(priceEl.dataset.last || 0);

            const newPrice = parseFloat(tickerData.ltp);



            if (newPrice !== oldPrice && oldPrice !== 0) {

                priceEl.classList.remove('flash-up', 'flash-down');

                void priceEl.offsetWidth;

                priceEl.classList.add(newPrice > oldPrice ? 'flash-up' : 'flash-down');

            }



            priceEl.dataset.last = newPrice;

            priceEl.textContent = newPrice.toFixed(2);

        } else if (priceEl && (!tickerData || !tickerData.ltp)) {

            priceEl.textContent = 'LOADING...';

        }



        if (changeEl && tickerData && tickerData.change !== undefined) {

            const change = parseFloat(tickerData.change);

            changeEl.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;

            changeEl.className = `ticker-change ${change >= 0 ? 'up' : 'down'}`;

        }

    });

}



function updateFullAnalysis(data) {

    if (!data || data.error) {

        console.log("DEBUG: Analysis has error or empty:", data?.error);

        return;

    }



    // Update prediction

    updatePrediction(data.prediction);



    // Update strategies

    if (data.strategies) {

        allStrategies = data.strategies;

        updateStrategiesGrid(data.strategies);

    }



    // Update trade recommendation with safe defaults

    if (data.trade_recommendation) {

        updateTradeRecommendation(data.trade_recommendation);

    }



    // Update option recommendation (Pro Feature)

    if (data.option_recommendation) {

        updateOptionRecommendation(data.option_recommendation);

    }



    // Update forward prediction (Pro Feature)

    if (data.forward_prediction) {

        updateForwardPrediction(data.forward_prediction);

    }



    // Update key levels

    if (data.indicators) {

        updateKeyLevels(data.indicators, data.price_data?.ltp);

    }



    // Update sentiment with VIX

    if (data.sentiment) {

        updateSentiment(data.sentiment, data.vix);

    }



    // Update ML info

    if (data.prediction?.ml) {

        updateMLInfo(data.prediction.ml);

    }



    // Update backtest info

    if (data.backtest) {

        updateBacktestInfo(data.backtest);

    }



    // Update pro confluence verdict

    if (data.pro_verdict) {

        updateProVerdict(data.pro_verdict);

    }

}



function updateProVerdict(verdict) {

    const card = document.getElementById('proVerdictCard');

    if (!card) return;

    card.style.display = '';

    const set = (id, text) => { const el = document.getElementById(id); if (el) el.textContent = text; };

    set('proVerdictAction', verdict.action || '--');

    set('proVerdictDirection', `${verdict.direction || '--'}`);

    set('proVerdictConfidence', `${verdict.confidence || '--'}%`);

    set('proVerdictVotes', `${verdict.bullish_votes ?? '--'}/${verdict.bearish_votes ?? '--'}/${verdict.neutral_votes ?? '--'}`);

    set('proVerdictRegime', verdict.regime || '--');

    const plan = verdict.trade_plan || {};

    set('proVerdictPlan', plan.entry
        ? `Entry ${plan.entry} | SL ${plan.stop_loss} | T1 ${plan.target_1} | T2 ${plan.target_2}`
        : (plan.note || '--'));

    const dirEl = document.getElementById('proVerdictDirection');

    if (dirEl) {
        dirEl.style.color = verdict.direction === 'BULLISH' ? 'var(--up-color)'
            : verdict.direction === 'BEARISH' ? 'var(--down-color)' : 'var(--text-primary)';
    }

}



function updatePrediction(prediction) {

    if (!prediction) return;



    const gaugeValue = document.getElementById('gaugeValue');

    const gaugeLabel = document.getElementById('gaugeLabel');

    const ceProb = document.getElementById('ceProb');

    const peProb = document.getElementById('peProb');



    if (gaugeValue) {

        gaugeValue.textContent = `${prediction.ce_prob || 50}%`;

    }



    if (gaugeLabel) {

        gaugeLabel.textContent = prediction.direction || 'ANALYZING';

        gaugeLabel.style.color = prediction.direction === 'BULLISH'

            ? 'var(--up-color)'

            : prediction.direction === 'BEARISH'

                ? 'var(--down-color)'

                : 'var(--accent-blue)';

    }



    if (ceProb) ceProb.textContent = `${prediction.ce_prob || 50}%`;

    if (peProb) peProb.textContent = `${prediction.pe_prob || 50}%`;

}



function updateStrategiesGrid(strategies) {

    const grid = document.getElementById('strategiesGrid');

    if (!grid) return;



    grid.innerHTML = strategies.map(strategy => `

        <div class="strategy-card ${strategy.signal}" onclick="showStrategyDetail('${strategy.name}')">

            <span class="strat-name">${strategy.name}</span>

            <div class="strat-signal">

                <span class="strat-signal-text ${strategy.signal}">${strategy.signal.toUpperCase()}</span>

                <span class="strat-strength">${strategy.strength}%</span>

            </div>

            <span class="strat-category">${strategy.category || 'technical'}</span>

        </div>

    `).join('');

}



function updateTradeRecommendation(rec) {

    const panel = document.getElementById('tradeSuggestionsPanel');

    if (!panel) return;



    const signalClass = rec.direction === 'BULLISH' ? 'bullish' : 'bearish';



    // Safe value extraction with defaults

    const entry = rec.entry !== undefined ? rec.entry.toFixed(2) : 'N/A';

    const stopLoss = rec.stop_loss !== undefined ? rec.stop_loss.toFixed(2) : 'N/A';

    const target = rec.target !== undefined ? rec.target.toFixed(2) : 'N/A';

    const lots = rec.suggested_lots !== undefined ? rec.suggested_lots : 1;

    const rr = rec.risk_reward !== undefined ? rec.risk_reward.toFixed(2) : 'N/A';

    const profit = rec.profit_on_target !== undefined ? rec.profit_on_target.toFixed(0) : 'N/A';

    const maxLoss = rec.max_loss !== undefined ? rec.max_loss.toFixed(0) : 'N/A';



    panel.innerHTML = `

        <div class="trade-signal ${signalClass}">

            <h4>${rec.direction || 'NEUTRAL'} SIGNAL</h4>

            <div class="trade-details">

                <div class="trade-row highlight">

                    <span class="label">Recommendation:</span>

                    <span class="value bold">${rec.recommendation || 'WAIT'}</span>

                </div>

                <div class="trade-row">

                    <span class="label">Entry Price:</span>

                    <span class="value">${entry}</span>

                </div>

                <div class="trade-row">

                    <span class="label">Stop Loss:</span>

                    <span class="value error">${stopLoss}</span>

                </div>

                <div class="trade-row">

                    <span class="label">Target:</span>

                    <span class="value success">${target}</span>

                </div>

                <div class="trade-row highlight">

                    <span class="label">Suggested Lots:</span>

                    <span class="value bold">${lots}</span>

                </div>

                <div class="trade-row">

                    <span class="label">Risk-Reward:</span>

                    <span class="value">${rr}:1</span>

                </div>

                <div class="trade-row highlight">

                    <span class="label">Profit at Target:</span>

                    <span class="value success">₹${profit}</span>

                </div>

                <div class="trade-row">

                    <span class="label">Max Loss:</span>

                    <span class="value error">₹${maxLoss}</span>

                </div>

            </div>

        </div>

    `;

}



function updateOptionRecommendation(rec) {

    // Add option recommendation to trade panel if available

    const panel = document.getElementById('tradeSuggestionsPanel');

    if (!panel || !rec || !rec.strike) return;



    const existingOptRec = panel.querySelector('.option-rec');

    if (existingOptRec) existingOptRec.remove();



    const optRecHtml = `

        <div class="option-rec" style="margin-top: 15px; padding: 10px; background: rgba(59,130,246,0.1); border-radius: 8px; border-left: 3px solid var(--accent-blue);">

            <h5 style="margin: 0 0 8px 0; color: var(--accent-blue);">🎯 OPTION PICK</h5>

            <div style="font-size: 1.1em; font-weight: bold; color: var(--text-primary);">${rec.recommendation || 'N/A'}</div>

            <div style="margin-top: 8px; color: var(--text-secondary); font-size: 0.9em;">

                <div>Premium: ₹${rec.premium || 'N/A'} → Target: ₹${rec.target_premium || 'N/A'}</div>

                <div>Profit/Lot: ₹${rec.profit_per_lot || 'N/A'}</div>

                <div>Confidence: ${rec.confidence || 0}%</div>

            </div>

        </div>

    `;



    panel.insertAdjacentHTML('beforeend', optRecHtml);

}



function updateForwardPrediction(pred) {

    // Add 15-min prediction display

    const mlStats = document.getElementById('mlStats');

    if (!mlStats) return;



    const existingFwd = document.getElementById('forwardPrediction');

    if (existingFwd) existingFwd.remove();



    const dirColor = pred.direction === 'BULLISH' ? 'var(--up-color)' :

        pred.direction === 'BEARISH' ? 'var(--down-color)' : 'var(--text-secondary)';



    const fwdHtml = `

        <div id="forwardPrediction" style="margin-top: 12px; padding: 10px; background: rgba(16, 185, 129, 0.1); border-radius: 8px;">

            <div style="font-size: 0.8em; color: var(--text-secondary);">${currentIndex.toUpperCase()} - NEXT 15 MIN:</div>

            <div style="font-size: 1.2em; font-weight: bold; color: ${dirColor};">${pred.direction || 'NEUTRAL'}</div>

            <div style="font-size: 0.85em; color: var(--text-secondary);">Confidence: ${pred.confidence || 0}%</div>

            <div style="font-size: 0.8em; color: var(--text-muted); margin-top: 4px;">${pred.reasoning || ''}</div>

        </div>

    `;



    mlStats.insertAdjacentHTML('beforeend', fwdHtml);

}



function updateKeyLevels(indicators, currentPrice) {

    const resEl = document.getElementById('resistanceLevels');

    const supEl = document.getElementById('supportLevels');

    const curEl = document.getElementById('currentPrice');



    if (indicators.pivot_points) {

        const pivots = indicators.pivot_points;



        if (resEl) {

            resEl.innerHTML = `

                <div class="level-item"><span class="lbl">R2</span> <span class="val down">${pivots.r2?.toFixed(2) || '--'}</span></div>

                <div class="level-item"><span class="lbl">R1</span> <span class="val down">${pivots.r1?.toFixed(2) || '--'}</span></div>

            `;

        }



        if (supEl) {

            supEl.innerHTML = `

                <div class="level-item"><span class="lbl">S1</span> <span class="val up">${pivots.s1?.toFixed(2) || '--'}</span></div>

                <div class="level-item"><span class="lbl">S2</span> <span class="val up">${pivots.s2?.toFixed(2) || '--'}</span></div>

            `;

        }

    }



    if (curEl && currentPrice) {

        curEl.textContent = currentPrice.toFixed(2);

    }

}



function updateSentiment(sentiment, vixData) {

    const vixEl = document.getElementById('vixValue');

    const pcrEl = document.getElementById('pcrValue');

    const fiiEl = document.getElementById('fiiValue');

    const diiEl = document.getElementById('diiValue');



    // VIX from sentiment or separate vixData

    let vixValue = sentiment.vix;

    if (vixData && vixData.ltp) {

        vixValue = vixData.ltp;

    }



    if (vixEl) {

        vixEl.textContent = vixValue ? vixValue.toFixed(2) : '--';

        vixEl.style.color = vixValue > 18 ? 'var(--down-color)' : 'var(--up-color)';

    }



    if (pcrEl) {

        const pcr = sentiment.pcr || 1.0;

        pcrEl.textContent = pcr.toFixed(2);

        pcrEl.style.color = pcr > 1.2 ? 'var(--up-color)' : pcr < 0.8 ? 'var(--down-color)' : 'var(--text-primary)';

    }



    if (fiiEl) {

        const fii = sentiment.fii_net || 0;

        fiiEl.textContent = `${fii > 0 ? '+' : ''}${fii}`;

        fiiEl.style.color = fii > 0 ? 'var(--up-color)' : 'var(--down-color)';

    }



    if (diiEl) {

        const dii = sentiment.dii_net || 0;

        diiEl.textContent = `${dii > 0 ? '+' : ''}${dii}`;

        diiEl.style.color = dii > 0 ? 'var(--up-color)' : 'var(--down-color)';

    }

}



function updateMLInfo(mlPrediction) {

    const agreementEl = document.getElementById('modelAgreement');

    const confidenceEl = document.getElementById('confidence');

    const rfEl = document.getElementById('rfPrediction');

    const gbEl = document.getElementById('gbPrediction');

    const statusEl = document.getElementById('mlStatus');

    const featuresEl = document.getElementById('featuresList');



    if (agreementEl) {

        agreementEl.textContent = `${mlPrediction.model_agreement || 0}%`;

    }



    if (confidenceEl) {

        confidenceEl.textContent = `${mlPrediction.confidence || 0}%`;

    }



    if (rfEl) {

        rfEl.textContent = mlPrediction.rf_prediction || '--';

        rfEl.style.color = mlPrediction.rf_prediction === 'BULLISH' ? 'var(--up-color)' : 'var(--down-color)';

    }



    if (gbEl) {

        gbEl.textContent = mlPrediction.gb_prediction || '--';

        gbEl.style.color = mlPrediction.gb_prediction === 'BULLISH' ? 'var(--up-color)' : 'var(--down-color)';

    }



    if (statusEl) {

        statusEl.textContent = 'Active';

        statusEl.classList.add('trained');

    }



    if (featuresEl && mlPrediction.top_features) {

        featuresEl.innerHTML = mlPrediction.top_features.map(f => `

            <div class="feature-item">

                <span>${f.name}</span>

                <span>${f.importance}%</span>

            </div>

            <div class="feature-bar" style="width: ${f.importance}%"></div>

        `).join('');

    }

}



function updateBacktestInfo(backtest) {

    // Add backtest results to ML panel

    const mlStats = document.getElementById('mlStats');

    if (!mlStats) return;



    const existingBt = document.getElementById('backtestInfo');

    if (existingBt) existingBt.remove();



    const winColor = backtest.win_rate > 50 ? 'var(--up-color)' : 'var(--down-color)';



    const btHtml = `

        <div id="backtestInfo" style="margin-top: 12px; padding: 10px; background: rgba(139, 92, 246, 0.1); border-radius: 8px;">

            <div style="font-size: 0.8em; color: var(--text-secondary);">${currentIndex.toUpperCase()} BACKTEST (${backtest.backtest_period || 'N/A'}):</div>

            <div style="display: flex; justify-content: space-between; margin-top: 4px;">

                <span style="color: ${winColor};">Win: ${backtest.win_rate || 0}%</span>

                <span>Trades: ${backtest.total_trades || 0}</span>

            </div>

            <div style="font-size: 0.85em; color: var(--text-secondary);">Avg: ${backtest.avg_profit_pct || 0}%</div>

        </div>

    `;



    mlStats.insertAdjacentHTML('beforeend', btHtml);

}



// ============================================

// CHART SERIES

// ============================================

window.createMainSeries = function () {

    if (!chart) return;



    try {

        console.log(`DEBUG: Creating series of type: ${currentChartType}`);



        if (mainSeries) {

            try { chart.removeSeries(mainSeries); } catch (e) { }

            mainSeries = null;

        }



        const candleOptions = {

            upColor: '#10b981', downColor: '#ef4444', borderVisible: false,

            wickUpColor: '#10b981', wickDownColor: '#ef4444',

        };



        const lineOptions = { color: '#3b82f6', lineWidth: 2 };



        if (currentChartType === 'candle' || currentChartType === 'candlestick') {

            mainSeries = chart.addCandlestickSeries(candleOptions);

        } else {

            mainSeries = chart.addLineSeries(lineOptions);

        }



        console.log("DEBUG: Series created successfully");

    } catch (e) {

        console.error("CRITICAL: Series Creation Failed", e);

    }

}



window.parseCandleTime = function(t) {

    if (typeof t === 'number') {

        return t > 1e11 ? Math.floor(t / 1000) : Math.floor(t);

    }

    if (typeof t === 'string') {

        let clean = t.trim().replace(' ', 'T');

        if (!clean.includes('Z') && !clean.includes('+')) {

            clean += '+05:30';

        }

        const ms = Date.parse(clean);

        if (!isNaN(ms)) {

            return Math.floor(ms / 1000);

        }

        const parts = t.split(/[- :T]/);

        if (parts.length >= 3) {

            const y = parseInt(parts[0]), m = parseInt(parts[1]) - 1, d = parseInt(parts[2]);

            const hh = parts[3] ? parseInt(parts[3]) : 0;

            const mm = parts[4] ? parseInt(parts[4]) : 0;

            const ss = parts[5] ? parseInt(parts[5]) : 0;

            return Math.floor(new Date(y, m, d, hh, mm, ss).getTime() / 1000);

        }

    }

    return Math.floor(Date.now() / 1000);

};



window.updateChart = function (candles) {

    if (!mainSeries || !candles || candles.length === 0) return;



    try {

        const parsed = [];

        const seen = new Set();

        for (const c of candles) {

            const t = window.parseCandleTime(c.time || c.timestamp);

            if (seen.has(t)) continue;

            seen.add(t);

            const open = parseFloat(c.open || 0);

            const high = parseFloat(c.high || 0);

            const low = parseFloat(c.low || 0);

            const close = parseFloat(c.close || 0);

            if (currentChartType === 'candle' || currentChartType === 'candlestick') {

                parsed.push({ time: t, open, high, low, close });

            } else {

                parsed.push({ time: t, value: close });

            }

        }

        parsed.sort((a, b) => a.time - b.time);



        mainSeries.setData(parsed);

        chart.timeScale().fitContent();

    } catch (e) {

        console.error("Chart Data Update Error:", e);

    }

};



// ============================================
// RECENT TRADES HANDLERS (NIFTY & BANKNIFTY)
// ============================================

window.currentNiftyTrades = [];
window.currentBankniftyTrades = [];

window.loadNiftyTrades = async function() {
    const hoursSelect = document.getElementById('niftyTradesHours');
    const hours = hoursSelect ? hoursSelect.value : 4;
    try {
        const response = await fetch(`${API_BASE}/api/recent-trades?index=nifty&hours=${hours}`);
        const data = await response.json();
        window.currentNiftyTrades = data.trades || [];
        renderTradesSection(data, 'nifty');
    } catch (err) {
        console.error('Failed to load Nifty recent trades:', err);
    }
};

window.loadBankniftyTrades = async function() {
    const hoursSelect = document.getElementById('bankniftyTradesHours');
    const hours = hoursSelect ? hoursSelect.value : 4;
    try {
        const response = await fetch(`${API_BASE}/api/recent-trades?index=banknifty&hours=${hours}`);
        const data = await response.json();
        window.currentBankniftyTrades = data.trades || [];
        renderTradesSection(data, 'banknifty');
    } catch (err) {
        console.error('Failed to load BankNifty recent trades:', err);
    }
};

window.loadRecentTrades = async function() {
    await Promise.all([
        window.loadNiftyTrades(),
        window.loadBankniftyTrades()
    ]);
};

function renderTradesSection(data, prefix) {
    if (!data || !data.summary) return;
    const s = data.summary;
    const trades = data.trades || [];

    const isBn = prefix === 'banknifty';
    const wrEl    = document.getElementById(isBn ? 'bnWinRate' : 'niftyWinRate');
    const ttEl    = document.getElementById(isBn ? 'bnTotalTrades' : 'niftyTotalTrades');
    const wlEl    = document.getElementById(isBn ? 'bnWinsLosses' : 'niftyWinsLosses');
    const npEl    = document.getElementById(isBn ? 'bnNetPoints' : 'niftyNetPoints');
    const pnlEl   = document.getElementById(isBn ? 'bnNetPnl' : 'niftyNetPnl');
    const streakEl = document.getElementById(isBn ? 'bnStreak' : 'niftyStreak');
    const body    = document.getElementById(isBn ? 'bankniftyTradesBody' : 'niftyTradesBody');

    // Stats bar
    if (wrEl) {
        wrEl.textContent = `${s.win_rate}%`;
        wrEl.style.color = s.win_rate >= 55 ? 'var(--up-color)' :
                           s.win_rate >= 45 ? 'var(--text-warning, #f59e0b)' : 'var(--down-color)';
    }
    if (ttEl) {
        const activeNote = s.active ? ` <span style="font-size:0.7rem;color:var(--accent-blue);">(${s.active} live)</span>` : '';
        ttEl.innerHTML = `${s.wins + s.losses}${activeNote}`;
    }
    if (wlEl) wlEl.textContent = `${s.wins}W - ${s.losses}L`;
    if (npEl) {
        const pfx = s.total_points > 0 ? '+' : '';
        npEl.textContent = `${pfx}${s.total_points} pts`;
        npEl.style.color = s.total_points >= 0 ? 'var(--up-color)' : 'var(--down-color)';
    }
    if (pnlEl) {
        const pfx = s.total_pnl > 0 ? '+' : '';
        pnlEl.textContent = `₹${pfx}${Number(s.total_pnl).toLocaleString()}`;
        pnlEl.style.color = s.total_pnl >= 0 ? 'var(--up-color)' : 'var(--down-color)';
    }
    if (streakEl) {
        if (s.streak && s.streak.count > 1) {
            const icon  = s.streak.type === 'WINNING' ? '🔥' : '⚠️';
            const label = s.streak.type === 'WINNING' ? 'Wins' : 'Losses';
            streakEl.textContent = `${icon} ${s.streak.count} ${label}`;
            streakEl.style.color = s.streak.type === 'WINNING' ? 'var(--up-color)' : 'var(--down-color)';
        } else if (s.streak && s.streak.count === 1) {
            streakEl.textContent = s.streak.type === 'WINNING' ? '✅ 1 Win' : '❌ 1 Loss';
            streakEl.style.color = s.streak.type === 'WINNING' ? 'var(--up-color)' : 'var(--down-color)';
        } else {
            streakEl.textContent = '-';
            streakEl.style.color = 'var(--text-secondary)';
        }
    }

    if (!body) return;
    if (trades.length === 0) {
        body.innerHTML = '<tr><td colspan="10" style="text-align:center;padding:20px;color:var(--text-muted);">No signals generated in this timeframe yet</td></tr>';
        return;
    }

    body.innerHTML = trades.map((t, idx) => {
        const isWin    = t.result === 'WIN';
        const isLoss   = t.result === 'LOSS';
        const isActive = t.result === 'ACTIVE';

        const statusBg    = isWin    ? 'rgba(16,185,129,0.18)' :
                            isLoss   ? 'rgba(239,68,68,0.18)'  :
                            isActive ? 'rgba(59,130,246,0.18)' : 'rgba(120,120,120,0.18)';
        const statusColor = isWin    ? '#10b981' :
                            isLoss   ? '#ef4444'  :
                            isActive ? '#3b82f6'  : '#888';
        const statusLabel = isActive
            ? '<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#3b82f6;animation:pulse 1.2s infinite;margin-right:4px;vertical-align:middle;"></span>LIVE'
            : t.result;

        const actionColor = t.direction === 'BULLISH' ? '#10b981' : '#ef4444';
        const actionBg    = t.direction === 'BULLISH' ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)';
        const pnlPrefix   = t.pnl_per_lot > 0 ? '+' : '';
        const ptsPrefix   = t.points > 0 ? '+' : '';

        // format time as HH:MM
        let timeDisplay = t.time || '';
        if (timeDisplay.includes(' '))      timeDisplay = timeDisplay.split(' ')[1].substring(0, 5);
        else if (timeDisplay.includes('T')) timeDisplay = timeDisplay.split('T')[1].substring(0, 5);

        const ptsColor = t.points >= 0 ? '#10b981' : '#ef4444';
        const pnlColor = t.pnl_per_lot >= 0 ? '#10b981' : '#ef4444';

        const exitLabel = isActive
            ? `<span style="font-size:0.68rem;color:#3b82f6;margin-right:2px;">LTP</span>₹${t.exit.toFixed(1)}`
            : `₹${t.exit.toFixed(1)}`;

        return `
            <tr onclick="showTradeDetails('${prefix}', ${idx})"
                title="Click to view full strategy, indicator snapshot & trade reasoning"
                style="border-bottom:1px solid rgba(255,255,255,0.04);transition:all 0.15s ease;cursor:pointer;"
                onmouseover="this.style.background='rgba(59,130,246,0.08)'"
                onmouseout="this.style.background='transparent'">
                <td style="padding:9px 10px;font-weight:600;color:var(--text-primary);">
                    ${timeDisplay}
                    <span style="font-size:0.7rem;color:#3b82f6;margin-left:4px;opacity:0.7;">ℹ️</span>
                </td>
                <td style="padding:9px 10px;font-weight:700;color:${actionColor};">
                    <span style="background:${actionBg};padding:2px 7px;border-radius:4px;">${t.action}</span>
                </td>
                <td style="padding:9px 10px;color:var(--text-primary);font-family:monospace;">₹${t.entry.toFixed(1)}</td>
                <td style="padding:9px 10px;color:#10b981;font-family:monospace;">₹${t.target.toFixed(1)}</td>
                <td style="padding:9px 10px;color:#ef4444;font-family:monospace;">₹${t.stop_loss.toFixed(1)}</td>
                <td style="padding:9px 10px;color:var(--text-primary);font-family:monospace;">${exitLabel}</td>
                <td style="padding:9px 10px;font-weight:600;color:${ptsColor};font-family:monospace;">${ptsPrefix}${t.points.toFixed(1)}</td>
                <td style="padding:9px 10px;font-weight:700;color:${pnlColor};font-family:monospace;">₹${pnlPrefix}${Number(t.pnl_per_lot).toLocaleString()}</td>
                <td style="padding:9px 10px;text-align:center;">
                    <span style="background:${statusBg};color:${statusColor};font-weight:700;font-size:0.75rem;padding:3px 9px;border-radius:4px;display:inline-block;">
                        ${statusLabel}
                    </span>
                </td>
                <td style="padding:9px 10px;color:var(--text-muted);font-size:0.78rem;">${t.reason}</td>
            </tr>
        `;
    }).join('');
}

window.showTradeDetails = function(prefix, idx) {
    const list = prefix === 'banknifty' ? window.currentBankniftyTrades : window.currentNiftyTrades;
    if (!list || !list[idx]) return;
    const t = list[idx];
    const ind = t.indicators || {};

    const modal = document.getElementById('tradeDetailModal');
    const badge = document.getElementById('mdlActionBadge');
    const title = document.getElementById('mdlTitle');
    const body = document.getElementById('mdlBody');
    if (!modal || !body) return;

    const isBull = t.direction === 'BULLISH';
    const isWin = t.result === 'WIN';
    const isLoss = t.result === 'LOSS';
    const statusBg = isWin ? '#10b981' : (isLoss ? '#ef4444' : '#3b82f6');
    const pnlPrefix = t.pnl_per_lot > 0 ? '+' : '';
    const ptsPrefix = t.points > 0 ? '+' : '';

    if (badge) {
        badge.textContent = t.action;
        badge.style.background = isBull ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)';
        badge.style.color = isBull ? '#10b981' : '#ef4444';
        badge.style.border = `1px solid ${isBull ? '#10b981' : '#ef4444'}`;
    }

    if (title) {
        title.innerHTML = `${prefix.toUpperCase()} Order Audit &bull; <span style="font-weight:400;color:#888;">${t.time}</span>`;
    }

    const rsiVal = ind.rsi !== null && ind.rsi !== undefined ? ind.rsi : 'N/A';
    const ema20Val = ind.ema20 !== null && ind.ema20 !== undefined ? `₹${ind.ema20}` : 'N/A';
    const ema50Val = ind.ema50 !== null && ind.ema50 !== undefined ? `₹${ind.ema50}` : 'N/A';
    const macdHist = ind.macd_hist !== null && ind.macd_hist !== undefined ? ind.macd_hist : 'N/A';
    const supertrend = (ind.supertrend || 'N/A').toUpperCase();

    const reasonsList = (ind.reasons_all && ind.reasons_all.length > 0)
        ? ind.reasons_all.map(r => `<li style="margin-bottom:6px; color:#10b981;">&#10003; <strong>${r}</strong></li>`).join('')
        : `<li style="color:#888;">${t.reason}</li>`;

    body.innerHTML = `
        <!-- Top Status Banner -->
        <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.03); padding:12px 16px; border-radius:8px; margin-bottom:18px;">
            <div>
                <span style="font-size:0.75rem; color:#888; text-transform:uppercase; letter-spacing:0.5px;">Order Outcome</span>
                <div style="font-size:1.2rem; font-weight:800; color:${statusBg}; margin-top:2px;">
                    ${t.result} (${ptsPrefix}${t.points} pts)
                </div>
            </div>
            <div style="text-align:right;">
                <span style="font-size:0.75rem; color:#888; text-transform:uppercase; letter-spacing:0.5px;">Realized P&L (1 Lot)</span>
                <div style="font-size:1.2rem; font-weight:800; color:${t.pnl_per_lot >= 0 ? '#10b981' : '#ef4444'}; margin-top:2px;">
                    ₹${pnlPrefix}${Number(t.pnl_per_lot).toLocaleString()}
                </div>
            </div>
        </div>

        <!-- Order Levels Grid -->
        <h4 style="margin:0 0 10px 0; font-size:0.82rem; color:#888; text-transform:uppercase; letter-spacing:0.5px;">Executed Order Parameters</h4>
        <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:10px; margin-bottom:20px;">
            <div style="background:#1e222d; padding:10px; border-radius:6px; border:1px solid #2a2e39;">
                <div style="font-size:0.72rem; color:#888;">Entry Fill</div>
                <div style="font-size:1.05rem; font-weight:700; color:#fff; font-family:monospace; margin-top:2px;">₹${t.entry.toFixed(1)}</div>
            </div>
            <div style="background:#1e222d; padding:10px; border-radius:6px; border:1px solid #2a2e39;">
                <div style="font-size:0.72rem; color:#10b981;">Target (${isBull ? '+' : '-'}${Math.abs(t.target - t.entry).toFixed(0)} pts)</div>
                <div style="font-size:1.05rem; font-weight:700; color:#10b981; font-family:monospace; margin-top:2px;">₹${t.target.toFixed(1)}</div>
            </div>
            <div style="background:#1e222d; padding:10px; border-radius:6px; border:1px solid #2a2e39;">
                <div style="font-size:0.72rem; color:#ef4444;">Stop Loss (${isBull ? '-' : '+'}${Math.abs(t.stop_loss - t.entry).toFixed(0)} pts)</div>
                <div style="font-size:1.05rem; font-weight:700; color:#ef4444; font-family:monospace; margin-top:2px;">₹${t.stop_loss.toFixed(1)}</div>
            </div>
            <div style="background:#1e222d; padding:10px; border-radius:6px; border:1px solid #2a2e39;">
                <div style="font-size:0.72rem; color:#888;">${t.result === 'ACTIVE' ? 'Live LTP' : 'Exit Price'}</div>
                <div style="font-size:1.05rem; font-weight:700; color:#fff; font-family:monospace; margin-top:2px;">₹${t.exit.toFixed(1)}</div>
            </div>
        </div>

        <!-- Strategy Confluence & Indicators Snapshot -->
        <h4 style="margin:0 0 10px 0; font-size:0.82rem; color:#888; text-transform:uppercase; letter-spacing:0.5px;">Technical Indicators at Entry Candle</h4>
        <div style="background:#1e222d; padding:14px; border-radius:8px; border:1px solid #2a2e39; margin-bottom:18px;">
            <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:12px; margin-bottom:12px;">
                <div>
                    <span style="font-size:0.75rem; color:#888;">RSI (14):</span>
                    <span style="font-weight:700; color:${rsiVal > 50 ? '#10b981' : '#ef4444'}; margin-left:6px;">${rsiVal}</span>
                </div>
                <div>
                    <span style="font-size:0.75rem; color:#888;">SuperTrend:</span>
                    <span style="font-weight:700; color:${supertrend === 'BULLISH' ? '#10b981' : '#ef4444'}; margin-left:6px;">${supertrend}</span>
                </div>
                <div>
                    <span style="font-size:0.75rem; color:#888;">MACD Hist:</span>
                    <span style="font-weight:700; color:${macdHist >= 0 ? '#10b981' : '#ef4444'}; margin-left:6px;">${macdHist}</span>
                </div>
                <div>
                    <span style="font-size:0.75rem; color:#888;">EMA 20:</span>
                    <span style="font-weight:700; color:#fff; font-family:monospace; margin-left:6px;">${ema20Val}</span>
                </div>
                <div>
                    <span style="font-size:0.75rem; color:#888;">EMA 50:</span>
                    <span style="font-weight:700; color:#fff; font-family:monospace; margin-left:6px;">${ema50Val}</span>
                </div>
                <div>
                    <span style="font-size:0.75rem; color:#888;">Trend State:</span>
                    <span style="font-weight:700; color:#10b981; margin-left:6px;">${isBull ? 'EMA 20 > EMA 50' : 'EMA 20 < EMA 50'}</span>
                </div>
            </div>

            <div style="border-top:1px solid rgba(255,255,255,0.06); padding-top:10px; margin-top:8px;">
                <div style="font-size:0.75rem; color:#888; margin-bottom:6px;">Active Strategy Signals Met:</div>
                <ul style="margin:0; padding-left:20px; font-size:0.85rem;">
                    ${reasonsList}
                </ul>
            </div>
        </div>

        <!-- Position Sizing Breakdown -->
        <div style="background:rgba(255,255,255,0.02); padding:10px 14px; border-radius:6px; font-size:0.8rem; color:#888; display:flex; justify-content:space-between;">
            <div>Contract Lot Size: <strong style="color:#fff;">${t.lot_size} Qty</strong></div>
            <div>Risk-to-Reward: <strong style="color:#10b981;">1 : 1.75</strong></div>
            <div>Instrument: <strong style="color:#fff;">${prefix.toUpperCase()} ATM Options</strong></div>
        </div>
    `;

    modal.style.display = 'flex';
};

window.closeTradeModal = function() {
    const modal = document.getElementById('tradeDetailModal');
    if (modal) modal.style.display = 'none';
};

window.addEventListener('click', function(e) {
    const modal = document.getElementById('tradeDetailModal');
    if (modal && e.target === modal) {
        modal.style.display = 'none';
    }
});


function updateOptionChain(data) {

    const body = document.getElementById('optionChainBody');

    const expiryEl = document.getElementById('expiryDisplay');



    if (expiryEl && data.expiry) {

        expiryEl.textContent = `EXPIRY: ${data.expiry}`;

    }



    if (!body || !data.chain) {

        if (body) body.innerHTML = '<div class="oc-row">No data available</div>';

        return;

    }



    body.innerHTML = data.chain.map(row => `

        <div class="oc-row ${row.is_atm ? 'atm' : ''}">

            <span class="oc-ce">${(row.ce_oi / 100000).toFixed(1)}L</span>

            <span class="oc-strike">${row.strike}</span>

            <span class="oc-pe">${(row.pe_oi / 100000).toFixed(1)}L</span>

        </div>

    `).join('');

}



// ============================================

// USER ACTIONS (Exposed to Global Scope)

// ============================================



window.selectIndex = function (index) {

    console.log(`DEBUG: Switching to index: ${index}`);

    currentIndex = index;



    // Update buttons

    document.querySelectorAll('.sym-btn').forEach(btn => {

        btn.classList.remove('active');

    });

    const clickedBtn = Array.from(document.querySelectorAll('.sym-btn')).find(b => b.textContent.toLowerCase().includes(index.toLowerCase()));

    if (clickedBtn) clickedBtn.classList.add('active');



    // Clear existing data to show loading state

    const tradepanel = document.getElementById('tradeSuggestionsPanel');

    if (tradepanel) {

        tradepanel.innerHTML = `<div class="trade-signal neutral"><h4>LOADING ${index.toUpperCase()}...</h4></div>`;

    }



    // Reload ALL data for new index

    loadInitialData();



    // Subscribe to new index

    if (socket && socket.connected) {

        socket.emit('subscribe', { index: currentIndex });

    }

};



window.changeTimeframe = function (tf) {

    currentTimeframe = tf;



    document.querySelectorAll('.tf-btn').forEach(btn => {

        btn.classList.remove('active');

    });

    const clickedBtn = Array.from(document.querySelectorAll('.tf-btn')).find(b => b.textContent.toLowerCase().includes(tf.toLowerCase()));

    if (clickedBtn) clickedBtn.classList.add('active');



    loadCandles();

};



window.setChartType = function (type) {

    if (currentChartType === type) return;

    currentChartType = type;



    document.querySelectorAll('.chart-btn').forEach(btn => {

        btn.classList.remove('active');

    });



    createMainSeries();

    loadCandles();

};



window.filterStrategies = function (category) {

    document.querySelectorAll('.strat-tab').forEach(tab => {

        tab.classList.remove('active');

    });



    const filtered = category === 'all'

        ? allStrategies

        : allStrategies.filter(s => s.category === category);



    updateStrategiesGrid(filtered);

};



window.showStrategyDetail = function (strategyName) {

    const strategy = allStrategies.find(s => s.name === strategyName);

    if (!strategy) return;



    const modal = document.getElementById('strategyModal');

    const title = document.getElementById('modalTitle');

    const signalEl = document.getElementById('modalSignal');

    const strengthEl = document.getElementById('modalStrength');

    const reasonEl = document.getElementById('modalReason');



    if (title) title.textContent = strategy.name;

    if (signalEl) {

        signalEl.textContent = strategy.signal.toUpperCase();

        signalEl.style.color = strategy.signal === 'bullish' ? 'var(--up-color)' : strategy.signal === 'bearish' ? 'var(--down-color)' : 'var(--text-primary)';

    }

    if (strengthEl) strengthEl.textContent = `${strategy.strength}%`;

    if (reasonEl) reasonEl.textContent = strategy.reason;

    // Pro strategies ship tradeable levels — show them when present
    const levelsRow = document.getElementById('modalLevelsRow');
    const levelsEl = document.getElementById('modalLevels');
    if (levelsRow && levelsEl) {
        if (strategy.entry !== undefined && strategy.stop_loss !== undefined && strategy.target !== undefined) {
            levelsEl.textContent = `Entry ${strategy.entry} | SL ${strategy.stop_loss} | Target ${strategy.target}`;
            levelsRow.style.display = '';
        } else {
            levelsRow.style.display = 'none';
        }
    }



    if (modal) modal.classList.add('active');

};



window.closeModal = function () {

    const modal = document.getElementById('strategyModal');

    if (modal) modal.classList.remove('active');

};



window.trainModel = async function () {

    const statusEl = document.getElementById('mlStatus');

    if (statusEl) {

        statusEl.textContent = 'Training...';

        statusEl.classList.remove('trained');

        statusEl.classList.add('training');

    }



    try {

        const response = await fetch(`${API_BASE}/api/train-ml?index=${currentIndex}`);

        const data = await response.json();



        if (statusEl) {

            statusEl.textContent = data.success ? 'Trained' : 'Failed';

            statusEl.classList.remove('training');

            if (data.success) statusEl.classList.add('trained');

        }



        loadAnalysis();

    } catch (error) {

        console.error('Training failed:', error);

        if (statusEl) {

            statusEl.textContent = 'Error';

            statusEl.classList.remove('training');

        }

    }

};



// Global Listeners

document.addEventListener('click', (e) => {

    const modal = document.getElementById('strategyModal');

    if (modal && e.target === modal) closeModal();

});



document.addEventListener('keydown', (e) => {

    if (e.key === 'Escape') closeModal();

});



// ============================================

// STOCK PICKS LOADING

// ============================================

async function loadStockPicks() {

    console.log("DEBUG: Loading stock picks...");

    loadShortTermPicks();

    loadLongTermPicks();

}



async function loadShortTermPicks() {

    const container = document.getElementById('shortTermPicks');

    const countBadge = document.getElementById('shortTermCount');

    if (!container) return;



    try {

        const response = await fetch(`${API_BASE}/api/top-stocks/short-term?count=10`);

        const data = await response.json();



        if (data.picks && data.picks.length > 0) {

            container.innerHTML = data.picks.map((stock, idx) => renderStockPickRow(stock, idx + 1, 'short')).join('');

            if (countBadge) countBadge.textContent = `${data.picks.length} Stocks`;

        } else {

            container.innerHTML = '<div class="loading-picks">No stocks found</div>';

        }



        updateLastUpdateTime();

    } catch (error) {

        console.error('Error loading short-term picks:', error);

        container.innerHTML = '<div class="loading-picks">Error loading data</div>';

    }

}



async function loadLongTermPicks() {

    const container = document.getElementById('longTermPicks');

    const countBadge = document.getElementById('longTermCount');

    if (!container) return;



    try {

        const response = await fetch(`${API_BASE}/api/top-stocks/long-term?count=10`);

        const data = await response.json();



        if (data.picks && data.picks.length > 0) {

            container.innerHTML = data.picks.map((stock, idx) => renderStockPickRow(stock, idx + 1, 'long')).join('');

            if (countBadge) countBadge.textContent = `${data.picks.length} Stocks`;

        } else {

            container.innerHTML = '<div class="loading-picks">No stocks found</div>';

        }

    } catch (error) {

        console.error('Error loading long-term picks:', error);

        container.innerHTML = '<div class="loading-picks">Error loading data</div>';

    }

}



function renderStockPickRow(stock, rank, type) {

    const changeClass = stock.change >= 0 ? 'up' : 'down';

    const changeSign = stock.change >= 0 ? '+' : '';

    const score = type === 'short' ? stock.short_term_score : stock.long_term_score;

    const signal = type === 'short' ? stock.short_term_signal : stock.long_term_signal;

    const scoreClass = score >= 70 ? 'high' : '';



    let signalClass = 'hold';

    if (signal && (signal.includes('BUY') || signal.includes('STRONG'))) signalClass = 'buy';

    else if (signal && signal.includes('SELL')) signalClass = 'sell';



    return `

        <div class="stock-pick-row" onclick="showStockDetail('${stock.code}')">

            <div class="pick-rank">#${rank}</div>

            <div class="pick-info">

                <span class="pick-symbol">${stock.code}</span>

                <span class="pick-name">${stock.name}</span>

            </div>

            <div class="pick-price">₹${stock.price.toLocaleString()}</div>

            <div class="pick-change ${changeClass}">${changeSign}${stock.change.toFixed(2)}%</div>

            <div class="pick-score ${scoreClass}">${score}</div>

        </div>

    `;

}



// ============================================

// MARKET MOVERS LOADING

// ============================================

async function loadMarketMovers() {

    console.log("DEBUG: Loading market movers...");

    try {

        const response = await fetch(`${API_BASE}/api/market-movers`);

        const data = await response.json();



        if (data.gainers) {

            renderMovers(data.gainers, 'topGainers', 'up');

        }

        if (data.losers) {

            renderMovers(data.losers, 'topLosers', 'down');

        }

    } catch (error) {

        console.error('Error loading market movers:', error);

    }

}



function renderMovers(movers, containerId, type) {

    const container = document.getElementById(containerId);

    if (!container) return;



    if (!movers || movers.length === 0) {

        container.innerHTML = '<div class="loading-picks">No data</div>';

        return;

    }



    container.innerHTML = movers.map(stock => `

        <div class="mover-row">

            <span class="mover-name">${stock.name}</span>

            <span class="mover-change ${type}">${stock.change_pct >= 0 ? '+' : ''}${stock.change_pct.toFixed(2)}%</span>

        </div>

    `).join('');

}



// ============================================

// REFRESH AND UTILITIES

// ============================================

function refreshStockPicks() {

    console.log("DEBUG: Refreshing stock picks...");

    const btn = document.querySelector('.refresh-btn');

    if (btn) {

        btn.textContent = '⏳ Loading...';

        btn.disabled = true;

    }



    Promise.all([loadShortTermPicks(), loadLongTermPicks(), loadMarketMovers()])

        .finally(() => {

            if (btn) {

                btn.textContent = '🔄 Refresh Picks';

                btn.disabled = false;

            }

        });

}



function updateLastUpdateTime() {

    const el = document.getElementById('lastUpdate');

    if (el) {

        const now = new Date();

        el.textContent = `Updated: ${now.toLocaleTimeString()}`;

    }

}



function showStockDetail(code) {

    console.log(`Show detail for: ${code}`);

    // Could open a modal with detailed stock analysis

    alert(`Stock Detail: ${code}\n\nThis would show detailed analysis, indicators, and chart for the stock.`);

}



// Auto-refresh stock picks every 60 seconds

setInterval(loadStockPicks, 60000);

setInterval(loadMarketMovers, 120000);



