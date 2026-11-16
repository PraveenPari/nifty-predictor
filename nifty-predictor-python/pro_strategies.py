"""
Pro Strategies Module — institutional-grade intraday strategies.

Unlike the 18 classic indicator strategies in strategies.py, these combine
PRICE ACTION + VOLATILITY + VOLUME + OPTION-CHAIN positioning, and every
signal ships with entry / stop-loss / target levels so it is directly
tradeable.

Each strategy returns:
    {name, category='pro', signal, strength, reason,
     entry, stop_loss, target, timeframe, tags}
"""

from typing import Dict, List, Optional
from datetime import datetime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _result(name: str, signal: str, strength: int, reason: str,
            entry: Optional[float] = None,
            stop_loss: Optional[float] = None,
            target: Optional[float] = None,
            timeframe: str = "15m intraday",
            tags: Optional[List[str]] = None) -> Dict:
    out = {
        'name': name,
        'category': 'pro',
        'signal': signal,
        'strength': max(0, min(100, int(strength))),
        'reason': reason,
        'timeframe': timeframe,
        'tags': tags or [],
    }
    if entry is not None:
        out['entry'] = round(entry, 2)
    if stop_loss is not None:
        out['stop_loss'] = round(stop_loss, 2)
    if target is not None:
        out['target'] = round(target, 2)
    return out


def _neutral(name: str, reason: str, tags=None) -> Dict:
    return _result(name, 'neutral', 50, reason, tags=tags or [])


def _candle_ts(c: Dict):
    """Best-effort timestamp extraction across Breeze/Yahoo/simulator formats."""
    for key in ('timestamp', 'time', 'datetime'):
        if key in c and c[key]:
            v = c[key]
            if isinstance(v, (int, float)):
                try:
                    return datetime.fromtimestamp(v)
                except (OverflowError, OSError, ValueError):
                    continue
            if isinstance(v, str):
                s = v.strip().replace('Z', '+00:00')
                try:
                    return datetime.fromisoformat(s)
                except ValueError:
                    pass
                for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
                            "%d-%b-%Y %H:%M:%S", "%Y-%m-%d"):
                    try:
                        return datetime.strptime(s[:len(fmt)], fmt)
                    except ValueError:
                        continue
    return None


def _today_session(candles: List[Dict]) -> List[Dict]:
    """Candles from the latest trading session in the data."""
    if not candles:
        return []
    day_groups = {}
    undated = []
    for c in candles:
        ts = _candle_ts(c)
        if ts is None:
            undated.append(c)
        else:
            day_groups.setdefault(ts.date(), []).append(c)
    if day_groups:
        latest = max(day_groups.keys())
        return day_groups[latest]
    return undated[-78:] if len(undated) > 78 else undated  # ~1 session of 5m bars


def _atr_value(indicators: Dict, candles: List[Dict], price: float) -> float:
    atr = indicators.get('atr')
    if atr:
        return float(atr)
    if len(candles) >= 15:
        trs = []
        for i in range(-15, 0):
            c = candles[i]
            p = candles[i - 1]
            trs.append(max(c['high'] - c['low'],
                           abs(c['high'] - p['close']),
                           abs(c['low'] - p['close'])))
        return sum(trs) / len(trs)
    return price * 0.002  # ~0.2% fallback


def _targets(price: float, atr: float, direction: str,
             sl_mult: float = 1.0, tp_mult: float = 2.0):
    if direction == 'bullish':
        return price, price - sl_mult * atr, price + tp_mult * atr
    if direction == 'bearish':
        return price, price + sl_mult * atr, price - tp_mult * atr
    return price, price - sl_mult * atr, price + tp_mult * atr


# ---------------------------------------------------------------------------
# 1. Opening Range Breakout (ORB-15)
# ---------------------------------------------------------------------------

