// Trading Strategies Module
const TradingStrategies = {
    // 1. RSI Overbought/Oversold Strategy
    rsiStrategy: function (rsi) {
        if (rsi === null) return { signal: 'neutral', strength: 50 };
        if (rsi < 30) return { signal: 'bullish', strength: 85, reason: 'RSI Oversold - Buy Signal' };
        if (rsi > 70) return { signal: 'bearish', strength: 85, reason: 'RSI Overbought - Sell Signal' };
        if (rsi < 40) return { signal: 'bullish', strength: 60, reason: 'RSI approaching oversold' };
        if (rsi > 60) return { signal: 'bearish', strength: 60, reason: 'RSI approaching overbought' };
        return { signal: 'neutral', strength: 50, reason: 'RSI in neutral zone' };
    },

    // 2. MACD Crossover Strategy
    macdStrategy: function (macd) {
        if (!macd) return { signal: 'neutral', strength: 50 };
        if (macd.histogram > 0 && macd.macd > 0) {
            return { signal: 'bullish', strength: 75, reason: 'MACD above signal line, positive histogram' };
        }
        if (macd.histogram < 0 && macd.macd < 0) {
            return { signal: 'bearish', strength: 75, reason: 'MACD below signal line, negative histogram' };
        }
        return { signal: 'neutral', strength: 50, reason: 'MACD showing mixed signals' };
    },

    // 3. Moving Average Crossover Strategy
    maCrossoverStrategy: function (shortMA, longMA, price) {
        if (!shortMA || !longMA) return { signal: 'neutral', strength: 50 };
        const diff = ((shortMA - longMA) / longMA) * 100;
        if (shortMA > longMA && price > shortMA) {
            return { signal: 'bullish', strength: 80, reason: 'Golden Cross - Short MA above Long MA' };
        }
        if (shortMA < longMA && price < shortMA) {
            return { signal: 'bearish', strength: 80, reason: 'Death Cross - Short MA below Long MA' };
        }
        return { signal: 'neutral', strength: 50, reason: 'MAs showing consolidation' };
    },

    // 4. Bollinger Bands Strategy
    bollingerStrategy: function (bb, price) {
        if (!bb) return { signal: 'neutral', strength: 50 };
        const bandWidth = (bb.upper - bb.lower) / bb.middle * 100;
        if (price <= bb.lower) {
            return { signal: 'bullish', strength: 80, reason: 'Price at lower Bollinger Band - oversold' };
        }
        if (price >= bb.upper) {
            return { signal: 'bearish', strength: 80, reason: 'Price at upper Bollinger Band - overbought' };
        }
        if (price > bb.middle) {
            return { signal: 'bullish', strength: 55, reason: 'Price above middle band' };
        }
        return { signal: 'bearish', strength: 55, reason: 'Price below middle band' };
    },

    // 5. Stochastic Strategy
    stochasticStrategy: function (stoch) {
        if (!stoch) return { signal: 'neutral', strength: 50 };
        if (stoch.k < 20 && stoch.d < 20) {
            return { signal: 'bullish', strength: 80, reason: 'Stochastic in oversold zone' };
        }
        if (stoch.k > 80 && stoch.d > 80) {
            return { signal: 'bearish', strength: 80, reason: 'Stochastic in overbought zone' };
        }
        if (stoch.k > stoch.d) {
            return { signal: 'bullish', strength: 60, reason: 'Stochastic K above D' };
        }
        return { signal: 'bearish', strength: 60, reason: 'Stochastic K below D' };
    },

    // 6. ADX Trend Strength Strategy
    adxStrategy: function (adx) {
        if (!adx) return { signal: 'neutral', strength: 50 };
        if (adx.adx > 25) {
            if (adx.plusDI > adx.minusDI) {
                return { signal: 'bullish', strength: 75, reason: 'Strong uptrend (ADX > 25, +DI > -DI)' };
            }
            return { signal: 'bearish', strength: 75, reason: 'Strong downtrend (ADX > 25, -DI > +DI)' };
        }
        return { signal: 'neutral', strength: 50, reason: 'Weak trend (ADX < 25)' };
    },

    // 7. SuperTrend Strategy
    superTrendStrategy: function (superTrend, price) {
        if (!superTrend) return { signal: 'neutral', strength: 50 };
        if (superTrend.trend === 'bullish') {
            return { signal: 'bullish', strength: 85, reason: 'SuperTrend indicates uptrend' };
        }
        return { signal: 'bearish', strength: 85, reason: 'SuperTrend indicates downtrend' };
    },

    // 8. VWAP Strategy
    vwapStrategy: function (vwap, price) {
        if (!vwap) return { signal: 'neutral', strength: 50 };
        const diff = ((price - vwap) / vwap) * 100;
        if (price > vwap) {
            return { signal: 'bullish', strength: 70, reason: `Price ${diff.toFixed(2)}% above VWAP` };
        }
        return { signal: 'bearish', strength: 70, reason: `Price ${Math.abs(diff).toFixed(2)}% below VWAP` };
    },

    // 9. Ichimoku Cloud Strategy
    ichimokuStrategy: function (ichimoku) {
        if (!ichimoku) return { signal: 'neutral', strength: 50 };
        const { tenkan, kijun, senkouA, currentPrice } = ichimoku;
        if (currentPrice > senkouA && tenkan > kijun) {
            return { signal: 'bullish', strength: 80, reason: 'Price above cloud, Tenkan above Kijun' };
        }
        if (currentPrice < senkouA && tenkan < kijun) {
            return { signal: 'bearish', strength: 80, reason: 'Price below cloud, Tenkan below Kijun' };
        }
        return { signal: 'neutral', strength: 50, reason: 'Ichimoku showing mixed signals' };
    },

    // 10. Parabolic SAR Strategy
    psarStrategy: function (psar) {
        if (!psar) return { signal: 'neutral', strength: 50 };
        if (psar.trend === 'bullish') {
            return { signal: 'bullish', strength: 75, reason: 'Parabolic SAR below price - Uptrend' };
        }
        return { signal: 'bearish', strength: 75, reason: 'Parabolic SAR above price - Downtrend' };
    },

    // 11. CCI Strategy
    cciStrategy: function (cci) {
        if (cci === null) return { signal: 'neutral', strength: 50 };
        if (cci < -100) return { signal: 'bullish', strength: 80, reason: 'CCI extremely oversold' };
        if (cci > 100) return { signal: 'bearish', strength: 80, reason: 'CCI extremely overbought' };
        if (cci < -50) return { signal: 'bullish', strength: 60, reason: 'CCI oversold' };
        if (cci > 50) return { signal: 'bearish', strength: 60, reason: 'CCI overbought' };
        return { signal: 'neutral', strength: 50, reason: 'CCI in neutral zone' };
    },

    // 12. Williams %R Strategy
    williamsRStrategy: function (wr) {
        if (wr === null) return { signal: 'neutral', strength: 50 };
        if (wr < -80) return { signal: 'bullish', strength: 80, reason: 'Williams %R oversold' };
        if (wr > -20) return { signal: 'bearish', strength: 80, reason: 'Williams %R overbought' };
        return { signal: 'neutral', strength: 50, reason: 'Williams %R in neutral zone' };
    },

    // 13. MFI Strategy
    mfiStrategy: function (mfi) {
        if (mfi === null) return { signal: 'neutral', strength: 50 };
        if (mfi < 20) return { signal: 'bullish', strength: 80, reason: 'MFI oversold - accumulation zone' };
        if (mfi > 80) return { signal: 'bearish', strength: 80, reason: 'MFI overbought - distribution zone' };
        if (mfi > 50) return { signal: 'bullish', strength: 55, reason: 'MFI above 50' };
        return { signal: 'bearish', strength: 55, reason: 'MFI below 50' };
    },

    // 14. Pivot Point Strategy
    pivotStrategy: function (pivots, price) {
        if (!pivots) return { signal: 'neutral', strength: 50 };
        if (price > pivots.r1) return { signal: 'bullish', strength: 75, reason: 'Price above R1 - strong bullish' };
        if (price < pivots.s1) return { signal: 'bearish', strength: 75, reason: 'Price below S1 - strong bearish' };
        if (price > pivots.pivot) return { signal: 'bullish', strength: 60, reason: 'Price above pivot' };
        return { signal: 'bearish', strength: 60, reason: 'Price below pivot' };
    },

    // 15. OI Analysis Strategy
    openInterestStrategy: function (ceOI, peOI, ceOIChange, peOIChange) {
        const ratio = peOI / ceOI;
        if (ratio > 1.2 && peOIChange > 0) {
            return { signal: 'bullish', strength: 75, reason: 'PE OI higher and increasing - support building' };
        }
        if (ratio < 0.8 && ceOIChange > 0) {
            return { signal: 'bearish', strength: 75, reason: 'CE OI higher and increasing - resistance building' };
        }
        return { signal: 'neutral', strength: 50, reason: 'OI showing balanced activity' };
    },

    // 16. PCR Strategy
    pcrStrategy: function (pcr) {
        if (pcr < 0.7) return { signal: 'bearish', strength: 70, reason: 'Low PCR - extreme bullishness (contrarian bearish)' };
        if (pcr > 1.3) return { signal: 'bullish', strength: 70, reason: 'High PCR - extreme bearishness (contrarian bullish)' };
        if (pcr < 0.9) return { signal: 'bullish', strength: 60, reason: 'PCR in bullish zone' };
        if (pcr > 1.1) return { signal: 'bearish', strength: 60, reason: 'PCR in bearish zone' };
        return { signal: 'neutral', strength: 50, reason: 'PCR in neutral zone' };
    },

    // 17. VIX Strategy
    vixStrategy: function (vix, vixChange) {
        if (vix < 12 && vixChange < 0) {
            return { signal: 'bullish', strength: 70, reason: 'Low VIX and falling - complacency, bullish' };
        }
        if (vix > 20) {
            return { signal: 'bullish', strength: 65, reason: 'High VIX - fear extreme, contrarian bullish' };
        }
        if (vix > 15 && vixChange > 0) {
            return { signal: 'bearish', strength: 65, reason: 'Rising VIX - increasing fear' };
        }
        return { signal: 'neutral', strength: 50, reason: 'VIX in normal range' };
    },

    // 18. FII/DII Strategy
    fiiDiiStrategy: function (fiiNet, diiNet) {
        const totalFlow = fiiNet + diiNet;
        if (fiiNet > 1000 && diiNet > 0) {
            return { signal: 'bullish', strength: 80, reason: 'Strong FII buying with DII support' };
        }
        if (fiiNet < -1000 && diiNet < 0) {
            return { signal: 'bearish', strength: 80, reason: 'Strong FII selling with DII selling' };
        }
        if (totalFlow > 1500) {
            return { signal: 'bullish', strength: 70, reason: 'Net institutional buying' };
        }
        if (totalFlow < -1500) {
            return { signal: 'bearish', strength: 70, reason: 'Net institutional selling' };
        }
        return { signal: 'neutral', strength: 50, reason: 'Mixed institutional activity' };
    },

    // Combined Strategy Analysis
    analyzeAllStrategies: function (marketData) {
        const strategies = [];
        const { prices, highs, lows, closes, volumes, indicators, sentiment } = marketData;

        // Technical Indicator Strategies
        strategies.push({ name: 'RSI Analysis', ...this.rsiStrategy(indicators.rsi) });
        strategies.push({ name: 'MACD Crossover', ...this.macdStrategy(indicators.macd) });
        strategies.push({ name: 'MA Crossover', ...this.maCrossoverStrategy(indicators.ema20, indicators.ema50, prices[prices.length - 1]) });
        strategies.push({ name: 'Bollinger Bands', ...this.bollingerStrategy(indicators.bb, prices[prices.length - 1]) });
        strategies.push({ name: 'Stochastic', ...this.stochasticStrategy(indicators.stochastic) });
        strategies.push({ name: 'ADX Trend', ...this.adxStrategy(indicators.adx) });
        strategies.push({ name: 'SuperTrend', ...this.superTrendStrategy(indicators.superTrend, prices[prices.length - 1]) });
        strategies.push({ name: 'VWAP', ...this.vwapStrategy(indicators.vwap, prices[prices.length - 1]) });
        strategies.push({ name: 'Ichimoku Cloud', ...this.ichimokuStrategy(indicators.ichimoku) });
        strategies.push({ name: 'Parabolic SAR', ...this.psarStrategy(indicators.psar) });
        strategies.push({ name: 'CCI Analysis', ...this.cciStrategy(indicators.cci) });
        strategies.push({ name: 'Williams %R', ...this.williamsRStrategy(indicators.williamsR) });

        // Sentiment Strategies
        if (sentiment) {
            strategies.push({ name: 'Open Interest', ...this.openInterestStrategy(sentiment.ceOI, sentiment.peOI, sentiment.ceOIChange, sentiment.peOIChange) });
            strategies.push({ name: 'PCR Analysis', ...this.pcrStrategy(sentiment.pcr) });
            strategies.push({ name: 'VIX Analysis', ...this.vixStrategy(sentiment.vix, sentiment.vixChange) });
            strategies.push({ name: 'FII/DII Flow', ...this.fiiDiiStrategy(sentiment.fiiNet, sentiment.diiNet) });
        }

        return strategies;
    },

    // Calculate Overall Prediction
    calculatePrediction: function (strategies) {
        let bullishScore = 0, bearishScore = 0, totalWeight = 0;

        strategies.forEach(s => {
            const weight = s.strength / 100;
            totalWeight += weight;
            if (s.signal === 'bullish') bullishScore += weight;
            else if (s.signal === 'bearish') bearishScore += weight;
        });

        const bullishPct = (bullishScore / totalWeight) * 100;
        const bearishPct = (bearishScore / totalWeight) * 100;

        return {
            ceProb: Math.round(bullishPct),
            peProb: Math.round(bearishPct),
            direction: bullishPct > bearishPct ? 'BULLISH' : bearishPct > bullishPct ? 'BEARISH' : 'NEUTRAL',
            confidence: Math.abs(bullishPct - bearishPct)
        };
    }
};

window.TradingStrategies = TradingStrategies;
