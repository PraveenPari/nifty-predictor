// Charts Module - Strategy Visualization
let priceChartInstance = null;
let strategyChartInstance = null;
let modalChartInstance = null;

const ChartManager = {
    // Color schemes
    colors: {
        green: '#10b981',
        red: '#ef4444',
        blue: '#3b82f6',
        purple: '#8b5cf6',
        orange: '#f59e0b',
        cyan: '#06b6d4',
        gray: '#64748b',
        greenTransparent: 'rgba(16, 185, 129, 0.2)',
        redTransparent: 'rgba(239, 68, 68, 0.2)',
        blueTransparent: 'rgba(59, 130, 246, 0.2)',
        purpleTransparent: 'rgba(139, 92, 246, 0.2)'
    },

    // Default chart options
    getDefaultOptions: function (title = '') {
        return {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#94a3b8',
                        font: { family: 'Inter', size: 11 },
                        usePointStyle: true,
                        padding: 15
                    }
                },
                title: {
                    display: !!title,
                    text: title,
                    color: '#f8fafc',
                    font: { family: 'Inter', size: 14, weight: '600' }
                },
                tooltip: {
                    backgroundColor: 'rgba(26, 31, 46, 0.95)',
                    titleColor: '#f8fafc',
                    bodyColor: '#94a3b8',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true,
                    callbacks: {}
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.05)', drawBorder: false },
                    ticks: { color: '#64748b', font: { size: 10 } }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.05)', drawBorder: false },
                    ticks: { color: '#64748b', font: { size: 10 } }
                }
            }
        };
    },

    // Create Price Chart (TradingView Lightweight Charts)
    createPriceChart: function (containerId, data, title) {
        const container = document.getElementById('tvChartContainer');
        if (!container) return null;

        // Clear previous chart
        container.innerHTML = '';

        const chart = LightweightCharts.createChart(container, {
            width: container.clientWidth,
            height: container.clientHeight,
            layout: {
                background: { type: 'solid', color: '#1a1f2e' },
                textColor: '#94a3b8',
            },
            grid: {
                vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
                horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
            },
            rightPriceScale: {
                borderColor: 'rgba(255, 255, 255, 0.1)',
            },
            timeScale: {
                borderColor: 'rgba(255, 255, 255, 0.1)',
                timeVisible: true,
                secondsVisible: false,
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
        });

        const candlestickSeries = chart.addCandlestickSeries({
            upColor: '#10b981',
            downColor: '#ef4444',
            borderVisible: false,
            wickUpColor: '#10b981',
            wickDownColor: '#ef4444',
        });

        // Format data for Lightweight Charts
        const chartData = data.map(d => ({
            time: d.timestamp, // Unix timestamp in seconds
            open: d.open,
            high: d.high,
            low: d.low,
            close: d.close
        }));

        candlestickSeries.setData(chartData);

        // Responsive resize
        const resizeObserver = new ResizeObserver(entries => {
            if (entries.length === 0 || entries[0].target !== container) { return; }
            const newRect = entries[0].contentRect;
            chart.applyOptions({ width: newRect.width, height: newRect.height });
        });
        resizeObserver.observe(container);

        priceChartInstance = chart; // Store instance if needed
        return chart;
    },

    // Create RSI Chart
    createRSIChart: function (canvasId, rsiData, labels) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (strategyChartInstance) {
            strategyChartInstance.destroy();
        }

        const options = this.getDefaultOptions('RSI (14)');
        options.plugins.annotation = {
            annotations: {
                overbought: {
                    type: 'line',
                    yMin: 70,
                    yMax: 70,
                    borderColor: this.colors.red,
                    borderWidth: 2,
                    borderDash: [5, 5],
                    label: {
                        display: true,
                        content: 'Overbought (70)',
                        position: 'end'
                    }
                },
                oversold: {
                    type: 'line',
                    yMin: 30,
                    yMax: 30,
                    borderColor: this.colors.green,
                    borderWidth: 2,
                    borderDash: [5, 5],
                    label: {
                        display: true,
                        content: 'Oversold (30)',
                        position: 'end'
                    }
                }
            }
        };
        options.scales.y.min = 0;
        options.scales.y.max = 100;

        strategyChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'RSI',
                    data: rsiData,
                    borderColor: this.colors.purple,
                    backgroundColor: this.colors.purpleTransparent,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0
                }]
            },
            options: options
        });

        return strategyChartInstance;
    },

    // Create MACD Chart
    createMACDChart: function (canvasId, macdLine, signalLine, histogram, labels) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (strategyChartInstance) {
            strategyChartInstance.destroy();
        }

        const options = this.getDefaultOptions('MACD (12, 26, 9)');

        strategyChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Histogram',
                        data: histogram,
                        backgroundColor: histogram.map(h => h >= 0 ? this.colors.greenTransparent : this.colors.redTransparent),
                        borderColor: histogram.map(h => h >= 0 ? this.colors.green : this.colors.red),
                        borderWidth: 1,
                        type: 'bar',
                        order: 2
                    },
                    {
                        label: 'MACD Line',
                        data: macdLine,
                        borderColor: this.colors.blue,
                        borderWidth: 2,
                        fill: false,
                        tension: 0.4,
                        pointRadius: 0,
                        type: 'line',
                        order: 1
                    },
                    {
                        label: 'Signal Line',
                        data: signalLine,
                        borderColor: this.colors.orange,
                        borderWidth: 2,
                        fill: false,
                        tension: 0.4,
                        pointRadius: 0,
                        type: 'line',
                        order: 1
                    }
                ]
            },
            options: options
        });

        return strategyChartInstance;
    },

    // Create Bollinger Bands Chart
    createBollingerChart: function (canvasId, prices, upper, middle, lower, labels) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (strategyChartInstance) {
            strategyChartInstance.destroy();
        }

        const options = this.getDefaultOptions('Bollinger Bands (20, 2)');

        strategyChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Upper Band',
                        data: upper,
                        borderColor: this.colors.red,
                        borderWidth: 1,
                        fill: false,
                        pointRadius: 0,
                        borderDash: [5, 5]
                    },
                    {
                        label: 'Price',
                        data: prices,
                        borderColor: this.colors.cyan,
                        backgroundColor: this.colors.blueTransparent,
                        borderWidth: 2,
                        fill: false,
                        pointRadius: 0
                    },
                    {
                        label: 'Middle Band (SMA 20)',
                        data: middle,
                        borderColor: this.colors.orange,
                        borderWidth: 1,
                        fill: false,
                        pointRadius: 0
                    },
                    {
                        label: 'Lower Band',
                        data: lower,
                        borderColor: this.colors.green,
                        borderWidth: 1,
                        fill: '-1',
                        backgroundColor: 'rgba(100, 116, 139, 0.1)',
                        pointRadius: 0,
                        borderDash: [5, 5]
                    }
                ]
            },
            options: options
        });

        return strategyChartInstance;
    },

    // Create Moving Averages Chart
    createMAChart: function (canvasId, prices, sma20, sma50, ema9, labels) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (strategyChartInstance) {
            strategyChartInstance.destroy();
        }

        const options = this.getDefaultOptions('Moving Averages');

        strategyChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Price',
                        data: prices,
                        borderColor: this.colors.cyan,
                        borderWidth: 2,
                        fill: false,
                        pointRadius: 0
                    },
                    {
                        label: 'EMA 9',
                        data: ema9,
                        borderColor: this.colors.purple,
                        borderWidth: 1.5,
                        fill: false,
                        pointRadius: 0
                    },
                    {
                        label: 'SMA 20',
                        data: sma20,
                        borderColor: this.colors.orange,
                        borderWidth: 1.5,
                        fill: false,
                        pointRadius: 0
                    },
                    {
                        label: 'SMA 50',
                        data: sma50,
                        borderColor: this.colors.green,
                        borderWidth: 1.5,
                        fill: false,
                        pointRadius: 0
                    }
                ]
            },
            options: options
        });

        return strategyChartInstance;
    },

    // Create Stochastic Chart
    createStochasticChart: function (canvasId, kLine, dLine, labels) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (strategyChartInstance) {
            strategyChartInstance.destroy();
        }

        const options = this.getDefaultOptions('Stochastic Oscillator (14, 3)');
        options.scales.y.min = 0;
        options.scales.y.max = 100;

        strategyChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '%K',
                        data: kLine,
                        borderColor: this.colors.blue,
                        borderWidth: 2,
                        fill: false,
                        pointRadius: 0
                    },
                    {
                        label: '%D',
                        data: dLine,
                        borderColor: this.colors.orange,
                        borderWidth: 2,
                        fill: false,
                        pointRadius: 0,
                        borderDash: [5, 5]
                    }
                ]
            },
            options: options
        });

        return strategyChartInstance;
    },

    // Create SuperTrend Chart
    createSuperTrendChart: function (canvasId, prices, superTrendLine, trend, labels) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (strategyChartInstance) {
            strategyChartInstance.destroy();
        }

        const options = this.getDefaultOptions('SuperTrend (10, 3)');

        strategyChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Price',
                        data: prices,
                        borderColor: this.colors.cyan,
                        borderWidth: 2,
                        fill: false,
                        pointRadius: 0
                    },
                    {
                        label: 'SuperTrend',
                        data: superTrendLine,
                        borderColor: trend === 'bullish' ? this.colors.green : this.colors.red,
                        backgroundColor: trend === 'bullish' ? this.colors.greenTransparent : this.colors.redTransparent,
                        borderWidth: 2,
                        fill: true,
                        pointRadius: 0
                    }
                ]
            },
            options: options
        });

        return strategyChartInstance;
    },

    // Create ADX Chart
    createADXChart: function (canvasId, adxLine, plusDI, minusDI, labels) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (strategyChartInstance) {
            strategyChartInstance.destroy();
        }

        const options = this.getDefaultOptions('ADX - Average Directional Index (14)');

        strategyChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'ADX',
                        data: adxLine,
                        borderColor: this.colors.purple,
                        borderWidth: 2,
                        fill: false,
                        pointRadius: 0
                    },
                    {
                        label: '+DI',
                        data: plusDI,
                        borderColor: this.colors.green,
                        borderWidth: 1.5,
                        fill: false,
                        pointRadius: 0
                    },
                    {
                        label: '-DI',
                        data: minusDI,
                        borderColor: this.colors.red,
                        borderWidth: 1.5,
                        fill: false,
                        pointRadius: 0
                    }
                ]
            },
            options: options
        });

        return strategyChartInstance;
    },

    // Create VWAP Chart
    createVWAPChart: function (canvasId, prices, vwapLine, labels) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (strategyChartInstance) {
            strategyChartInstance.destroy();
        }

        const options = this.getDefaultOptions('VWAP - Volume Weighted Average Price');

        strategyChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Price',
                        data: prices,
                        borderColor: this.colors.cyan,
                        borderWidth: 2,
                        fill: false,
                        pointRadius: 0
                    },
                    {
                        label: 'VWAP',
                        data: vwapLine,
                        borderColor: this.colors.orange,
                        backgroundColor: this.colors.purpleTransparent,
                        borderWidth: 2,
                        fill: true,
                        pointRadius: 0
                    }
                ]
            },
            options: options
        });

        return strategyChartInstance;
    },

    // Create Future Prediction Chart
    createPredictionChart: function (canvasId, historicalPrices, projectedPrices, labels) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (strategyChartInstance) {
            strategyChartInstance.destroy();
        }

        const options = this.getDefaultOptions('🔮 30 Min Future Projection');

        // Split data into historical and projection
        const histData = [...historicalPrices];
        const projData = Array(historicalPrices.length - 1).fill(null).concat([historicalPrices[historicalPrices.length - 1], ...projectedPrices]);

        // Extend labels for future
        const lastLabel = labels[labels.length - 1];
        const nextLabels = [];
        for (let i = 1; i <= 6; i++) { // 30 mins = 6 segments of 5 mins
            nextLabels.push('+' + (i * 5) + 'm');
        }
        const allLabels = [...labels, ...nextLabels];

        strategyChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: allLabels,
                datasets: [
                    {
                        label: 'Historical Price',
                        data: histData,
                        borderColor: this.colors.cyan,
                        borderWidth: 2,
                        fill: false,
                        pointRadius: 0
                    },
                    {
                        label: 'Future Projection',
                        data: projData,
                        borderColor: this.colors.orange,
                        borderWidth: 3,
                        borderDash: [5, 5],
                        fill: true,
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        pointRadius: 0,
                        tension: 0.4
                    }
                ]
            },
            options: options
        });

        return strategyChartInstance;
    },

    // Destroy all charts
    destroyAll: function () {
        if (priceChartInstance) priceChartInstance.destroy();
        if (strategyChartInstance) strategyChartInstance.destroy();
        if (modalChartInstance) modalChartInstance.destroy();
    }
};

window.ChartManager = ChartManager;