def orb_strategy(candles: List[Dict], price: float) -> Dict:
    name = "ORB-15 Breakout"
    session = _today_session(candles)
    if len(session) < 6:
        return _neutral(name, "Need 6+ candles of today's session for opening range",
                        tags=["breakout", "intraday"])
    orb_high = max(c['high'] for c in session[:3])
    orb_low = min(c['low'] for c in session[:3])
    orb_mid = (orb_high + orb_low) / 2
    orb_range = orb_high - orb_low
    if orb_range <= 0:
        return _neutral(name, "Opening range not formed yet", tags=["breakout"])
    buf = orb_range * 0.1
    if price > orb_high + buf:
        return _result(name, 'bullish', 82,
                       f"Price {price:.0f} broke ORB high {orb_high:.0f} (+buffer) — momentum long",
                       price, orb_mid, price + 1.5 * orb_range,
                       tags=["breakout", "momentum"])
    if price < orb_low - buf:
        return _result(name, 'bearish', 82,
                       f"Price {price:.0f} broke ORB low {orb_low:.0f} (−buffer) — momentum short",
                       price, orb_mid, price - 1.5 * orb_range,
                       tags=["breakout", "momentum"])
    pos = "upper half" if price > orb_mid else "lower half"
    return _neutral(name, f"Inside opening range {orb_low:.0f}–{orb_high:.0f} ({pos}) — wait for break",
                    tags=["breakout"])


# ---------------------------------------------------------------------------
# 2. VWAP Bounce / Rejection
# ---------------------------------------------------------------------------

def vwap_pro_strategy(indicators: Dict, candles: List[Dict], price: float) -> Dict:
    name = "VWAP Institutional Bias"
    vwap = indicators.get('vwap')
    if not vwap:
        return _neutral(name, "VWAP unavailable", tags=["vwap"])
    atr = _atr_value(indicators, candles, price)
    dist_pct = (price - vwap) / vwap * 100
    tol = max(atr * 0.15, price * 0.0003)
    if abs(price - vwap) <= tol:
        return _neutral(name, f"Price riding VWAP {vwap:.0f} — no edge, wait for rejection/acceptance",
                        tags=["vwap"])
    if price > vwap:
        e, s, t = _targets(price, atr, 'bullish', 0.8, 1.5)
        strength = min(85, 62 + int(abs(dist_pct) * 12))
        return _result(name, 'bullish', strength,
                       f"Above VWAP {vwap:.0f} ({dist_pct:+.2f}%) — institutions buying dips; SL under VWAP",
                       e, min(s, vwap - tol), t, tags=["vwap", "trend"])
    e, s, t = _targets(price, atr, 'bearish', 0.8, 1.5)
    strength = min(85, 62 + int(abs(dist_pct) * 12))
    return _result(name, 'bearish', strength,
                   f"Below VWAP {vwap:.0f} ({dist_pct:+.2f}%) — institutions selling rallies; SL over VWAP",
                   e, max(s, vwap + tol), t, tags=["vwap", "trend"])


# ---------------------------------------------------------------------------
# 3. EMA 9/21 Momentum Ribbon
# ---------------------------------------------------------------------------

def ema_ribbon_strategy(indicators: Dict, candles: List[Dict], price: float) -> Dict:
    name = "EMA 9/21 Ribbon"
    ema9 = indicators.get('ema_9')
    ema21 = indicators.get('ema_21')
    ema50 = indicators.get('ema_50')
    if ema9 is None or ema21 is None:
        return _neutral(name, "EMA 9/21 unavailable", tags=["trend"])
    atr = _atr_value(indicators, candles, price)
    if ema9 > ema21 and price > ema9:
        stacked = ema50 is not None and ema21 > ema50
        e, s, t = _targets(price, atr, 'bullish', 1.0, 2.0)
        return _result(name, 'bullish', 84 if stacked else 72,
                       f"Bull stack 9>21{'>50' if stacked else ''}, price above ribbon — buy pullbacks to EMA9 {ema9:.0f}",
                       e, s, t, tags=["trend", "momentum"])
    if ema9 < ema21 and price < ema9:
        stacked = ema50 is not None and ema21 < ema50
        e, s, t = _targets(price, atr, 'bearish', 1.0, 2.0)
        return _result(name, 'bearish', 84 if stacked else 72,
                       f"Bear stack 9<21{'<50' if stacked else ''}, price below ribbon — sell rallies to EMA9 {ema9:.0f}",
                       e, s, t, tags=["trend", "momentum"])
    return _neutral(name, "EMA ribbon flat/crossed — chop zone, stand aside", tags=["trend"])


