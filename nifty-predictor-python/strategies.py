"""
Trading Strategies Module
18 Professional Trading Strategies with weighted signals
"""

from typing import Dict, List, Optional, Tuple
from global_constants import STRATEGY_WEIGHTS

try:
    from pro_strategies import analyze_pro_strategies
    PRO_STRATEGIES_AVAILABLE = True
except ImportError:
    PRO_STRATEGIES_AVAILABLE = False
    analyze_pro_strategies = None


class TradingStrategies:
    """
    Complete trading strategy library with 18 professional strategies
    """
    
    @staticmethod
    def check_sideways(indicators: Dict) -> Tuple[bool, str]:
        """Detect if market is sideways/consolidating"""
        adx = indicators.get('adx', {}).get('adx', 0)
        
        # Bollinger Band Width
        bb = indicators.get('bollinger', {})
        bb_width = 0
        if bb:
            upper = bb.get('upper', 0)
            lower = bb.get('lower', 0)
            middle = bb.get('middle', 1) # Prevent div by zero
            if middle > 0:
                bb_width = ((upper - lower) / middle) * 100
        
        if adx < 20:
            return True, f"Weak Trend (ADX: {adx:.1f})"
        if bb_width < 0.15: # Very tight squeeze
            return True, f"Volatility Squeeze (BB Width: {bb_width:.2f}%)"
            
        return False, ""

    @staticmethod
    def detect_patterns(candles: List[Dict]) -> List[str]:
        """Detect basic candlestick patterns from last few candles"""
        patterns = []
        if len(candles) < 3:
            return patterns
            
        c1 = candles[-1] # Current
        c2 = candles[-2] # Previous
        
        # Helper to get body/wick
        def get_candle_props(c):
            open_p, close_p = c['open'], c['close']
            high_p, low_p = c['high'], c['low']
            body = abs(close_p - open_p)
            upper_wick = high_p - max(open_p, close_p)
            lower_wick = min(open_p, close_p) - low_p
            color = 'green' if close_p > open_p else 'red'
            total_len = high_p - low_p
            return body, upper_wick, lower_wick, color, total_len

        b1, u1, l1, color1, len1 = get_candle_props(c1)
        b2, u2, l2, color2, len2 = get_candle_props(c2)
        
        # Hammer / Shooting Star (Approximate)
        if l1 > (2 * b1) and u1 < b1:
             patterns.append("Hammer (Reversal)")
        if u1 > (2 * b1) and l1 < b1:
             patterns.append("Shooting Star (Reversal)")
             
        # Bullish Engulfing
        if color1 == 'green' and color2 == 'red' and c1['close'] > c2['open'] and c1['open'] < c2['close']:
            patterns.append("Bullish Engulfing")
            
        # Bearish Engulfing
        if color1 == 'red' and color2 == 'green' and c1['close'] < c2['open'] and c1['open'] > c2['close']:
            patterns.append("Bearish Engulfing")
            
        return patterns

    @staticmethod
    def rsi_strategy(rsi: Optional[float]) -> Dict:
        """RSI Overbought/Oversold Strategy"""
        if rsi is None:
            return {'signal': 'neutral', 'strength': 50, 'reason': 'RSI data unavailable'}
        
        if rsi < 30:
            return {'signal': 'bullish', 'strength': 85, 'reason': 'RSI Oversold (<30) - Strong Buy Signal'}
        elif rsi > 70:
            return {'signal': 'bearish', 'strength': 85, 'reason': 'RSI Overbought (>70) - Strong Sell Signal'}
        elif rsi < 40:
            return {'signal': 'bullish', 'strength': 60, 'reason': 'RSI approaching oversold zone'}
        elif rsi > 60:
            return {'signal': 'bearish', 'strength': 60, 'reason': 'RSI approaching overbought zone'}
        
        return {'signal': 'neutral', 'strength': 50, 'reason': f'RSI in neutral zone ({rsi:.1f})'}
    
    @staticmethod
    def macd_strategy(macd: Optional[Dict]) -> Dict:
        """MACD Crossover Strategy"""
        if macd is None:
            return {'signal': 'neutral', 'strength': 50, 'reason': 'MACD data unavailable'}
        
        histogram = macd.get('histogram', 0)
        macd_line = macd.get('macd', 0)
        
        if histogram > 0 and macd_line > 0:
            return {'signal': 'bullish', 'strength': 75, 'reason': 'MACD above signal, positive histogram'}
        elif histogram < 0 and macd_line < 0:
            return {'signal': 'bearish', 'strength': 75, 'reason': 'MACD below signal, negative histogram'}
        elif histogram > 0:
            return {'signal': 'bullish', 'strength': 60, 'reason': 'MACD histogram turning positive'}
        elif histogram < 0:
            return {'signal': 'bearish', 'strength': 60, 'reason': 'MACD histogram turning negative'}
        
        return {'signal': 'neutral', 'strength': 50, 'reason': 'MACD showing mixed signals'}
    
    @staticmethod
    def ma_crossover_strategy(ema_20: Optional[float], 
                               ema_50: Optional[float], 
                               price: float) -> Dict:
        """Moving Average Crossover Strategy"""
        if ema_20 is None or ema_50 is None:
            return {'signal': 'neutral', 'strength': 50, 'reason': 'MA data unavailable'}
        
        if ema_20 > ema_50 and price > ema_20:
            return {'signal': 'bullish', 'strength': 80, 'reason': 'Golden Cross - EMA20 > EMA50, price above'}
        elif ema_20 < ema_50 and price < ema_20:
            return {'signal': 'bearish', 'strength': 80, 'reason': 'Death Cross - EMA20 < EMA50, price below'}
        elif ema_20 > ema_50:
            return {'signal': 'bullish', 'strength': 55, 'reason': 'EMA20 above EMA50'}
        elif ema_20 < ema_50:
            return {'signal': 'bearish', 'strength': 55, 'reason': 'EMA20 below EMA50'}
        
        return {'signal': 'neutral', 'strength': 50, 'reason': 'MAs showing consolidation'}
    
    @staticmethod
    def bollinger_strategy(bb: Optional[Dict], price: float) -> Dict:
        """Bollinger Bands Strategy"""
        if bb is None:
            return {'signal': 'neutral', 'strength': 50, 'reason': 'Bollinger data unavailable'}
        
        upper = bb['upper']
        lower = bb['lower']
        middle = bb['middle']
        
        if price <= lower:
            return {'signal': 'bullish', 'strength': 82, 'reason': 'Price at lower band - Oversold bounce expected'}
        elif price >= upper:
            return {'signal': 'bearish', 'strength': 82, 'reason': 'Price at upper band - Overbought pullback expected'}
        elif price > middle:
            return {'signal': 'bullish', 'strength': 55, 'reason': 'Price above middle band'}
        else:
            return {'signal': 'bearish', 'strength': 55, 'reason': 'Price below middle band'}
    
    @staticmethod
    def stochastic_strategy(stoch: Optional[Dict]) -> Dict:
        """Stochastic Oscillator Strategy"""
        if stoch is None:
            return {'signal': 'neutral', 'strength': 50, 'reason': 'Stochastic data unavailable'}
        
        k = stoch['k']
        d = stoch['d']
        
        if k < 20 and d < 20:
            return {'signal': 'bullish', 'strength': 80, 'reason': 'Stochastic in oversold zone (<20)'}
        elif k > 80 and d > 80:
            return {'signal': 'bearish', 'strength': 80, 'reason': 'Stochastic in overbought zone (>80)'}
        elif k > d:
            return {'signal': 'bullish', 'strength': 60, 'reason': 'Stochastic %K crossed above %D'}
        else:
            return {'signal': 'bearish', 'strength': 60, 'reason': 'Stochastic %K crossed below %D'}
    
    @staticmethod
    def adx_strategy(adx: Optional[Dict]) -> Dict:
        """ADX Trend Strength Strategy"""
        if adx is None:
            return {'signal': 'neutral', 'strength': 50, 'reason': 'ADX data unavailable'}
        
        adx_value = adx['adx']
        plus_di = adx['plus_di']
        minus_di = adx['minus_di']
        
        if adx_value > 25:
            if plus_di > minus_di:
                return {'signal': 'bullish', 'strength': 78, 'reason': f'Strong uptrend (ADX={adx_value:.0f}, +DI > -DI)'}
            else:
                return {'signal': 'bearish', 'strength': 78, 'reason': f'Strong downtrend (ADX={adx_value:.0f}, -DI > +DI)'}
        elif adx_value > 20:
            return {'signal': 'neutral', 'strength': 55, 'reason': f'Moderate trend (ADX={adx_value:.0f})'}
        
        return {'signal': 'neutral', 'strength': 45, 'reason': f'Weak/No trend (ADX={adx_value:.0f})'}
    
    @staticmethod
    def supertrend_strategy(supertrend: Optional[Dict], price: float) -> Dict:
        """SuperTrend Strategy"""
        if supertrend is None:
            return {'signal': 'neutral', 'strength': 50, 'reason': 'SuperTrend data unavailable'}
        
        trend = supertrend['trend']
        
        if trend == 'bullish':
            return {'signal': 'bullish', 'strength': 85, 'reason': 'SuperTrend indicates bullish trend'}
        else:
            return {'signal': 'bearish', 'strength': 85, 'reason': 'SuperTrend indicates bearish trend'}
    
    @staticmethod
    def vwap_strategy(vwap: Optional[float], price: float) -> Dict:
        """VWAP Strategy"""
        if vwap is None:
            return {'signal': 'neutral', 'strength': 50, 'reason': 'VWAP data unavailable'}
        
        diff_pct = ((price - vwap) / vwap) * 100
        
        if price > vwap:
            strength = min(80, 60 + abs(diff_pct) * 10)
            return {'signal': 'bullish', 'strength': int(strength), 
                    'reason': f'Price {diff_pct:.2f}% above VWAP - Bullish'}
        else:
            strength = min(80, 60 + abs(diff_pct) * 10)
            return {'signal': 'bearish', 'strength': int(strength), 
                    'reason': f'Price {abs(diff_pct):.2f}% below VWAP - Bearish'}
    
    @staticmethod
    def ichimoku_strategy(ichimoku: Optional[Dict]) -> Dict:
        """Ichimoku Cloud Strategy"""
        if ichimoku is None:
            return {'signal': 'neutral', 'strength': 50, 'reason': 'Ichimoku data unavailable'}
        
        tenkan = ichimoku['tenkan']
        kijun = ichimoku['kijun']
        senkou_a = ichimoku['senkou_a']
        price = ichimoku['current_price']
        
        if price > senkou_a and tenkan > kijun:
            return {'signal': 'bullish', 'strength': 82, 'reason': 'Price above cloud, Tenkan > Kijun'}
        elif price < senkou_a and tenkan < kijun:
            return {'signal': 'bearish', 'strength': 82, 'reason': 'Price below cloud, Tenkan < Kijun'}
        elif price > senkou_a:
            return {'signal': 'bullish', 'strength': 60, 'reason': 'Price above cloud'}
        elif price < senkou_a:
            return {'signal': 'bearish', 'strength': 60, 'reason': 'Price below cloud'}
        
        return {'signal': 'neutral', 'strength': 50, 'reason': 'Price inside cloud - consolidation'}
    
    @staticmethod
    def psar_strategy(psar: Optional[Dict]) -> Dict:
        """Parabolic SAR Strategy"""
        if psar is None:
            return {'signal': 'neutral', 'strength': 50, 'reason': 'PSAR data unavailable'}
        
        trend = psar['trend']
        
        if trend == 'bullish':
            return {'signal': 'bullish', 'strength': 75, 'reason': 'Parabolic SAR below price - Uptrend'}
        else:
            return {'signal': 'bearish', 'strength': 75, 'reason': 'Parabolic SAR above price - Downtrend'}
    
    @staticmethod
    def cci_strategy(cci: Optional[float]) -> Dict:
        """CCI Strategy"""
        if cci is None:
            return {'signal': 'neutral', 'strength': 50, 'reason': 'CCI data unavailable'}
        
        if cci < -100:
            return {'signal': 'bullish', 'strength': 80, 'reason': f'CCI extremely oversold ({cci:.0f})'}
        elif cci > 100:
            return {'signal': 'bearish', 'strength': 80, 'reason': f'CCI extremely overbought ({cci:.0f})'}
        elif cci < -50:
            return {'signal': 'bullish', 'strength': 60, 'reason': f'CCI oversold ({cci:.0f})'}
        elif cci > 50:
            return {'signal': 'bearish', 'strength': 60, 'reason': f'CCI overbought ({cci:.0f})'}
        
        return {'signal': 'neutral', 'strength': 50, 'reason': f'CCI neutral ({cci:.0f})'}
    
    @staticmethod
    def williams_r_strategy(wr: Optional[float]) -> Dict:
        """Williams %R Strategy"""
        if wr is None:
            return {'signal': 'neutral', 'strength': 50, 'reason': 'Williams %R data unavailable'}
        
        if wr < -80:
            return {'signal': 'bullish', 'strength': 78, 'reason': f'Williams %R oversold ({wr:.0f})'}
        elif wr > -20:
            return {'signal': 'bearish', 'strength': 78, 'reason': f'Williams %R overbought ({wr:.0f})'}
        
        return {'signal': 'neutral', 'strength': 50, 'reason': f'Williams %R neutral ({wr:.0f})'}
    
    @staticmethod
    def mfi_strategy(mfi: Optional[float]) -> Dict:
        """Money Flow Index Strategy"""
        if mfi is None:
            return {'signal': 'neutral', 'strength': 50, 'reason': 'MFI data unavailable'}
        
        if mfi < 20:
            return {'signal': 'bullish', 'strength': 80, 'reason': f'MFI oversold ({mfi:.0f}) - Accumulation'}
        elif mfi > 80:
            return {'signal': 'bearish', 'strength': 80, 'reason': f'MFI overbought ({mfi:.0f}) - Distribution'}
        elif mfi > 50:
            return {'signal': 'bullish', 'strength': 55, 'reason': f'MFI above 50 ({mfi:.0f})'}
        
        return {'signal': 'bearish', 'strength': 55, 'reason': f'MFI below 50 ({mfi:.0f})'}
    
    @staticmethod
    def pivot_strategy(pivots: Optional[Dict], price: float) -> Dict:
        """Pivot Point Strategy"""
        if pivots is None:
            return {'signal': 'neutral', 'strength': 50, 'reason': 'Pivot data unavailable'}
        
        # Get pivot values with safe access (handles both 'pp' and 'pivot' keys)
        pp = pivots.get('pp') or pivots.get('pivot')
        r1 = pivots.get('r1')
        s1 = pivots.get('s1')
        
        if pp is None or r1 is None or s1 is None:
            return {'signal': 'neutral', 'strength': 50, 'reason': 'Pivot data incomplete'}
        
        if price > r1:
            return {'signal': 'bullish', 'strength': 75, 'reason': 'Price above R1 - Strong bullish'}
        elif price < s1:
            return {'signal': 'bearish', 'strength': 75, 'reason': 'Price below S1 - Strong bearish'}
        elif price > pp:
            return {'signal': 'bullish', 'strength': 60, 'reason': 'Price above Pivot Point'}
        
        return {'signal': 'bearish', 'strength': 60, 'reason': 'Price below Pivot Point'}
    
    @staticmethod
    def oi_strategy(ce_oi: int, pe_oi: int, ce_change: int, pe_change: int) -> Dict:
        """Open Interest Analysis Strategy"""
        if ce_oi == 0 or pe_oi == 0:
            return {'signal': 'neutral', 'strength': 50, 'reason': 'OI data unavailable'}
        
        pcr = pe_oi / ce_oi
        
        if pcr > 1.2 and pe_change > 0:
            return {'signal': 'bullish', 'strength': 75, 'reason': f'High PE OI (PCR={pcr:.2f}) - Support building'}
        elif pcr < 0.8 and ce_change > 0:
            return {'signal': 'bearish', 'strength': 75, 'reason': f'High CE OI (PCR={pcr:.2f}) - Resistance building'}
        
        return {'signal': 'neutral', 'strength': 50, 'reason': f'Balanced OI (PCR={pcr:.2f})'}
    
    @staticmethod
    def pcr_strategy(pcr: float) -> Dict:
        """Put-Call Ratio Strategy"""
        if pcr < 0.7:
            return {'signal': 'bearish', 'strength': 70, 'reason': f'Low PCR ({pcr:.2f}) - Extreme bullishness (contrarian bearish)'}
        elif pcr > 1.3:
            return {'signal': 'bullish', 'strength': 70, 'reason': f'High PCR ({pcr:.2f}) - Extreme fear (contrarian bullish)'}
        elif pcr < 0.9:
            return {'signal': 'bullish', 'strength': 60, 'reason': f'PCR in bullish zone ({pcr:.2f})'}
        elif pcr > 1.1:
            return {'signal': 'bearish', 'strength': 60, 'reason': f'PCR in bearish zone ({pcr:.2f})'}
        
        return {'signal': 'neutral', 'strength': 50, 'reason': f'PCR neutral ({pcr:.2f})'}
    
    @staticmethod
    def vix_strategy(vix: float, vix_change: float) -> Dict:
        """VIX/Volatility Strategy"""
        if vix < 12 and vix_change < 0:
            return {'signal': 'bullish', 'strength': 70, 'reason': f'Low VIX ({vix:.1f}) and falling - Complacency'}
        elif vix > 20:
            return {'signal': 'bullish', 'strength': 65, 'reason': f'High VIX ({vix:.1f}) - Extreme fear (contrarian bullish)'}
        elif vix > 15 and vix_change > 0:
            return {'signal': 'bearish', 'strength': 65, 'reason': f'Rising VIX ({vix:.1f}) - Increasing fear'}
        
        return {'signal': 'neutral', 'strength': 50, 'reason': f'VIX normal ({vix:.1f})'}
    
    @staticmethod
    def fii_dii_strategy(fii_net: float, dii_net: float) -> Dict:
        """FII/DII Flow Strategy"""
        total_flow = fii_net + dii_net
        
        if fii_net > 1000 and dii_net > 0:
            return {'signal': 'bullish', 'strength': 80, 'reason': 'Strong FII buying with DII support'}
        elif fii_net < -1000 and dii_net < 0:
            return {'signal': 'bearish', 'strength': 80, 'reason': 'Strong FII selling with DII selling'}
        elif total_flow > 1500:
            return {'signal': 'bullish', 'strength': 70, 'reason': f'Net institutional buying ({total_flow:.0f} Cr)'}
        elif total_flow < -1500:
            return {'signal': 'bearish', 'strength': 70, 'reason': f'Net institutional selling ({total_flow:.0f} Cr)'}
        
        return {'signal': 'neutral', 'strength': 50, 'reason': 'Mixed institutional activity'}
    

    @staticmethod
    def generate_pro_analysis(strategies: List[Dict], sideways: bool, sideways_reason: str, patterns: List[str]) -> str:
        """Generate detailed professional analysis text"""
        
        # 1. Market State
        if sideways:
            state = f"SIDEWAYS / CONSOLIDATION ({sideways_reason})"
            action = "WAIT for breakout."
        else:
            bullish_count = sum(1 for s in strategies if s['signal'] == 'bullish')
            bearish_count = sum(1 for s in strategies if s['signal'] == 'bearish')
            if bullish_count > bearish_count:
                state = "BULLISH MOMENTUM"
                action = "LOOK FOR BUY ENTERIES."
            elif bearish_count > bullish_count:
                state = "BEARISH MOMENTUM"
                action = "LOOK FOR SELL ENTRIES."
            else:
                state = "NEUTRAL / MIXED"
                action = "CAUTION ADVISED."

        # 2. Key Confirmations
        top_confirmations = sorted(
            [s for s in strategies if s['signal'] != 'neutral'], 
            key=lambda x: x['strength'], 
            reverse=True
        )[:3]
        
        conf_text = ", ".join([f"{s['name']}: {s['reason']}" for s in top_confirmations])
        
        # 3. Patterns
        pattern_text = f"Patterns: {', '.join(patterns)}" if patterns else "No Key Patterns"
        
        return f"MARKET STATE: {state} | {action}\nCONFIRMATIONS: {conf_text}\n{pattern_text}"

    @staticmethod
    def analyze_all(indicators: Dict, price: float, sentiment: Optional[Dict] = None, candles: List[Dict] = None,
                    option_chain: Optional[List[Dict]] = None) -> Dict:
        """Run all strategies (18 classic + 15 pro) and return results with detailed analysis"""
        strategies = []
        candles = candles or []
        
        # Check Sideways
        is_sideways, sideways_reason = TradingStrategies.check_sideways(indicators)
        
        # Check Patterns
        patterns = TradingStrategies.detect_patterns(candles)
        
        # Technical Strategies
        strategies.append({
            'name': 'RSI Analysis',
            'category': 'momentum',
            **TradingStrategies.rsi_strategy(indicators.get('rsi'))
        })
        
        strategies.append({
            'name': 'MACD Crossover',
            'category': 'momentum',
            **TradingStrategies.macd_strategy(indicators.get('macd'))
        })
        
        strategies.append({
            'name': 'MA Crossover',
            'category': 'trend',
            **TradingStrategies.ma_crossover_strategy(
                indicators.get('ema_20'),
                indicators.get('ema_50'),
                price
            )
        })
        
        strategies.append({
            'name': 'Bollinger Bands',
            'category': 'volatility',
            **TradingStrategies.bollinger_strategy(indicators.get('bollinger'), price)
        })
        
        strategies.append({
            'name': 'Stochastic',
            'category': 'momentum',
            **TradingStrategies.stochastic_strategy(indicators.get('stochastic'))
        })
        
        strategies.append({
            'name': 'ADX Trend',
            'category': 'trend',
            **TradingStrategies.adx_strategy(indicators.get('adx'))
        })
        
        strategies.append({
            'name': 'SuperTrend',
            'category': 'trend',
            **TradingStrategies.supertrend_strategy(indicators.get('supertrend'), price)
        })
        
        strategies.append({
            'name': 'VWAP',
            'category': 'volume',
            **TradingStrategies.vwap_strategy(indicators.get('vwap'), price)
        })
        
        strategies.append({
            'name': 'Ichimoku Cloud',
            'category': 'trend',
            **TradingStrategies.ichimoku_strategy(indicators.get('ichimoku'))
        })
        
        strategies.append({
            'name': 'Parabolic SAR',
            'category': 'trend',
            **TradingStrategies.psar_strategy(indicators.get('psar'))
        })
        
        strategies.append({
            'name': 'CCI Analysis',
            'category': 'momentum',
            **TradingStrategies.cci_strategy(indicators.get('cci'))
        })
        
        strategies.append({
            'name': 'Williams %R',
            'category': 'momentum',
            **TradingStrategies.williams_r_strategy(indicators.get('williams_r'))
        })
        
        strategies.append({
            'name': 'MFI Analysis',
            'category': 'volume',
            **TradingStrategies.mfi_strategy(indicators.get('mfi'))
        })
        
        strategies.append({
            'name': 'Pivot Points',
            'category': 'support_resistance',
            **TradingStrategies.pivot_strategy(indicators.get('pivot_points'), price)
        })
        
        # Sentiment Strategies
        if sentiment:
            strategies.append({
                'name': 'PCR Analysis',
                'category': 'sentiment',
                **TradingStrategies.pcr_strategy(sentiment.get('pcr', 1.0))
            })
            
            strategies.append({
                'name': 'VIX Analysis',
                'category': 'sentiment',
                **TradingStrategies.vix_strategy(
                    sentiment.get('vix', 14),
                    sentiment.get('vix_change', 0)
                )
            })
            
            strategies.append({
                'name': 'FII/DII Flow',
                'category': 'sentiment',
                **TradingStrategies.fii_dii_strategy(
                    sentiment.get('fii_net', 0),
                    sentiment.get('dii_net', 0)
                )
            })
            
            strategies.append({
                'name': 'Open Interest',
                'category': 'sentiment',
                **TradingStrategies.oi_strategy(
                    sentiment.get('total_ce_oi', 1000000),
                    sentiment.get('total_pe_oi', 1000000),
                    0, 0
                )
            })
        
        
        # --- 15 Pro strategies (price action + volume + option chain) ---
        pro_verdict = None
        if PRO_STRATEGIES_AVAILABLE and candles:
            try:
                pro_out = analyze_pro_strategies(indicators, price, candles, sentiment, option_chain)
                strategies.extend(pro_out['strategies'])
                pro_verdict = pro_out['pro_verdict']
            except Exception as e:
                print(f"[WARN] Pro strategies failed: {e}")

        # Generate Pro Analysis
        analysis_text = TradingStrategies.generate_pro_analysis(strategies, is_sideways, sideways_reason, patterns)

        return {
            'strategies': strategies,
            'is_sideways': is_sideways,
            'sideways_reason': sideways_reason,
            'patterns': patterns,
            'pro_analysis': analysis_text,
            'pro_verdict': pro_verdict,
        }
    
    @staticmethod
    def calculate_prediction(strategies: List[Dict]) -> Dict:
        """Calculate overall prediction from all strategies"""
        if not strategies:
            return {
                'direction': 'NEUTRAL',
                'ce_prob': 50,
                'pe_prob': 50,
                'confidence': 0
            }
        
        bullish_score = 0
        bearish_score = 0
        total_weight = 0
        
        for strategy in strategies:
            weight = strategy['strength'] / 100
            total_weight += weight
            
            if strategy['signal'] == 'bullish':
                bullish_score += weight
            elif strategy['signal'] == 'bearish':
                bearish_score += weight
        
        if total_weight == 0:
            return {
                'direction': 'NEUTRAL',
                'ce_prob': 50,
                'pe_prob': 50,
                'confidence': 0
            }
        
        bullish_pct = (bullish_score / total_weight) * 100
        bearish_pct = (bearish_score / total_weight) * 100
        
        if bullish_pct > bearish_pct:
            direction = 'BULLISH'
        elif bearish_pct > bullish_pct:
            direction = 'BEARISH'
        else:
            direction = 'NEUTRAL'
        
        confidence = abs(bullish_pct - bearish_pct)
        
        return {
            'direction': direction,
            'ce_prob': round(bullish_pct),
            'pe_prob': round(bearish_pct),
            'confidence': round(confidence)
        }
