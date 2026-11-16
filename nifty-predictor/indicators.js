// Technical Indicators Module
const TechnicalIndicators = {
    // Simple Moving Average
    SMA: function(prices, period) {
        if (prices.length < period) return null;
        const slice = prices.slice(-period);
        return slice.reduce((a, b) => a + b, 0) / period;
    },

    // Exponential Moving Average
    EMA: function(prices, period) {
        if (prices.length < period) return null;
        const multiplier = 2 / (period + 1);
        let ema = prices.slice(0, period).reduce((a, b) => a + b, 0) / period;
        for (let i = period; i < prices.length; i++) {
            ema = (prices[i] - ema) * multiplier + ema;
        }
        return ema;
    },

    // Relative Strength Index
    RSI: function(prices, period = 14) {
        if (prices.length < period + 1) return null;
        let gains = 0, losses = 0;
        for (let i = 1; i <= period; i++) {
            const change = prices[i] - prices[i - 1];
            if (change >= 0) gains += change;
            else losses -= change;
        }
        let avgGain = gains / period;
        let avgLoss = losses / period;
        for (let i = period + 1; i < prices.length; i++) {
            const change = prices[i] - prices[i - 1];
            if (change >= 0) {
                avgGain = (avgGain * (period - 1) + change) / period;
                avgLoss = (avgLoss * (period - 1)) / period;
            } else {
                avgGain = (avgGain * (period - 1)) / period;
                avgLoss = (avgLoss * (period - 1) - change) / period;
            }
        }
        if (avgLoss === 0) return 100;
        const rs = avgGain / avgLoss;
        return 100 - (100 / (1 + rs));
    },

    // MACD
    MACD: function(prices, fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) {
        const fastEMA = this.EMA(prices, fastPeriod);
        const slowEMA = this.EMA(prices, slowPeriod);
        if (!fastEMA || !slowEMA) return null;
        const macdLine = fastEMA - slowEMA;
        return { macd: macdLine, signal: macdLine * 0.9, histogram: macdLine * 0.1 };
    },

    // Bollinger Bands
    BollingerBands: function(prices, period = 20, stdDev = 2) {
        const sma = this.SMA(prices, period);
        if (!sma) return null;
        const slice = prices.slice(-period);
        const variance = slice.reduce((acc, val) => acc + Math.pow(val - sma, 2), 0) / period;
        const std = Math.sqrt(variance);
        return {
            upper: sma + (std * stdDev),
            middle: sma,
            lower: sma - (std * stdDev)
        };
    },

    // Stochastic Oscillator
    Stochastic: function(highs, lows, closes, kPeriod = 14, dPeriod = 3) {
        if (closes.length < kPeriod) return null;
        const highestHigh = Math.max(...highs.slice(-kPeriod));
        const lowestLow = Math.min(...lows.slice(-kPeriod));
        const currentClose = closes[closes.length - 1];
        const k = ((currentClose - lowestLow) / (highestHigh - lowestLow)) * 100;
        return { k, d: k * 0.9 };
    },

    // Average Directional Index
    ADX: function(highs, lows, closes, period = 14) {
        if (closes.length < period) return null;
        // Simplified ADX calculation
        let plusDM = 0, minusDM = 0, tr = 0;
        for (let i = 1; i < period; i++) {
            const highDiff = highs[i] - highs[i-1];
            const lowDiff = lows[i-1] - lows[i];
            plusDM += highDiff > lowDiff && highDiff > 0 ? highDiff : 0;
            minusDM += lowDiff > highDiff && lowDiff > 0 ? lowDiff : 0;
            tr += Math.max(highs[i] - lows[i], Math.abs(highs[i] - closes[i-1]), Math.abs(lows[i] - closes[i-1]));
        }
        const plusDI = (plusDM / tr) * 100;
        const minusDI = (minusDM / tr) * 100;
        const dx = Math.abs(plusDI - minusDI) / (plusDI + minusDI) * 100;
        return { adx: dx, plusDI, minusDI };
    },

    // Commodity Channel Index
    CCI: function(highs, lows, closes, period = 20) {
        if (closes.length < period) return null;
        const typicalPrices = closes.map((c, i) => (highs[i] + lows[i] + c) / 3);
        const sma = this.SMA(typicalPrices, period);
        const meanDeviation = typicalPrices.slice(-period).reduce((acc, tp) => acc + Math.abs(tp - sma), 0) / period;
        return (typicalPrices[typicalPrices.length - 1] - sma) / (0.015 * meanDeviation);
    },

    // Williams %R
    WilliamsR: function(highs, lows, closes, period = 14) {
        if (closes.length < period) return null;
        const highestHigh = Math.max(...highs.slice(-period));
        const lowestLow = Math.min(...lows.slice(-period));
        return ((highestHigh - closes[closes.length - 1]) / (highestHigh - lowestLow)) * -100;
    },

    // Average True Range
    ATR: function(highs, lows, closes, period = 14) {
        if (closes.length < period) return null;
        let atr = 0;
        for (let i = 1; i < period; i++) {
            const tr = Math.max(
                highs[i] - lows[i],
                Math.abs(highs[i] - closes[i-1]),
                Math.abs(lows[i] - closes[i-1])
            );
            atr += tr;
        }
        return atr / period;
    },

    // Pivot Points
    PivotPoints: function(high, low, close) {
        const pivot = (high + low + close) / 3;
        return {
            pivot,
            r1: (2 * pivot) - low,
            r2: pivot + (high - low),
            r3: high + 2 * (pivot - low),
            s1: (2 * pivot) - high,
            s2: pivot - (high - low),
            s3: low - 2 * (high - pivot)
        };
    },

    // VWAP (simplified)
    VWAP: function(highs, lows, closes, volumes) {
        let totalVP = 0, totalVol = 0;
        for (let i = 0; i < closes.length; i++) {
            const typicalPrice = (highs[i] + lows[i] + closes[i]) / 3;
            totalVP += typicalPrice * volumes[i];
            totalVol += volumes[i];
        }
        return totalVP / totalVol;
    },

    // SuperTrend
    SuperTrend: function(highs, lows, closes, period = 10, multiplier = 3) {
        const atr = this.ATR(highs, lows, closes, period);
        if (!atr) return null;
        const hl2 = (highs[highs.length-1] + lows[lows.length-1]) / 2;
        const upperBand = hl2 + (multiplier * atr);
        const lowerBand = hl2 - (multiplier * atr);
        const trend = closes[closes.length-1] > lowerBand ? 'bullish' : 'bearish';
        return { upperBand, lowerBand, trend };
    },

    // Ichimoku Cloud
    IchimokuCloud: function(highs, lows, closes) {
        const conversionPeriod = 9, basePeriod = 26;
        if (closes.length < basePeriod) return null;
        const conversionHigh = Math.max(...highs.slice(-conversionPeriod));
        const conversionLow = Math.min(...lows.slice(-conversionPeriod));
        const tenkan = (conversionHigh + conversionLow) / 2;
        const baseHigh = Math.max(...highs.slice(-basePeriod));
        const baseLow = Math.min(...lows.slice(-basePeriod));
        const kijun = (baseHigh + baseLow) / 2;
        const senkouA = (tenkan + kijun) / 2;
        return { tenkan, kijun, senkouA, currentPrice: closes[closes.length-1] };
    },

    // Parabolic SAR
    ParabolicSAR: function(highs, lows, closes, af = 0.02, maxAf = 0.2) {
        if (closes.length < 5) return null;
        const currentPrice = closes[closes.length - 1];
        const prevHigh = Math.max(...highs.slice(-5));
        const prevLow = Math.min(...lows.slice(-5));
        // Simplified SAR
        const sar = currentPrice > (prevHigh + prevLow) / 2 ? prevLow * 0.98 : prevHigh * 1.02;
        const trend = currentPrice > sar ? 'bullish' : 'bearish';
        return { sar, trend };
    },

    // Money Flow Index
    MFI: function(highs, lows, closes, volumes, period = 14) {
        if (closes.length < period) return null;
        let positiveFlow = 0, negativeFlow = 0;
        for (let i = 1; i < period; i++) {
            const typicalPrice = (highs[i] + lows[i] + closes[i]) / 3;
            const prevTypicalPrice = (highs[i-1] + lows[i-1] + closes[i-1]) / 3;
            const rawMoneyFlow = typicalPrice * volumes[i];
            if (typicalPrice > prevTypicalPrice) positiveFlow += rawMoneyFlow;
            else negativeFlow += rawMoneyFlow;
        }
        const ratio = positiveFlow / negativeFlow;
        return 100 - (100 / (1 + ratio));
    },

    // On-Balance Volume
    OBV: function(closes, volumes) {
        let obv = 0;
        for (let i = 1; i < closes.length; i++) {
            if (closes[i] > closes[i-1]) obv += volumes[i];
            else if (closes[i] < closes[i-1]) obv -= volumes[i];
        }
        return obv;
    }
};