# ---------------------------------------------------------------------------
# 4. SuperTrend + ADX Confluence (false-signal filter)
# ---------------------------------------------------------------------------

def supertrend_adx_strategy(indicators: Dict, candles: List[Dict], price: float) -> Dict:
    name = "SuperTrend × ADX Filter"
    st = indicators.get('supertrend') or {}
    adx = indicators.get('adx') or {}
    if not st or not adx:
        return _neutral(name, "SuperTrend/ADX unavailable", tags=["trend"])
    adx_v = adx.get('adx', 0)
    pdi = adx.get('plus_di', 0)
    mdi = adx.get('minus_di', 0)
    atr = _atr_value(indicators, candles, price)
    trend = st.get('trend', 'bullish')
    if trend == 'bullish' and adx_v >= 20 and pdi > mdi:
        e, s, t = _targets(price, atr, 'bullish', 1.2, 2.2)
        return _result(name, 'bullish', min(90, 68 + int((adx_v - 20) / 2)),
                       f"SuperTrend UP + ADX {adx_v:.0f} (+DI>{'−DI'}) — trend confirmed",
                       e, s, t, tags=["trend", "filter"])
    if trend == 'bearish' and adx_v >= 20 and mdi > pdi:
        e, s, t = _targets(price, atr, 'bearish', 1.2, 2.2)
        return _result(name, 'bearish', min(90, 68 + int((adx_v - 20) / 2)),
                       f"SuperTrend DOWN + ADX {adx_v:.0f} (−DI>+DI) — trend confirmed",
                       e, s, t, tags=["trend", "filter"])
    return _neutral(name, f"SuperTrend {trend} but ADX {adx_v:.0f} weak/mismatched — filtered, no trade",
                    tags=["trend", "filter"])


# ---------------------------------------------------------------------------
# 5. Bollinger Squeeze Breakout
# ---------------------------------------------------------------------------

def bb_squeeze_strategy(indicators: Dict, candles: List[Dict], price: float) -> Dict:
    name = "Bollinger Squeeze Breakout"
    bb = indicators.get('bollinger')
    if not bb or len(candles) < 25:
        return _neutral(name, "Need 25+ candles for squeeze percentile", tags=["volatility"])
    closes = [c['close'] for c in candles[-25:]]
    widths = []
    for i in range(20, 25):
        w = closes[i]
        window = closes[i - 20:i]
        mean = sum(window) / 20
        var = sum((x - mean) ** 2 for x in window) / 20
        widths.append((var ** 0.5) / mean * 100 * 2)
    cur_bw = bb.get('bandwidth', widths[-1])
    pct = sum(1 for w in widths if cur_bw <= w) / len(widths) * 100
    atr = _atr_value(indicators, candles, price)
    squeezing = pct >= 60
    if price >= bb['upper'] and not squeezing:
        e, s, t = _targets(price, atr, 'bullish', 1.0, 2.0)
        return _result(name, 'bullish', 76,
                       f"Breakout above upper band {bb['upper']:.0f} with expansion — ride momentum",
                       e, s, t, tags=["volatility", "breakout"])
    if price <= bb['lower'] and not squeezing:
        e, s, t = _targets(price, atr, 'bearish', 1.0, 2.0)
        return _result(name, 'bearish', 76,
                       f"Breakdown below lower band {bb['lower']:.0f} with expansion — ride momentum",
                       e, s, t, tags=["volatility", "breakout"])
    if squeezing:
        return _neutral(name, f"SQUEEZE ON — bandwidth {cur_bw:.2f}% in tightest {100 - pct:.0f}% — coil for breakout, don't fade",
                        tags=["volatility"])
    return _neutral(name, f"Bands normal width ({cur_bw:.2f}%) — no squeeze edge", tags=["volatility"])


