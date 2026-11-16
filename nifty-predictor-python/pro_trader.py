"""
Pro Trader Module - Professional Trading Calculations
Handles option recommendations, lot sizing, backtesting, and forward predictions
"""

from typing import Dict, List, Optional
from scipy.stats import norm
import numpy as np

# Lot sizes for index options
LOT_SIZES = {
    'nifty': 25,
    'banknifty': 15
}

# Default risk per trade in INR
DEFAULT_RISK_PER_TRADE = 5000

# Target profit percentage
TARGET_PROFIT_PCT = 30


class ProTrader:
    """Professional trading calculations for options"""
    
    @staticmethod
    def black_scholes(S, K, T, r, sigma, option_type='CE'):
        """
        Calculate Black-Scholes option price
        S: Spot price
        K: Strike price
        T: Time to expiry (in years)
        r: Risk-free rate (decimal)
        sigma: Volatility (decimal)
        """
        try:
            d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            
            if option_type == 'CE':
                price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
            else:
                price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
            
            return max(0.05, price) # Minimum price
        except:
            return 0

    @staticmethod
    def calculate_option_recommendation(
        index: str,
        spot_price: float,
        direction: str,
        option_chain: Optional[List[Dict]],
        target_profit_pct: float = TARGET_PROFIT_PCT
    ) -> Dict:
        """
        Calculate the best option strike for a given profit target
        
        Returns:
            strike: Recommended strike price
            option_type: CE or PE
            premium: Option premium (LTP)
            target_premium: Premium at target profit
            confidence: How likely to achieve target
        """
        if not option_chain or len(option_chain) == 0:
            return {
                'strike': None,
                'option_type': 'CE' if direction == 'BULLISH' else 'PE',
                'premium': 0,
                'target_premium': 0,
                'confidence': 0,
                'recommendation': f"Option chain data unavailable"
            }
        
        option_type = 'CE' if direction == 'BULLISH' else 'PE'
        lot_size = LOT_SIZES.get(index.lower(), 25)
        
        # Find ATM strike
        atm_strike = min(option_chain, key=lambda x: abs(x['strike'] - spot_price))['strike']
        
        # For CALL: Look at ATM and 1-2 strikes ITM/OTM
        # For PUT: Similar logic
        candidates = []
        is_estimated = False
        
        # Determine time to expiry (approx 3 days if not provided)
        # Using 0.15 as default volatility (IV) if we can't get it
        days_to_expiry = 3 
        T = days_to_expiry / 365.0
        r = 0.07 # 7% risk free rate
        sigma = 0.15 # 15% VIX default
        
        for row in option_chain:
            strike = row['strike']
            
            if option_type == 'CE':
                premium = row.get('ce_ltp', 0)
                oi = row.get('ce_oi', 0)
            else:
                premium = row.get('pe_ltp', 0)
                oi = row.get('pe_oi', 0)
            
            # FALLBACK: If premium is 0, estimate it
            if premium <= 0 and spot_price > 0:
                premium = ProTrader.black_scholes(spot_price, strike, T, r, sigma, option_type)
                is_estimated = True
            
            if premium <= 0:
                continue
                
            # Calculate target premium for desired profit
            target_premium = premium * (1 + target_profit_pct / 100)
            
            # Estimate potential points movement needed
            if option_type == 'CE':
                # For call, need spot to go up
                points_needed = (target_premium - premium) * 0.7  # Delta approximation
            else:
                # For put, need spot to go down  
                points_needed = (target_premium - premium) * 0.7
            
            # Score based on OI (liquidity), premium affordability, distance from ATM
            distance_from_atm = abs(strike - atm_strike)
            atm_score = max(0, 100 - distance_from_atm / 10)  # Closer to ATM = better
            oi_score = min(100, (oi / 1000000) * 20)  # Normalize OI
            premium_score = 100 if 50 <= premium <= 300 else 50  # Prefer mid-range premiums
            
            total_score = atm_score * 0.4 + oi_score * 0.3 + premium_score * 0.3
            
            candidates.append({
                'strike': strike,
                'premium': premium,
                'target_premium': round(target_premium, 2),
                'oi': oi,
                'score': total_score,
                'points_needed': round(points_needed, 2),
                'is_atm': row.get('is_atm', False)
            })
        
        if not candidates:
            return {
                'strike': atm_strike,
                'option_type': option_type,
                'premium': 0,
                'target_premium': 0,
                'confidence': 0,
                'recommendation': 'No suitable options found'
            }
        
        # Sort by score and pick best
        candidates.sort(key=lambda x: x['score'], reverse=True)
        best = candidates[0]
        
        # Calculate profit per lot
        profit_per_lot = (best['target_premium'] - best['premium']) * lot_size
        
        est_label = " (Est)" if is_estimated else ""
        
        return {
            'strike': best['strike'],
            'option_type': option_type,
            'premium': round(best['premium'], 2),
            'target_premium': best['target_premium'],
            'points_needed': best['points_needed'],
            'oi': best['oi'],
            'profit_per_lot': round(profit_per_lot, 2),
            'lot_size': lot_size,
            'confidence': round(best['score']),
            'recommendation': f"BUY {index.upper()} {int(best['strike'])} {option_type} @ ₹{best['premium']:.2f}{est_label}"
        }
    
    @staticmethod
    def calculate_lot_size(
        premium: float,
        stop_loss_pct: float = 30,
        max_risk: float = DEFAULT_RISK_PER_TRADE,
        lot_size: int = 25
    ) -> Dict:
        """
        Calculate number of lots based on risk management
        
        Args:
            premium: Option premium per unit
            stop_loss_pct: Stop loss percentage
            max_risk: Maximum risk per trade in INR
            lot_size: Number of units per lot
            
        Returns:
            suggested_lots: Recommended number of lots
            total_investment: Total premium to pay
            max_loss: Maximum possible loss
        """
        if premium <= 0:
            return {
                'suggested_lots': 1,
                'total_investment': 0,
                'max_loss': 0,
                'risk_per_lot': 0
            }
        
        # Risk per lot = Premium * Lot Size * Stop Loss %
        risk_per_lot = premium * lot_size * (stop_loss_pct / 100)
        
        # Maximum lots based on risk tolerance
        suggested_lots = max(1, int(max_risk / risk_per_lot))
        
        # Cap at reasonable level
        suggested_lots = min(suggested_lots, 10)
        
        total_investment = premium * lot_size * suggested_lots
        max_loss = risk_per_lot * suggested_lots
        
        return {
            'suggested_lots': suggested_lots,
            'total_investment': round(total_investment, 2),
            'max_loss': round(max_loss, 2),
            'risk_per_lot': round(risk_per_lot, 2)
        }
    
    @staticmethod
    def calculate_risk_reward(
        entry_price: float,
        stop_loss: float,
        target: float
    ) -> Dict:
        """Calculate risk-reward ratio"""
        if entry_price <= 0:
            return {'ratio': 0, 'risk': 0, 'reward': 0}
            
        risk = abs(entry_price - stop_loss)
        reward = abs(target - entry_price)
        
        ratio = round(reward / risk, 2) if risk > 0 else 0
        
        return {
            'ratio': ratio,
            'risk': round(risk, 2),
            'reward': round(reward, 2)
        }
    
    @staticmethod
    def calculate_profit_at_target(
        entry_premium: float,
        target_premium: float,
        lot_size: int,
        num_lots: int
    ) -> float:
        """Calculate profit in INR at target"""
        points_gain = target_premium - entry_premium
        return round(points_gain * lot_size * num_lots, 2)
    
    @staticmethod
    def predict_direction_15min(
        candles: List[Dict],
        indicators: Dict,
        ml_prediction: Dict
    ) -> Dict:
        """
        Predict market direction for next 15 minutes
        Combines multiple signals for higher accuracy
        """
        if not candles or len(candles) < 5:
            return {
                'direction': 'NEUTRAL',
                'confidence': 0,
                'reasoning': 'Insufficient data'
            }
        
        signals = []
        weights = []
        
        # 1. Momentum Signal (RSI + MACD) - WITH NONE SAFETY
        rsi = indicators.get('rsi')
        if rsi is None:
            rsi = 50  # Default neutral
        macd = indicators.get('macd') or {}
        histogram = macd.get('histogram')
        if histogram is None:
            histogram = 0
        
        momentum_signal = 0
        if rsi < 40 and histogram > 0:
            momentum_signal = 1  # Bullish
        elif rsi > 60 and histogram < 0:
            momentum_signal = -1  # Bearish
        signals.append(momentum_signal)
        weights.append(0.2)
        
        # 2. Trend Signal (EMA + SuperTrend) - WITH NONE SAFETY
        ema_20 = indicators.get('ema_20')
        ema_50 = indicators.get('ema_50')
        supertrend_data = indicators.get('supertrend') or {}
        supertrend = supertrend_data.get('trend', 'neutral')
        
        trend_signal = 0
        if ema_20 is not None and ema_50 is not None:
            if ema_20 > ema_50 and supertrend == 'bullish':
                trend_signal = 1
            elif ema_20 < ema_50 and supertrend == 'bearish':
                trend_signal = -1
        signals.append(trend_signal)
        weights.append(0.25)
        
        # 3. Volume Signal (VWAP + Volume) - WITH NONE SAFETY
        vwap = indicators.get('vwap')
        current_price = candles[-1].get('close', 0) if candles else 0
        
        volume_signal = 0
        if vwap is not None and current_price > 0:
            if current_price > vwap:
                volume_signal = 1
            elif current_price < vwap:
                volume_signal = -1
        signals.append(volume_signal)
        weights.append(0.15)
        
        # 4. Candle Pattern Signal
        last_candle = candles[-1]
        prev_candle = candles[-2] if len(candles) > 1 else last_candle
        
        pattern_signal = 0
        # Bullish engulfing
        if last_candle['close'] > last_candle['open'] and \
           prev_candle['close'] < prev_candle['open'] and \
           last_candle['close'] > prev_candle['open']:
            pattern_signal = 1
        # Bearish engulfing
        elif last_candle['close'] < last_candle['open'] and \
             prev_candle['close'] > prev_candle['open'] and \
             last_candle['close'] < prev_candle['open']:
            pattern_signal = -1
        signals.append(pattern_signal)
        weights.append(0.1)
        
        # 5. ML Prediction Signal (highest weight)
        ml_signal = 0
        ml_direction = ml_prediction.get('direction', 'NEUTRAL')
        if ml_direction == 'BULLISH':
            ml_signal = 1
        elif ml_direction == 'BEARISH':
            ml_signal = -1
        signals.append(ml_signal)
        weights.append(0.3)
        
        # Calculate weighted direction
        weighted_sum = sum(s * w for s, w in zip(signals, weights))
        
        if weighted_sum > 0.2:
            direction = 'BULLISH'
        elif weighted_sum < -0.2:
            direction = 'BEARISH'
        else:
            direction = 'NEUTRAL'
        
        # Calculate confidence
        confidence = min(95, int(abs(weighted_sum) * 100 + 50))
        
        # Build reasoning
        reasons = []
        if momentum_signal == 1:
            reasons.append("RSI+MACD bullish")
        elif momentum_signal == -1:
            reasons.append("RSI+MACD bearish")
        if trend_signal == 1:
            reasons.append("Uptrend confirmed")
        elif trend_signal == -1:
            reasons.append("Downtrend confirmed")
        if ml_signal != 0:
            reasons.append(f"ML predicts {ml_direction}")
        
        return {
            'direction': direction,
            'confidence': confidence,
            'reasoning': ', '.join(reasons) if reasons else 'Mixed signals',
            'signals': {
                'momentum': momentum_signal,
                'trend': trend_signal,
                'volume': volume_signal,
                'pattern': pattern_signal,
                'ml': ml_signal
            }
        }
    
    @staticmethod
    def backtest_strategy(
        candles: List[Dict],
        strategy_name: str = 'momentum'
    ) -> Dict:
        """
        Backtest a strategy against historical data
        Returns win rate, average profit, and max drawdown
        """
        if not candles or len(candles) < 20:
            return {
                'win_rate': 0,
                'avg_profit_pct': 0,
                'max_drawdown_pct': 0,
                'total_trades': 0,
                'backtest_period': '0 days'
            }
        
        trades = []
        position = None
        
        for i in range(10, len(candles)):
            window = candles[i-10:i]
            current = candles[i]
            
            # Simple SMA crossover strategy for backtest
            sma_5 = sum(c['close'] for c in window[-5:]) / 5
            sma_10 = sum(c['close'] for c in window) / 10
            
            if position is None:
                # Entry logic
                if sma_5 > sma_10:
                    position = {
                        'type': 'LONG',
                        'entry': current['close'],
                        'entry_idx': i
                    }
                elif sma_5 < sma_10:
                    position = {
                        'type': 'SHORT',
                        'entry': current['close'],
                        'entry_idx': i
                    }
            else:
                # Exit logic (reverse signal or 3 candles max)
                hold_time = i - position['entry_idx']
                
                should_exit = False
                if position['type'] == 'LONG' and sma_5 < sma_10:
                    should_exit = True
                elif position['type'] == 'SHORT' and sma_5 > sma_10:
                    should_exit = True
                elif hold_time >= 3:
                    should_exit = True
                
                if should_exit:
                    pnl_pct = 0
                    if position['type'] == 'LONG':
                        pnl_pct = ((current['close'] - position['entry']) / position['entry']) * 100
                    else:
                        pnl_pct = ((position['entry'] - current['close']) / position['entry']) * 100
                    
                    trades.append({
                        'type': position['type'],
                        'entry': position['entry'],
                        'exit': current['close'],
                        'pnl_pct': round(pnl_pct, 2),
                        'win': pnl_pct > 0
                    })
                    position = None
        
        if not trades:
            return {
                'win_rate': 0,
                'avg_profit_pct': 0,
                'max_drawdown_pct': 0,
                'total_trades': 0,
                'backtest_period': f'{len(candles)} candles'
            }
        
        wins = sum(1 for t in trades if t['win'])
        win_rate = (wins / len(trades)) * 100
        avg_profit = sum(t['pnl_pct'] for t in trades) / len(trades)
        
        # Calculate max drawdown
        cumulative = 0
        peak = 0
        max_drawdown = 0
        for t in trades:
            cumulative += t['pnl_pct']
            peak = max(peak, cumulative)
            drawdown = peak - cumulative
            max_drawdown = max(max_drawdown, drawdown)
        
        return {
            'win_rate': round(win_rate, 1),
            'avg_profit_pct': round(avg_profit, 2),
            'max_drawdown_pct': round(max_drawdown, 2),
            'total_trades': len(trades),
            'winning_trades': wins,
            'losing_trades': len(trades) - wins,
            'backtest_period': f'{len(candles)} candles'
        }


# Singleton instance
pro_trader = ProTrader()