// Candlestick Pattern Detection
const CandlestickPatterns = {
    // Detect Doji
    isDoji: function(open, high, low, close) {
        const body = Math.abs(close - open);
        const range = high - low;
        return body < range * 0.1;
    },

    // Detect Hammer
    isHammer: function(open, high, low, close) {
        const body = Math.abs(close - open);
        const lowerWick = Math.min(open, close) - low;
        const upperWick = high - Math.max(open, close);
        return lowerWick > body * 2 && upperWick < body * 0.5;
    },

    // Detect Shooting Star
    isShootingStar: function(open, high, low, close) {
        const body = Math.abs(close - open);
        const upperWick = high - Math.max(open, close);
        const lowerWick = Math.min(open, close) - low;
        return upperWick > body * 2 && lowerWick < body * 0.5;
    },

    // Detect Engulfing Pattern
    isEngulfing: function(prevOpen, prevClose, open, close) {
        const prevBody = Math.abs(prevClose - prevOpen);
        const currentBody = Math.abs(close - open);
        const isBullish = prevClose < prevOpen && close > open && open < prevClose && close > prevOpen;
        const isBearish = prevClose > prevOpen && close < open && open > prevClose && close < prevOpen;
        return { bullish: isBullish, bearish: isBearish };
    },

    // Detect Morning Star
    isMorningStar: function(candles) {
        if (candles.length < 3) return false;
        const [first, second, third] = candles.slice(-3);
        return first.close < first.open && 
               Math.abs(second.close - second.open) < (first.open - first.close) * 0.3 &&
               third.close > third.open;
    },

    // Detect Evening Star
    isEveningStar: function(candles) {
        if (candles.length < 3) return false;
        const [first, second, third] = candles.slice(-3);
        return first.close > first.open && 
               Math.abs(second.close - second.open) < (first.close - first.open) * 0.3 &&
               third.close < third.open;
    },

    // Detect Three White Soldiers
    isThreeWhiteSoldiers: function(candles) {
        if (candles.length < 3) return false;
        const [first, second, third] = candles.slice(-3);
        return first.close > first.open && 
               second.close > second.open && 
               third.close > third.open &&
               second.open > first.open &&
               third.open > second.open;
    },

    // Detect Three Black Crows
    isThreeBlackCrows: function(candles) {
        if (candles.length < 3) return false;
        const [first, second, third] = candles.slice(-3);
        return first.close < first.open && 
               second.close < second.open && 
               third.close < third.open &&
               second.open < first.open &&
               third.open < second.open;
    },

    // Detect Harami
    isHarami: function(prevOpen, prevClose, open, close) {
        const isBullish = prevClose < prevOpen && close > open && 
                         open > prevClose && close < prevOpen;
        const isBearish = prevClose > prevOpen && close < open && 
                         open < prevClose && close > prevOpen;
        return { bullish: isBullish, bearish: isBearish };
    },

    // Detect Piercing Pattern
    isPiercingPattern: function(prevOpen, prevClose, open, close) {
        const midpoint = (prevOpen + prevClose) / 2;
        return prevClose < prevOpen && close > open && 
               open < prevClose && close > midpoint && close < prevOpen;
    },

    // Detect Dark Cloud Cover
    isDarkCloudCover: function(prevOpen, prevClose, open, close) {
        const midpoint = (prevOpen + prevClose) / 2;
        return prevClose > prevOpen && close < open && 
               open > prevClose && close < midpoint && close > prevOpen;
    }
};

// Export modules
window.TechnicalIndicators = TechnicalIndicators;
window.CandlestickPatterns = CandlestickPatterns;