# ---------------------------------------------------------------------------
# 6. Donchian 20 Breakout
# ---------------------------------------------------------------------------

def donchian_strategy(indicators: Dict, candles: List[Dict], price: float) -> Dict:
    name = "Donchian 20 Breakout"
    dc = indicators.get('donchian')
    if not dc:
        return _neutral(name, "Donchian channel unavailable", tags=["breakout"])
    atr = _atr_value(indicators, candles, price)
    if price > dc['upper']:
        e, s, t = _targets(price, atr, 'bullish', 1.0, 2.0)
        return _result(name, 'bullish', 80,
                       f"20-bar HIGH breakout {dc['upper']:.0f} — turtle-style long, SL at mid {dc['middle']:.0f}",
                       e, min(s, dc['middle']), t, tags=["breakout"])
    if price < dc['lower']:
        e, s, t = _targets(price, atr, 'bearish', 1.0, 2.0)
        return _result(name, 'bearish', 80,
                       f"20-bar LOW breakdown {dc['lower']:.0f} — turtle-style short, SL at mid {dc['middle']:.0f}",
                       e, max(s, dc['middle']), t, tags=["breakout"])
    return _neutral(name, f"Inside Donchian {dc['lower']:.0f}–{dc['upper']:.0f} — wait for 20-bar break",
                    tags=["breakout"])


# ---------------------------------------------------------------------------
# 7. Keltner + Volume Thrust
# ---------------------------------------------------------------------------

def keltner_strategy(indicators: Dict, candles: List[Dict], price: float) -> Dict:
    name = "Keltner Volume Thrust"
    kc = indicators.get('keltner')
    if not kc or len(candles) < 20:
        return _neutral(name, "Keltner/volume data unavailable", tags=["breakout"])
    vols = [c.get('volume', 0) for c in candles[-20:]]
    avg_vol = sum(vols[:-1]) / max(1, len(vols) - 1)
    thrust = avg_vol > 0 and vols[-1] > avg_vol * 1.5
    atr = _atr_value(indicators, candles, price)
    if price > kc['upper']:
        e, s, t = _targets(price, atr, 'bullish', 1.0, 1.8)
        return _result(name, 'bullish', 83 if thrust else 64,
                       f"Above Keltner upper {kc['upper']:.0f}{' + VOLUME THRUST' if thrust else ' (thin volume — weak)'}",
                       e, s, t, tags=["breakout", "volume"])
    if price < kc['lower']:
        e, s, t = _targets(price, atr, 'bearish', 1.0, 1.8)
        return _result(name, 'bearish', 83 if thrust else 64,
                       f"Below Keltner lower {kc['lower']:.0f}{' + VOLUME THRUST' if thrust else ' (thin volume — weak)'}",
                       e, s, t, tags=["breakout", "volume"])
    return _neutral(name, f"Inside Keltner {kc['lower']:.0f}–{kc['upper']:.0f} — mean-reversion zone, no thrust",
                    tags=["breakout"])


# ---------------------------------------------------------------------------
# 8. ATR Trailing Stop Signal
# ---------------------------------------------------------------------------

def atr_trailing_strategy(indicators: Dict, candles: List[Dict], price: float) -> Dict:
    name = "ATR Chandelier Signal"
    if len(candles) < 22:
        return _neutral(name, "Need 22+ candles for Chandelier stop", tags=["trend"])
    atr = _atr_value(indicators, candles, price)
    swing_high = max(c['high'] for c in candles[-22:-1])
    swing_low = min(c['low'] for c in candles[-22:-1])
    long_stop = swing_high - 3 * atr
    short_stop = swing_low + 3 * atr
    if price > long_stop and price > candles[-2]['close']:
        return _result(name, 'bullish', 74,
                       f"Holding above Chandelier long-stop {long_stop:.0f} (22-bar high − 3×ATR) — stay long",
                       price, long_stop, price + 2 * atr, tags=["trend", "risk"])
    if price < short_stop and price < candles[-2]['close']:
        return _result(name, 'bearish', 74,
                       f"Holding below Chandelier short-stop {short_stop:.0f} (22-bar low + 3×ATR) — stay short",
                       price, short_stop, price - 2 * atr, tags=["trend", "risk"])
    return _neutral(name, "Chandelier flip zone — trend in transition, reduce size", tags=["trend", "risk"])


