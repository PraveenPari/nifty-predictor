"""
Elite Trade Setup Engine — "Buffett-grade" trade forensics.

Discipline borrowed from the greats: only A+ setups get capital, every trade
has a quantified edge, a hard invalidation, and a measured destination.

Provides:
  - Swing detection (scipy.signal.argrelextrema, manual fallback)
  - Auto trendlines: support / resistance / channel with forward projection
  - Projection cone: where price is likely headed + probability + horizon
  - Elite grading: A+ / A / B / C with checklist + position sizing
  - `ta`-library cross-verification (optional, graceful without it)

Pure functions over candle lists — no network, no secrets.
"""

import math
from typing import Dict, List, Optional, Tuple

try:
    import numpy as np
except ImportError:
    np = None

try:
    from scipy.signal import argrelextrema
    SCIPY_XTREMA = True
except ImportError:
    SCIPY_XTREMA = False

# 'ta' technical-analysis package — cross-verification layer (optional)
try:
    import pandas as pd
    import ta as ta_lib
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False
    ta_lib = None


# ---------------------------------------------------------------------------
# Candle helpers
# ---------------------------------------------------------------------------

def _closes(candles: List[Dict]) -> List[float]:
    return [float(c.get('close', 0)) for c in candles]


def _highs(candles: List[Dict]) -> List[float]:
    return [float(c.get('high', 0)) for c in candles]


def _lows(candles: List[Dict]) -> List[float]:
    return [float(c.get('low', 0)) for c in candles]


