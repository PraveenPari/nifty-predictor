"""
Stock Analyzer Module
Analyzes NIFTY50 stocks and provides recommendations for short-term and long-term trading
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from stock_universe import NIFTY50_STOCKS, get_all_symbols


class StockAnalyzer:
    """Analyzes stocks and generates trading recommendations"""
    
    def __init__(self):
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 60  # 60 seconds cache
        
    def _is_cache_valid(self, key: str) -> bool:
        if key not in self.cache_time:
            return False
        return (time.time() - self.cache_time[key]) < self.cache_duration
    
    def fetch_stock_data(self, symbol: str, period: str = '5d', interval: str = '5m') -> Optional[pd.DataFrame]:
        """Fetch historical data for a single stock"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            if df.empty:
                return None
            return df
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return None
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
    
    def calculate_macd(self, prices: pd.Series) -> Dict:
        """Calculate MACD"""
        if len(prices) < 26:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
        
        ema12 = prices.ewm(span=12, adjust=False).mean()
        ema26 = prices.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        
        return {
            'macd': float(macd.iloc[-1]),
            'signal': float(signal.iloc[-1]),
            'histogram': float(histogram.iloc[-1])
        }
    
    def calculate_volume_surge(self, volumes: pd.Series) -> float:
        """Calculate volume surge ratio"""
        if len(volumes) < 20:
            return 1.0
        avg_volume = volumes.iloc[-20:-1].mean()
        current_volume = volumes.iloc[-1]
        return float(current_volume / avg_volume) if avg_volume > 0 else 1.0
    
    def calculate_momentum(self, prices: pd.Series, period: int = 10) -> float:
        """Calculate price momentum percentage"""
        if len(prices) < period:
            return 0.0
        return float((prices.iloc[-1] - prices.iloc[-period]) / prices.iloc[-period] * 100)
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(close) < period + 1:
            return 0.0
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0.0
    
    def analyze_stock(self, code: str, stock_info: Dict) -> Optional[Dict]:
        """Analyze a single stock and return scores"""
        try:
            symbol = stock_info['symbol']
            df = self.fetch_stock_data(symbol, period='5d', interval='15m')
            
            if df is None or len(df) < 30:
                return None
            
            close = df['Close']
            high = df['High']
            low = df['Low']
            volume = df['Volume']
            
            # Current price and change
            current_price = float(close.iloc[-1])
            prev_close = float(close.iloc[-2]) if len(close) > 1 else current_price
            price_change = ((current_price - prev_close) / prev_close) * 100
            
            # Technical indicators
            rsi = self.calculate_rsi(close)
            macd = self.calculate_macd(close)
            volume_surge = self.calculate_volume_surge(volume)
            momentum_5 = self.calculate_momentum(close, 5)
            momentum_10 = self.calculate_momentum(close, 10)
            atr = self.calculate_atr(high, low, close)
            atr_pct = (atr / current_price) * 100 if current_price > 0 else 0
            
            # Short-term score (0-100) - for 15-min trades
            short_term_score = 50
            
            # RSI signals
            if rsi < 30:
                short_term_score += 20  # Oversold - bullish
            elif rsi > 70:
                short_term_score -= 15  # Overbought - bearish
            elif 30 <= rsi <= 45:
                short_term_score += 10
            
            # MACD signals
            if macd['histogram'] > 0 and macd['histogram'] > macd['signal'] * 0.1:
                short_term_score += 15
            elif macd['histogram'] < 0:
                short_term_score -= 10
            
            # Volume surge
            if volume_surge > 1.5:
                short_term_score += 15
            elif volume_surge > 1.2:
                short_term_score += 8
            
            # Momentum
            if momentum_5 > 0.5:
                short_term_score += 10
            elif momentum_5 < -0.5:
                short_term_score -= 10
            
            # Volatility bonus (higher ATR = more opportunity)
            if atr_pct > 1.0:
                short_term_score += 5
            
            # Clamp score
            short_term_score = max(0, min(100, short_term_score))
            
            # Long-term score (0-100) - for investment
            long_term_score = 50
            
            # Trend analysis
            if momentum_10 > 2:
                long_term_score += 20
            elif momentum_10 > 0:
                long_term_score += 10
            elif momentum_10 < -2:
                long_term_score -= 15
            
            # RSI not overbought for long-term
            if rsi < 60:
                long_term_score += 10
            elif rsi > 75:
                long_term_score -= 20
            
            # MACD trend
            if macd['macd'] > macd['signal']:
                long_term_score += 15
            else:
                long_term_score -= 5
            
            # Volume confirmation
            if volume_surge > 1.3:
                long_term_score += 10
            
            # Clamp score
            long_term_score = max(0, min(100, long_term_score))
            
            # Determine signals
            if short_term_score >= 70:
                short_term_signal = 'STRONG BUY'
            elif short_term_score >= 55:
                short_term_signal = 'BUY'
            elif short_term_score <= 30:
                short_term_signal = 'SELL'
            else:
                short_term_signal = 'HOLD'
            
            if long_term_score >= 70:
                long_term_signal = 'STRONG BUY'
            elif long_term_score >= 55:
                long_term_signal = 'BUY'
            elif long_term_score <= 30:
                long_term_signal = 'AVOID'
            else:
                long_term_signal = 'HOLD'
            
            return {
                'code': code,
                'name': stock_info['name'],
                'symbol': symbol,
                'sector': stock_info['sector'],
                'price': round(current_price, 2),
                'change': round(price_change, 2),
                'rsi': round(rsi, 1),
                'macd_histogram': round(macd['histogram'], 2),
                'volume_surge': round(volume_surge, 2),
                'momentum_5': round(momentum_5, 2),
                'momentum_10': round(momentum_10, 2),
                'atr_pct': round(atr_pct, 2),
                'short_term_score': round(short_term_score),
                'short_term_signal': short_term_signal,
                'long_term_score': round(long_term_score),
                'long_term_signal': long_term_signal,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error analyzing {code}: {e}")
            return None
    
    def analyze_all_stocks(self) -> List[Dict]:
        """Analyze all NIFTY50 stocks in parallel"""
        cache_key = 'all_stocks_analysis'
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        results = []
        
        # Use thread pool for parallel fetching
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(self.analyze_stock, code, info): code 
                for code, info in NIFTY50_STOCKS.items()
            }
            
            for future in as_completed(futures):
                code = futures[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"Error processing {code}: {e}")
        
        # Cache results
        self.cache[cache_key] = results
        self.cache_time[cache_key] = time.time()
        
        return results
    
    def get_top_short_term_picks(self, count: int = 10) -> List[Dict]:
        """Get top stocks for short-term (15-min) trading"""
        all_stocks = self.analyze_all_stocks()
        
        # Sort by short-term score descending
        sorted_stocks = sorted(all_stocks, key=lambda x: x['short_term_score'], reverse=True)
        
        return sorted_stocks[:count]
    
    def get_top_long_term_picks(self, count: int = 10) -> List[Dict]:
        """Get top stocks for long-term investment"""
        all_stocks = self.analyze_all_stocks()
        
        # Sort by long-term score descending
        sorted_stocks = sorted(all_stocks, key=lambda x: x['long_term_score'], reverse=True)
        
        return sorted_stocks[:count]
    
    def get_market_overview(self) -> Dict:
        """Get overall market sentiment from analyzed stocks"""
        all_stocks = self.analyze_all_stocks()
        
        if not all_stocks:
            return {'sentiment': 'NEUTRAL', 'bullish_count': 0, 'bearish_count': 0}
        
        bullish = sum(1 for s in all_stocks if s['short_term_signal'] in ['BUY', 'STRONG BUY'])
        bearish = sum(1 for s in all_stocks if s['short_term_signal'] in ['SELL'])
        total = len(all_stocks)
        
        bullish_pct = (bullish / total) * 100 if total > 0 else 0
        
        if bullish_pct >= 60:
            sentiment = 'BULLISH'
        elif bullish_pct <= 30:
            sentiment = 'BEARISH'
        else:
            sentiment = 'NEUTRAL'
        
        return {
            'sentiment': sentiment,
            'bullish_count': bullish,
            'bearish_count': bearish,
            'total_analyzed': total,
            'bullish_percentage': round(bullish_pct, 1)
        }


# Singleton instance
stock_analyzer = StockAnalyzer()


def get_short_term_picks(count: int = 10) -> List[Dict]:
    """Get top stocks for short-term trading"""
    return stock_analyzer.get_top_short_term_picks(count)


def get_long_term_picks(count: int = 10) -> List[Dict]:
    """Get top stocks for long-term investment"""
    return stock_analyzer.get_top_long_term_picks(count)


def get_all_analysis() -> List[Dict]:
    """Get analysis for all stocks"""
    return stock_analyzer.analyze_all_stocks()


def get_market_overview() -> Dict:
    """Get market sentiment overview"""
    return stock_analyzer.get_market_overview()