# ---------------------------------------------------------------------------
# 9. OBV Confirmation
# ---------------------------------------------------------------------------

def obv_strategy(indicators: Dict, candles: List[Dict], price: float) -> Dict:
    name = "OBV Smart-Money Check"
    if len(candles) < 25:
        return _neutral(name, "Need 25+ candles for OBV slope", tags=["volume"])
    closes = [c['close'] for c in candles[-25:]]
    vols = [c.get('volume', 0) for c in candles[-25:]]
    obv = 0.0
    obv_series = []
    for i in range(1, len(closes)):
        if closes[i] > closes[i - 1]:
            obv += vols[i]
        elif closes[i] < closes[i - 1]:
            obv -= vols[i]
        obv_series.append(obv)
    obv_now, obv_prev = obv_series[-1], obv_series[-6]
    price_up = closes[-1] > closes[-6]
    obv_up = obv_now > obv_prev
    atr = _atr_value(indicators, candles, price)
    if price_up and obv_up:
        e, s, t = _targets(price, atr, 'bullish', 1.0, 1.8)
        return _result(name, 'bullish', 72,
                       "Rally CONFIRMED by rising OBV — smart money accumulating",
                       e, s, t, tags=["volume"])
    if not price_up and not obv_up:
        e, s, t = _targets(price, atr, 'bearish', 1.0, 1.8)
        return _result(name, 'bearish', 72,
                       "Decline CONFIRMED by falling OBV — distribution in progress",
                       e, s, t, tags=["volume"])
    div = "bullish divergence (price down, OBV up)" if obv_up else "bearish divergence (price up, OBV down)"
    return _result(name, 'bullish' if obv_up else 'bearish', 60,
                   f"OBV DIVERGENCE: {div} — early reversal warning, wait for price confirmation",
                   price, price - atr if obv_up else price + atr,
                   price + 1.5 * atr if obv_up else price - 1.5 * atr,
                   tags=["volume", "divergence"])


# ---------------------------------------------------------------------------
# 10. RSI Divergence Pro
# ---------------------------------------------------------------------------

def rsi_divergence_strategy(indicators: Dict, candles: List[Dict], price: float) -> Dict:
    name = "RSI Divergence Pro"
    rsi_hist = indicators.get('rsi_history') or []
    if len(rsi_hist) < 20 or len(candles) < 20:
        return _neutral(name, "Need 20+ bars of RSI history", tags=["divergence"])
    closes = [c['close'] for c in candles[-len(rsi_hist):]]
    # swing lows: price makes lower low while RSI makes higher low
    p1, p2 = min(closes[-14:-7]), min(closes[-7:])
    r1 = min(rsi_hist[-14:-7])
    r2 = min(rsi_hist[-7:])
    q1, q2 = max(closes[-14:-7]), max(closes[-7:])
    s1 = max(rsi_hist[-14:-7])
    s2 = max(rsi_hist[-7:])
    atr = _atr_value(indicators, candles, price)
    if p2 < p1 and r2 > r1:
        e, s, t = _targets(price, atr, 'bullish', 1.0, 2.0)
        return _result(name, 'bullish', 78,
                       f"BULLISH RSI divergence: lower low {p2:.0f} vs {p1:.0f} but RSI {r2:.0f} vs {r1:.0f} — momentum turning",
                       e, s, t, tags=["divergence", "reversal"])
    if q2 > q1 and s2 < s1:
        e, s, t = _targets(price, atr, 'bearish', 1.0, 2.0)
        return _result(name, 'bearish', 78,
                       f"BEARISH RSI divergence: higher high {q2:.0f} vs {q1:.0f} but RSI {s2:.0f} vs {s1:.0f} — momentum fading",
                       e, s, t, tags=["divergence", "reversal"])
    return _neutral(name, "No RSI divergence — momentum aligned with price", tags=["divergence"])