def _unixtime(c: Dict) -> int:
    v = c.get('timestamp', c.get('time', 0))
    if isinstance(v, (int, float)):
        return int(v // 1000) if v > 1e11 else int(v)
    if isinstance(v, str):
        s = v.strip().replace('Z', '+00:00')
        if s.replace('.', '', 1).isdigit():
            f = float(s)
            return int(f // 1000) if f > 1e11 else int(f)
        try:
            from datetime import datetime
            return int(datetime.fromisoformat(s).timestamp())
        except ValueError:
            pass
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d-%b-%Y %H:%M:%S"):
            try:
                from datetime import datetime
                return int(datetime.strptime(s[:len(fmt)], fmt).timestamp())
            except ValueError:
                continue
    d = c.get('datetime')
    if isinstance(d, str):
        try:
            from datetime import datetime
            return int(datetime.fromisoformat(d.replace('Z', '+00:00')).timestamp())
        except ValueError:
            return 0
    return 0


def atr(candles: List[Dict], period: int = 14) -> float:
    if len(candles) < period + 1:
        return 0.0
    trs = []
    for i in range(1, len(candles)):
        h = float(candles[i]['high']); l = float(candles[i]['low'])
        pc = float(candles[i - 1]['close'])
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(trs[-period:]) / period if trs else 0.0


# ---------------------------------------------------------------------------
# Swing detection
# ---------------------------------------------------------------------------

def find_swings(candles: List[Dict], order: int = 3) -> Dict[str, List[int]]:
    """Indices of swing highs / swing lows."""
    n = len(candles)
    if n < order * 2 + 3:
        return {'highs': [], 'lows': []}
    highs = _highs(candles)
    lows = _lows(candles)
    if SCIPY_XTREMA and np is not None:
        try:
            ha = np.array(highs); la = np.array(lows)
            hi = argrelextrema(ha, np.greater, order=order)[0].tolist()
            lo = argrelextrema(la, np.less, order=order)[0].tolist()
            return {'highs': hi, 'lows': lo}
        except Exception:
            pass
    # Manual fractal fallback
    hi, lo = [], []
    for i in range(order, n - order):
        if highs[i] == max(highs[i - order:i + order + 1]):
            hi.append(i)
        if lows[i] == min(lows[i - order:i + order + 1]):
            lo.append(i)
    return {'highs': hi, 'lows': lo}


def _linfit(xs: List[float], ys: List[float]) -> Tuple[float, float]:
    """Least-squares slope + intercept (no numpy dependency)."""
    n = len(xs)
    if n < 2:
        return 0.0, ys[0] if ys else 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:
        return 0.0, my
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den
    return slope, my - slope * mx


# ---------------------------------------------------------------------------
# Trendlines
# ---------------------------------------------------------------------------

def compute_trendlines(candles: List[Dict], lookback: int = 60,
                       extend_bars: int = 12) -> List[Dict]:
    """
    Auto trendlines from recent swings, extended forward for projection.
    Returns line dicts: {name, color, width, points:[{time,value}], slope_pct,
                         touch_count, broken}
    """
    if not candles or len(candles) < 20:
        return []
    seg = candles[-lookback:]
    offset = len(candles) - len(seg)
    swings = find_swings(seg, order=3)
    n = len(seg)
    closes = _closes(seg)
    last_close = closes[-1]

    # Median bar duration for forward extension
    times = [_unixtime(c) for c in seg]
    step = 300
    diffs = [b - a for a, b in zip(times, times[1:]) if b > a]
    if diffs:
        diffs.sort()
        step = diffs[len(diffs) // 2]

    lines = []

    def build(name: str, idxs: List[int], prices: List[float], color: str):
        pts = sorted(idxs)[-4:]  # last 4 touches max
        if len(pts) < 2:
            # Fallback: anchor on half-segment extremes so a line always exists
            want_min = 'Support' in name
            half = max(1, n // 2)
            first, second = prices[:half], prices[half:]
            i1 = first.index(min(first) if want_min else max(first))
            i2 = half + second.index(min(second) if want_min else max(second))
            pts = [i1, i2] if i1 != i2 else [0, n - 1]
        xs = [float(i) for i in pts]
        ys = [prices[i] for i in pts]
        slope, icept = _linfit(xs, ys)
        # Touches = swings within 0.05% of the line
        line_at = lambda i: slope * i + icept  # noqa: E731
        touches = sum(1 for i in pts if abs(prices[i] - line_at(i)) / max(1, prices[i]) < 0.0005)
        x0, x1 = float(pts[0]), float(n - 1 + extend_bars)
        t0 = times[pts[0]]
        points = [
            {'time': t0, 'value': round(line_at(x0), 2)},
            {'time': times[-1] + int((x1 - (n - 1)) * step), 'value': round(line_at(x1), 2)},
        ]
        broken = (last_close < line_at(n - 1)) if 'Support' in name else (last_close > line_at(n - 1))
        slope_pct = (slope * 20 / last_close * 100) if last_close else 0  # 20-bar move %
        lines.append({
            'name': name, 'color': color, 'width': 2,
            'points': points, 'slope_pct': round(slope_pct, 3),
            'touch_count': touches, 'broken': bool(broken),
            'current_value': round(line_at(n - 1), 2),
            # Bar-relative anchors (frontend draws value = anchor + slope*(bar-anchor_bar))
            'anchor_bar': pts[0] + (len(candles) - n),
            'anchor_value': round(line_at(x0), 2),
            'slope_per_bar': slope,
        })

    build('Support TL ↑', swings['lows'], _lows(seg), '#10b981')
    build('Resistance TL ↓', swings['highs'], _highs(seg), '#f43f5e')
    _ = offset
    return lines


# ---------------------------------------------------------------------------
# 'ta'-package cross-verification (optional)
# ---------------------------------------------------------------------------

def ta_consensus(candles: List[Dict]) -> Dict:
    """
    Independent vote from the `ta` package (RSI / EMA / MACD / ADX / PSAR).
    Returns {available, votes:{bullish,bearish,neutral}, details[]}.
    """
    out = {'available': TA_AVAILABLE, 'votes': {'bullish': 0, 'bearish': 0, 'neutral': 0}, 'details': []}
    if not TA_AVAILABLE or len(candles) < 60:
        return out
    try:
        df = pd.DataFrame({
            'Open': [float(c['open']) for c in candles],
            'High': [float(c['high']) for c in candles],
            'Low': [float(c['low']) for c in candles],
            'Close': [float(c['close']) for c in candles],
            'Volume': [float(c.get('volume', 0)) for c in candles],
        })
        close = df['Close']
        votes = out['votes']

        def vote(bull: Optional[bool], label: str, val: str):
            if bull is None:
                votes['neutral'] += 1
                out['details'].append(f"{label}: neutral ({val})")
            elif bull:
                votes['bullish'] += 1
                out['details'].append(f"{label}: BULL ({val})")
            else:
                votes['bearish'] += 1
                out['details'].append(f"{label}: BEAR ({val})")

        rsi = float(ta_lib.momentum.RSIIndicator(close, 14).rsi().iloc[-1])
        vote(rsi > 55 if (rsi >= 45 or rsi >= 55) else None if 45 <= rsi <= 55 else rsi > 50,
             'ta-RSI14', f"{rsi:.1f}")
        ema9 = float(ta_lib.trend.EMAIndicator(close, 9).ema_indicator().iloc[-1])
        ema21 = float(ta_lib.trend.EMAIndicator(close, 21).ema_indicator().iloc[-1])
        vote(close.iloc[-1] > ema9 > ema21, 'ta-EMA9/21', f"{ema9:.0f}/{ema21:.0f}")
        macd = ta_lib.trend.MACD(close)
        vote(float(macd.macd_diff().iloc[-1]) > 0, 'ta-MACD',
             f"hist {float(macd.macd_diff().iloc[-1]):.2f}")
        try:
            adx_v = float(ta_lib.trend.ADXIndicator(df['High'], df['Low'], close, 14).adx().iloc[-1])
            pdi = float(ta_lib.trend.ADXIndicator(df['High'], df['Low'], close, 14).adx_pos().iloc[-1])
            mdi = float(ta_lib.trend.ADXIndicator(df['High'], df['Low'], close, 14).adx_neg().iloc[-1])
            vote(pdi > mdi if adx_v >= 18 else None, 'ta-ADX14', f"{adx_v:.0f} +{pdi:.0f}/-{mdi:.0f}")
        except Exception:
            votes['neutral'] += 1
        try:
            psar = ta_lib.trend.PSARIndicator(df['High'], df['Low'], close)
            psar_v = float(psar.psar().iloc[-1])
            vote(close.iloc[-1] > psar_v, 'ta-PSAR', f"{psar_v:.0f}")
        except Exception:
            votes['neutral'] += 1
    except Exception as e:
        out['details'].append(f"ta engine error: {e}")
    return out


# ---------------------------------------------------------------------------
# Projection — "where it will go"
# ---------------------------------------------------------------------------

def build_projection(candles: List[Dict], direction: str, entry: float,
                     stop_loss: float, target: float,
                     trendlines: Optional[List[Dict]] = None) -> Dict:
    """Measured-move projection cone + probability + invalidation."""
    a = atr(candles) or entry * 0.002
    risk = abs(entry - stop_loss) if stop_loss else a
    reward = abs(target - entry) if target else 2 * a
    rr = round(reward / risk, 2) if risk > 0 else 0

    if direction == 'BULLISH':
        zone = [round(target - 0.4 * a, 2), round(target + 0.6 * a, 2)]
    elif direction == 'BEARISH':
        zone = [round(target - 0.6 * a, 2), round(target + 0.4 * a, 2)]
    else:
        zone = [round(entry - a, 2), round(entry + a, 2)]

    # Probability from structure: RR quality + trendline confluence + ATR room
    prob = 50
    prob += min(12, max(0, int((rr - 1.0) * 10)))          # RR 1→3 adds up to +20→cap 12
    tl_note = None
    if trendlines:
        for tl in trendlines:
            dist_pct = abs(tl['current_value'] - entry) / entry * 100 if entry else 9
            if dist_pct < 0.3 and not tl['broken']:
                prob += 6
                tl_note = f"Confluence: {tl['name']} @ {tl['current_value']} ({tl['touch_count']} touches)"
                break
            if tl['broken'] and (('Support' in tl['name'] and direction == 'BEARISH') or
                                 ('Resistance' in tl['name'] and direction == 'BULLISH')):
                prob += 5
                tl_note = f"Momentum: {tl['name']} broken — measured move active"
                break
    prob = max(5, min(92, prob))

    reasoning = [
        f"Measured move: entry {entry:.2f} → zone {zone[0]:.2f}–{zone[1]:.2f} ({abs(zone[1]-zone[0])/a:.1f}× ATR {a:.1f})",
        f"Risk-Reward 1:{rr} — {'ACCEPTABLE' if rr >= 1.5 else 'THIN — reduce size or skip'}",
    ]
    if tl_note:
        reasoning.append(tl_note)
    reasoning.append(f"Invalidation: {'SL ' + str(round(stop_loss, 2)) + ' (hard exit, no averaging)'}")

    return {
        'direction': direction,
        'target_zone': zone,
        'probability': prob,
        'horizon': '3–9 bars (15–45 min on 5m)',
        'atr': round(a, 2),
        'risk_reward': rr,
        'invalidation': round(stop_loss, 2),
        'reasoning': reasoning,
    }


# ---------------------------------------------------------------------------
# Elite grading — Buffett discipline
# ---------------------------------------------------------------------------

def grade_setup(checklist: List[Dict], risk_reward: float,
                ta_votes: Optional[Dict] = None) -> Dict:
    """
    Grade A+ / A / B / C from a checklist of {label, passed, weight}.
    Buffett rule: only A/A+ get full size; C = no trade.
    """
    if ta_votes and ta_votes.get('available'):
        v = ta_votes['votes']
        total = v['bullish'] + v['bearish'] + v['neutral']
        if total:
            dom = max(v, key=v.get)
            agree = v[dom] / total
            checklist = checklist + [{
                'label': f"ta-package cross-check: {dom} {agree:.0%}",
                'passed': agree >= 0.6 and dom != 'neutral',
                'weight': 1.5,
            }]
    earned = sum(c.get('weight', 1) for c in checklist if c.get('passed'))
    total_w = sum(c.get('weight', 1) for c in checklist) or 1
    score = round(earned / total_w * 100)

    if risk_reward < 1.5:
        score = min(score, 64)  # hard penalty: thin RR can never be elite
        rr_note = "CAPPED: RR below 1.5 — never elite"
    else:
        rr_note = f"RR 1:{risk_reward} clears the 1.5 bar"

    if score >= 85:
        grade, size, verdict = 'A+', 'FULL size (2% risk)', 'TAKE THE TRADE'
    elif score >= 70:
        grade, size, verdict = 'A', 'Standard size (1% risk)', 'TAKE THE TRADE'
    elif score >= 55:
        grade, size, verdict = 'B', 'Half size (0.5% risk)', 'TAKE REDUCED / WAIT FOR TRIGGER'
    else:
        grade, size, verdict = 'C', 'NO position', 'SKIP — capital preserved is capital earned'

    if grade == 'C':
        verdict += " · Buffett rule #1: never lose money. Rule #2: never forget rule #1."

    return {
        'grade': grade, 'score': score, 'position_size': size, 'verdict': verdict,
        'checklist': [{'label': c['label'], 'passed': bool(c.get('passed'))} for c in checklist],
        'rr_note': rr_note,
    }


def build_checklist(direction: str, price: float, indicators: Dict,
                    sentiment: Optional[Dict], regime: str,
                    supports: List[float], resistances: List[float]) -> List[Dict]:
    """8-point elite checklist from live indicators."""
    adx = (indicators.get('adx') or {})
    adx_v = adx.get('adx', 0) or 0
    pdi, mdi = adx.get('plus_di', 0) or 0, adx.get('minus_di', 0) or 0
    st = (indicators.get('supertrend') or {}).get('trend', '')
    rsi = indicators.get('rsi') or 50
    macd_h = (indicators.get('macd') or {}).get('histogram', 0) or 0
    ema9, ema21 = indicators.get('ema_9'), indicators.get('ema_21')
    vwap = indicators.get('vwap')
    is_bull = direction == 'BULLISH'

    def near(levels):
        return any(abs(price - lv) / price * 100 < 0.35 for lv in levels) if levels else False

    return [
        {'label': f"Trend: ADX {adx_v:.0f} + {'+DI' if is_bull else '−DI'} dominant",
         'passed': adx_v >= 18 and ((pdi > mdi) if is_bull else (mdi > pdi)), 'weight': 2},
        {'label': f"SuperTrend {st or '?'} aligned {direction}",
         'passed': (st == 'bullish') == is_bull and bool(st), 'weight': 1.5},
        {'label': f"Momentum: RSI {rsi:.0f} + MACD hist {macd_h:+.1f}",
         'passed': ((rsi > 50 and macd_h > 0) if is_bull else (rsi < 50 and macd_h < 0)), 'weight': 1.5},
        {'label': f"EMA ribbon stacked {'9>21, price above' if is_bull else '9<21, price below'}",
         'passed': bool(ema9 and ema21) and (((ema9 > ema21) and price > ema9) if is_bull else ((ema9 < ema21) and price < ema9)),
         'weight': 1.5},
        {'label': f"VWAP side: price {'above' if (vwap and price > vwap) else 'below'} institutional line",
         'passed': bool(vwap) and ((price > vwap) if is_bull else (price < vwap)), 'weight': 1},
        {'label': f"S/R confluence near {'support' if is_bull else 'resistance'}",
         'passed': near(supports if is_bull else resistances), 'weight': 1.5},
        {'label': f"Regime {regime} tradable (not chop)",
         'passed': regime in ('TRENDING', 'TRANSITION'), 'weight': 1},
        {'label': f"Sentiment not fighting (VIX {(sentiment or {}).get('vix', '?')}, PCR {(sentiment or {}).get('pcr', '?')})",
         'passed': ((sentiment or {}).get('vix', 14) or 14) < 24, 'weight': 1},
    ]


def position_sizer(capital: float, risk_pct: float, entry: float,
                   stop_loss: float, lot_size: int,
                   option_premium: float = 0) -> Dict:
    """Fixed-fractional sizing with lot rounding."""
    risk_rs = capital * risk_pct / 100
    per_unit = abs(entry - stop_loss) if not option_premium else option_premium * 0.4
    per_unit = per_unit or 1
    qty = int(risk_rs / per_unit)
    lots = max(1, qty // lot_size) if lot_size else 1
    return {
        'capital': capital, 'risk_pct': risk_pct, 'risk_rupees': round(risk_rs, 2),
        'per_unit_risk': round(per_unit, 2), 'lots': lots, 'qty': lots * lot_size,
        'max_loss': round(lots * lot_size * per_unit, 2),
    }
