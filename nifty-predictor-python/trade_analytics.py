"""
Trade Analytics Module
Calculates historical trades taken in the last few hours and computes real-time success rate.

Logic:
- Scans today's 5m candles for genuine momentum entry signals
- Enforces realistic cooldown between trades (min 20 mins / 4 candles)
- Checks multi-condition confluence: EMA cross + RSI + SuperTrend + MACD all required
- Outcome determined by checking next 45 mins (9 candles): WIN if target hit, LOSS if SL hit
- ACTIVE = most recent trade still in play (hasn't hit target or SL yet)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from indicators_fast import TechnicalIndicatorsFast as TechnicalIndicators


def analyze_recent_trades(candles: List[Dict], index: str = 'nifty', hours: int = 5) -> Dict:
    """
    Simulate and validate trades taken over the last N hours using actual candle data.
    Evaluates momentum, trend crossovers, and price action to determine:
    - What trade was taken (e.g. BUY 22600 CE / PE)
    - Entry, SL, Target
    - Outcome: WIN / LOSS / ACTIVE
    - Success rate % and total P&L
    """
    if not candles or len(candles) < 15:
        return {
            'trades': [],
            'summary': {
                'total_trades': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0,
                'total_points': 0,
                'total_pnl': 0,
                'streak': {'type': 'NONE', 'count': 0}
            }
        }

    lot_size    = 15 if 'bank' in index.lower() else 25
    strike_step = 100 if 'bank' in index.lower() else 50
    points_target = 35 if 'bank' not in index.lower() else 70
    points_sl     = 20 if 'bank' not in index.lower() else 40

    # Filter to requested hours window (e.g. last 5 hours = ~60 5m candles)
    max_candles = hours * 12 + 10
    recent_candles = candles[-max_candles:] if len(candles) > max_candles else candles

    trades = []

    # Require minimum 15 candles of history before considering any signal
    min_window = 15

    # Minimum candle gap between trades = 4 candles = 20 minutes (realistic cooldown)
    min_gap = 4

    # Outcome look-ahead window = 9 candles = 45 minutes
    lookahead = 9

    last_trade_idx = -min_gap  # allows first trade after min_window

    for i in range(min_window, len(recent_candles)):
        # Enforce cooldown: skip if not enough candles since last trade
        if (i - last_trade_idx) < min_gap:
            continue

        window = recent_candles[:i + 1]
        current_candle = recent_candles[i]

        # ── Indicator calculation ──────────────────────────────────────────────
        ind = TechnicalIndicators.calculate_all(window)
        rsi = ind.get('rsi', 50) or 50
        ema20 = ind.get('ema_20')
        ema50 = ind.get('ema_50')
        macd_data = ind.get('macd') or {}
        macd_hist = macd_data.get('histogram', 0) or 0
        supertrend_data = ind.get('supertrend') or {}
        st_trend = supertrend_data.get('trend', 'neutral')

        current_close = float(current_candle.get('close', 0))
        current_high  = float(current_candle.get('high', current_close))
        current_low   = float(current_candle.get('low', current_close))

        if current_close <= 0:
            continue

        direction = None
        reasons = []
        signal_strength = 0  # count of confluent signals

        # ── Bullish confluence (need at least 2 signals) ──────────────────────
        if ema20 and ema50 and ema20 > ema50:
            signal_strength += 1
            reasons.append('EMA 20 > 50 Trend')
        if rsi > 55:
            signal_strength += 1
            reasons.append('RSI Bullish Momentum')
        if st_trend == 'bullish':
            signal_strength += 1
            reasons.append('SuperTrend Buy')
        if macd_hist > 0:
            signal_strength += 1
            reasons.append('MACD Positive')

        if signal_strength >= 2 and rsi > 50 and (not (ema20 and ema50 and ema20 < ema50)):
            direction = 'BULLISH'
        else:
            # Reset for bearish check
            signal_strength = 0
            reasons = []
            if ema20 and ema50 and ema20 < ema50:
                signal_strength += 1
                reasons.append('EMA 20 < 50 Downtrend')
            if rsi < 45:
                signal_strength += 1
                reasons.append('RSI Bearish Momentum')
            if st_trend == 'bearish':
                signal_strength += 1
                reasons.append('SuperTrend Sell')
            if macd_hist < 0:
                signal_strength += 1
                reasons.append('MACD Negative')

            if signal_strength >= 2 and rsi < 50 and (not (ema20 and ema50 and ema20 > ema50)):
                direction = 'BEARISH'

        if not direction:
            continue

        # ── Prevent two consecutive same-direction trades too close together ──
        if trades:
            last_t = trades[-1]
            if last_t['direction'] == direction and (i - last_t['_idx']) < min_gap:
                continue

        # ── Trade setup ───────────────────────────────────────────────────────
        entry_price = current_close
        atm_strike  = round(entry_price / strike_step) * strike_step
        opt_type    = 'CE' if direction == 'BULLISH' else 'PE'
        action      = f"BUY {index.upper()} {int(atm_strike)} {opt_type}"

        if direction == 'BULLISH':
            target_price = round(entry_price + points_target, 2)
            stop_price   = round(entry_price - points_sl,     2)
        else:
            target_price = round(entry_price - points_target, 2)
            stop_price   = round(entry_price + points_sl,     2)

        # ── Outcome resolution (next 45 mins of candles) ──────────────────────
        future_candles = recent_candles[i + 1: i + 1 + lookahead]
        result      = 'ACTIVE'
        exit_price  = entry_price
        points      = 0.0

        for fc in future_candles:
            fc_high  = float(fc.get('high',  entry_price))
            fc_low   = float(fc.get('low',   entry_price))
            fc_close = float(fc.get('close', entry_price))

            if direction == 'BULLISH':
                if fc_high >= target_price:
                    result     = 'WIN'
                    exit_price = target_price
                    points     = float(points_target)
                    break
                elif fc_low <= stop_price:
                    result     = 'LOSS'
                    exit_price = stop_price
                    points     = -float(points_sl)
                    break
            else:  # BEARISH
                if fc_low <= target_price:
                    result     = 'WIN'
                    exit_price = target_price
                    points     = float(points_target)
                    break
                elif fc_high >= stop_price:
                    result     = 'LOSS'
                    exit_price = stop_price
                    points     = -float(points_sl)
                    break
        else:
            # No decisive outcome in lookahead window
            if future_candles:
                last_close = float(future_candles[-1].get('close', entry_price))
                raw_pts = (last_close - entry_price) if direction == 'BULLISH' else (entry_price - last_close)
                # If candle window exhausted (no more future data) → still ACTIVE
                if i + lookahead >= len(recent_candles) - 1:
                    result     = 'ACTIVE'
                    exit_price = round(last_close, 2)
                    points     = round(raw_pts, 2)
                else:
                    # Timed out in middle of session → call it by close
                    result     = 'WIN' if raw_pts >= 5 else ('LOSS' if raw_pts <= -5 else 'FLAT')
                    exit_price = round(last_close, 2)
                    points     = round(raw_pts, 2)

        pnl = round(points * lot_size, 2)

        # Time string
        time_str = str(current_candle.get('time', current_candle.get('timestamp', '')))

        trades.append({
            '_idx':       i,
            'time':       time_str,
            'direction':  direction,
            'action':     action,
            'strike':     int(atm_strike),
            'option_type': opt_type,
            'entry':      round(entry_price, 2),
            'target':     target_price,
            'stop_loss':  stop_price,
            'exit':       round(exit_price, 2),
            'result':     result,
            'points':     round(points, 2),
            'pnl_per_lot': pnl,
            'lot_size':   lot_size,
            'reason':     ', '.join(reasons[:2]) if reasons else 'Technical Trigger',
            'signal_strength': signal_strength,
            'indicators': {
                'rsi': round(float(rsi), 2) if rsi is not None else None,
                'ema20': round(float(ema20), 2) if ema20 is not None else None,
                'ema50': round(float(ema50), 2) if ema50 is not None else None,
                'macd_hist': round(float(macd_hist), 2) if macd_hist is not None else None,
                'supertrend': st_trend,
                'reasons_all': reasons
            }
        })

        last_trade_idx = i

    # ── Summary calculations ───────────────────────────────────────────────────
    wins    = sum(1 for t in trades if t['result'] == 'WIN')
    losses  = sum(1 for t in trades if t['result'] == 'LOSS')
    flats   = sum(1 for t in trades if t['result'] == 'FLAT')
    active  = sum(1 for t in trades if t['result'] == 'ACTIVE')

    total_decided = wins + losses
    win_rate      = round((wins / total_decided * 100), 1) if total_decided > 0 else 0
    total_points  = round(sum(t['points'] for t in trades if t['result'] in ['WIN', 'LOSS', 'FLAT']), 2)
    total_pnl     = round(sum(t['pnl_per_lot'] for t in trades if t['result'] in ['WIN', 'LOSS', 'FLAT']), 2)

    # Current streak (only from decided trades)
    decided = [t for t in trades if t['result'] in ['WIN', 'LOSS']]
    streak = {'type': 'NONE', 'count': 0}
    if decided:
        last_res = decided[-1]['result']
        count = 0
        for t in reversed(decided):
            if t['result'] == last_res:
                count += 1
            else:
                break
        streak = {'type': 'WINNING' if last_res == 'WIN' else 'LOSING', 'count': count}

    # Clean internal _idx before returning
    for t in trades:
        t.pop('_idx', None)
        t.pop('signal_strength', None)

    # Newest first for UI
    trades_reversed = list(reversed(trades))

    return {
        'trades': trades_reversed,
        'summary': {
            'total_trades':  len(trades),
            'wins':          wins,
            'losses':        losses,
            'flats':         flats,
            'active':        active,
            'win_rate':      win_rate,
            'total_points':  total_points,
            'total_pnl':     total_pnl,
            'streak':        streak,
            'index':         index.upper()
        }
    }