# ---------------------------------------------------------------------------
# 11. Max-OI Support / Resistance (option chain)
# ---------------------------------------------------------------------------

def max_oi_levels_strategy(option_chain: Optional[List[Dict]], price: float) -> Dict:
    name = "Max-OI Support/Resistance"
    if not option_chain:
        return _neutral(name, "Option chain unavailable — no OI levels", tags=["options", "oi"])
    pe_rows = [(r.get('pe_oi', 0), r['strike']) for r in option_chain if r.get('strike')]
    ce_rows = [(r.get('ce_oi', 0), r['strike']) for r in option_chain if r.get('strike')]
    if not pe_rows or max(pe_rows)[0] <= 0:
        return _neutral(name, "OI data empty in chain", tags=["options", "oi"])
    support = max(pe_rows)[1]      # max put OI = support
    resistance = max(ce_rows)[1]   # max call OI = resistance
    dist_s = (price - support) / price * 100
    dist_r = (resistance - price) / price * 100
    if abs(dist_s) < 0.25:
        return _result(name, 'bullish', 74,
                       f"Price {price:.0f} AT max-Put-OI support {support:.0f} — writers defend, bounce likely",
                       price, support * 0.997, price + (resistance - price) * 0.5,
                       tags=["options", "oi", "support"])
    if abs(dist_r) < 0.25:
        return _result(name, 'bearish', 74,
                       f"Price {price:.0f} AT max-Call-OI resistance {resistance:.0f} — writers cap, rejection likely",
                       price, resistance * 1.003, price - (price - support) * 0.5,
                       tags=["options", "oi", "resistance"])
    mid = "upper half" if price > (support + resistance) / 2 else "lower half"
    return _neutral(name, f"OI range {support:.0f}–{resistance:.0f} ({mid}) — trade the edges, not the middle",
                    tags=["options", "oi"])


# ---------------------------------------------------------------------------
# 12. Max Pain Magnet
# ---------------------------------------------------------------------------

def max_pain_strategy(option_chain: Optional[List[Dict]], price: float) -> Dict:
    name = "Max-Pain Magnet"
    if not option_chain:
        return _neutral(name, "Option chain unavailable", tags=["options", "expiry"])
    strikes = sorted(r['strike'] for r in option_chain if r.get('strike'))
    if len(strikes) < 3:
        return _neutral(name, "Too few strikes for max pain", tags=["options"])
    best, best_pain = strikes[0], float('inf')
    for s in strikes:
        pain = 0.0
        for r in option_chain:
            k = r['strike']
            pain += max(0.0, s - k) * r.get('pe_oi', 0) + max(0.0, k - s) * r.get('ce_oi', 0)
        if pain < best_pain:
            best_pain, best = pain, s
    dist_pct = (best - price) / price * 100
    if abs(dist_pct) < 0.15:
        return _neutral(name, f"Price pinned AT max pain {best:.0f} — expiry gravity, avoid fresh directional bets",
                        tags=["options", "expiry"])
    direction = 'bullish' if dist_pct > 0 else 'bearish'
    move = abs(best - price)
    return _result(name, direction, 62,
                   f"Max pain {best:.0f} is {dist_pct:+.2f}% away — expiry drift pulls toward {best:.0f}",
                   price,
                   price - move * 0.5 if direction == 'bullish' else price + move * 0.5,
                   best, timeframe="expiry drift", tags=["options", "expiry"])


# ---------------------------------------------------------------------------
# 13. PCR Extreme Pro (with VIX regime filter)
# ---------------------------------------------------------------------------

def pcr_pro_strategy(sentiment: Optional[Dict]) -> Dict:
    name = "PCR Extreme + VIX Regime"
    if not sentiment:
        return _neutral(name, "Sentiment data unavailable", tags=["options", "sentiment"])
    pcr = sentiment.get('pcr', 1.0)
    vix = sentiment.get('vix', 14)
    if vix > 22:
        return _neutral(name, f"VIX {vix:.1f} panic regime — extremes unreliable, cut size / stay out",
                        tags=["options", "vix"])
    if pcr >= 1.4:
        return _result(name, 'bullish', 75,
                       f"PCR {pcr:.2f} extreme fear (heavy put writing) + VIX {vix:.1f} calm — contrarian bounce setup",
                       tags=["options", "contrarian"])
    if pcr <= 0.7:
        return _result(name, 'bearish', 75,
                       f"PCR {pcr:.2f} extreme greed (heavy call writing) — contrarian pullback setup",
                       tags=["options", "contrarian"])
    lean = "mildly bullish" if pcr > 1.05 else ("mildly bearish" if pcr < 0.95 else "neutral")
    return _neutral(name, f"PCR {pcr:.2f} {lean}, VIX {vix:.1f} — no positioning extreme", tags=["options"])


# ---------------------------------------------------------------------------
# 14. Heikin-Ashi Trend State
# ---------------------------------------------------------------------------

def heikin_ashi_strategy(indicators: Dict, candles: List[Dict], price: float) -> Dict:
    name = "Heikin-Ashi Trend State"
    ha = indicators.get('heikin_ashi')
    if not ha:
        return _neutral(name, "Heikin-Ashi unavailable", tags=["trend"])
    atr = _atr_value(indicators, candles, price)
    trend = ha.get('trend', 'doji')
    if trend == 'strong_bullish':
        e, s, t = _targets(price, atr, 'bullish', 1.0, 2.0)
        return _result(name, 'bullish', 80, "HA strong uptrend (no lower wicks) — hold longs, trail stops",
                       e, s, t, tags=["trend"])
    if trend == 'strong_bearish':
        e, s, t = _targets(price, atr, 'bearish', 1.0, 2.0)
        return _result(name, 'bearish', 80, "HA strong downtrend (no upper wicks) — hold shorts, trail stops",
                       e, s, t, tags=["trend"])
    if trend == 'bullish':
        e, s, t = _targets(price, atr, 'bullish', 1.0, 1.5)
        return _result(name, 'bullish', 62, "HA uptrend weakening (wicks appearing) — book partials",
                       e, s, t, tags=["trend"])
    if trend == 'bearish':
        e, s, t = _targets(price, atr, 'bearish', 1.0, 1.5)
        return _result(name, 'bearish', 62, "HA downtrend weakening (wicks appearing) — book partials",
                       e, s, t, tags=["trend"])
    return _neutral(name, "HA doji/indecision — trend changing hands, wait", tags=["trend"])


# ---------------------------------------------------------------------------
# 15. Pivot Confluence (price + pivots + VWAP)
# ---------------------------------------------------------------------------

def pivot_confluence_strategy(indicators: Dict, price: float) -> Dict:
    name = "Pivot + VWAP Confluence"
    piv = indicators.get('pivot_points') or {}
    vwap = indicators.get('vwap')
    pp = piv.get('pp')
    r1, s1 = piv.get('r1'), piv.get('s1')
    if pp is None or r1 is None or s1 is None:
        return _neutral(name, "Pivot levels unavailable", tags=["levels"])
    tol = price * 0.0015
    near = lambda lvl: lvl is not None and abs(price - lvl) <= tol * 3
    vwap_conf = vwap is not None and abs(price - vwap) <= tol * 3
    if price > r1:
        return _result(name, 'bullish', 78 if vwap_conf else 66,
                       f"Above R1 {r1:.0f}{' + VWAP confluence' if vwap_conf else ''} — breakout continuation toward R2 {piv.get('r2', r1):.0f}",
                       price, pp, piv.get('r2', price * 1.005), tags=["levels", "breakout"])
    if price < s1:
        return _result(name, 'bearish', 78 if vwap_conf else 66,
                       f"Below S1 {s1:.0f}{' + VWAP confluence' if vwap_conf else ''} — breakdown continuation toward S2 {piv.get('s2', s1):.0f}",
                       price, pp, piv.get('s2', price * 0.995), tags=["levels", "breakout"])
    if near(pp):
        bias = "bullish" if (vwap and price > vwap) else ("bearish" if (vwap and price < vwap) else "neutral")
        if bias == "neutral":
            return _neutral(name, f"Chop at Pivot {pp:.0f} — wait for R1/S1 break", tags=["levels"])
        return _result(name, bias, 60,
                       f"At Pivot {pp:.0f}, VWAP sides {bias} — scalp toward {'R1' if bias == 'bullish' else 'S1'}",
                       price, pp - tol * 4 if bias == 'bullish' else pp + tol * 4,
                       r1 if bias == 'bullish' else s1, tags=["levels"])
    side = "between PP–R1 (bullish zone)" if price > pp else "between S1–PP (bearish zone)"
    return _neutral(name, f"Inside {side} — trade the R1/S1 break, not the middle", tags=["levels"])


# ---------------------------------------------------------------------------
# Master runner + confluence verdict
# ---------------------------------------------------------------------------

def analyze_pro_strategies(indicators: Dict, price: float,
                           candles: List[Dict],
                           sentiment: Optional[Dict] = None,
                           option_chain: Optional[List[Dict]] = None) -> Dict:
    """Run all 15 pro strategies + compute the PRO CONFLUENCE verdict."""
    strategies = [
        orb_strategy(candles, price),
        vwap_pro_strategy(indicators, candles, price),
        ema_ribbon_strategy(indicators, candles, price),
        supertrend_adx_strategy(indicators, candles, price),
        bb_squeeze_strategy(indicators, candles, price),
        donchian_strategy(indicators, candles, price),
        keltner_strategy(indicators, candles, price),
        atr_trailing_strategy(indicators, candles, price),
        obv_strategy(indicators, candles, price),
        rsi_divergence_strategy(indicators, candles, price),
        max_oi_levels_strategy(option_chain, price),
        max_pain_strategy(option_chain, price),
        pcr_pro_strategy(sentiment),
        heikin_ashi_strategy(indicators, candles, price),
        pivot_confluence_strategy(indicators, price),
    ]

    bull = sum(s['strength'] for s in strategies if s['signal'] == 'bullish')
    bear = sum(s['strength'] for s in strategies if s['signal'] == 'bearish')
    n_bull = sum(1 for s in strategies if s['signal'] == 'bullish')
    n_bear = sum(1 for s in strategies if s['signal'] == 'bearish')
    total = bull + bear

    if total == 0 or n_bull == n_bear:
        direction, conf = 'NEUTRAL', 50
    elif bull > bear:
        direction, conf = 'BULLISH', round(50 + (bull - bear) / total * 50)
    else:
        direction, conf = 'BEARISH', round(50 + (bear - bull) / total * 50)

    # ATR-based trade plan for the verdict
    atr = _atr_value(indicators, candles, price)
    if direction == 'BULLISH':
        plan = {'entry': round(price, 2), 'stop_loss': round(price - 1.2 * atr, 2),
                'target_1': round(price + 1.5 * atr, 2), 'target_2': round(price + 2.5 * atr, 2)}
    elif direction == 'BEARISH':
        plan = {'entry': round(price, 2), 'stop_loss': round(price + 1.2 * atr, 2),
                'target_1': round(price - 1.5 * atr, 2), 'target_2': round(price - 2.5 * atr, 2)}
    else:
        plan = {'entry': None, 'stop_loss': None, 'target_1': None, 'target_2': None,
                'note': 'No confluence — WAIT'}

    # Regime tag
    adx_v = (indicators.get('adx') or {}).get('adx', 0)
    regime = 'TRENDING' if adx_v >= 22 else ('RANGING' if adx_v < 17 else 'TRANSITION')

    verdict = {
        'direction': direction,
        'confidence': conf,
        'bullish_votes': n_bull,
        'bearish_votes': n_bear,
        'neutral_votes': len(strategies) - n_bull - n_bear,
        'regime': regime,
        'trade_plan': plan,
        'action': ('TAKE TRADE' if conf >= 65 else 'LEAN / HALF SIZE' if conf >= 55 else 'WAIT'),
    }
    return {'strategies': strategies, 'pro_verdict': verdict}
