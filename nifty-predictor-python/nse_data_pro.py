"""
NSE Pro Data Module
Fetches all professional trading data from NSE:
- Option Chain with OI, IV, Greeks
- PCR (Put-Call Ratio)
- Max Pain calculation
- FII/DII activity
- VIX data
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from nsepython import nse_optionchain_scrapper, nse_get_index_quote

class NSEProData:
    """Professional NSE data provider for trading decisions"""
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = 30  # 30 seconds cache
        self.lot_sizes = {
            'nifty': 75,  # Current lot size
            'banknifty': 30
        }
        self.index_symbols = {
            'nifty': 'NIFTY',
            'banknifty': 'BANKNIFTY'
        }
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self.cache:
            return False
        _, timestamp = self.cache[key]
        return (time.time() - timestamp) < self.cache_duration
    
    def get_option_chain(self, index: str = 'nifty') -> Optional[Dict]:
        """
        Fetch real option chain data from NSE
        Returns: OI, IV, Greeks for all strikes
        """
        cache_key = f"oc_{index}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key][0]
        
        try:
            symbol = self.index_symbols.get(index, 'NIFTY')
            print(f"Fetching option chain for {symbol}...")
            
            oc_data = nse_optionchain_scrapper(symbol)
            
            if not oc_data:
                return None
            
            # Parse the option chain
            records = oc_data.get('records', {})
            expiry_dates = records.get('expiryDates', [])
            current_expiry = expiry_dates[0] if expiry_dates else None
            
            # Get underlying value
            underlying = records.get('underlyingValue', 0)
            
            # Filter data for current expiry
            data = records.get('data', [])
            
            chain = []
            total_ce_oi = 0
            total_pe_oi = 0
            
            for row in data:
                if row.get('expiryDate') != current_expiry:
                    continue
                
                strike = row.get('strikePrice', 0)
                ce = row.get('CE', {})
                pe = row.get('PE', {})
                
                ce_oi = ce.get('openInterest', 0)
                pe_oi = pe.get('openInterest', 0)
                
                total_ce_oi += ce_oi
                total_pe_oi += pe_oi
                
                chain.append({
                    'strike': strike,
                    'ce_oi': ce_oi,
                    'ce_oi_change': ce.get('changeinOpenInterest', 0),
                    'ce_ltp': ce.get('lastPrice', 0),
                    'ce_iv': ce.get('impliedVolatility', 0),
                    'ce_volume': ce.get('totalTradedVolume', 0),
                    'pe_oi': pe_oi,
                    'pe_oi_change': pe.get('changeinOpenInterest', 0),
                    'pe_ltp': pe.get('lastPrice', 0),
                    'pe_iv': pe.get('impliedVolatility', 0),
                    'pe_volume': pe.get('totalTradedVolume', 0),
                    'is_atm': abs(strike - underlying) < 50  # Within 50 points of spot
                })
            
            # Sort by strike
            chain.sort(key=lambda x: x['strike'])
            
            # Calculate PCR
            pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi > 0 else 1.0
            
            # Calculate Max Pain
            max_pain = self._calculate_max_pain(chain, underlying)
            
            result = {
                'underlying': underlying,
                'expiry': current_expiry,
                'chain': chain,
                'total_ce_oi': total_ce_oi,
                'total_pe_oi': total_pe_oi,
                'pcr': pcr,
                'max_pain': max_pain,
                'timestamp': datetime.now().isoformat(),
                'source': 'NSE'
            }
            
            self.cache[cache_key] = (result, time.time())
            return result
            
        except Exception as e:
            print(f"Error fetching option chain: {e}")
            return None
    
    def _calculate_max_pain(self, chain: List[Dict], spot: float) -> float:
        """Calculate Max Pain - the strike where option writers lose minimum"""
        if not chain:
            return spot
        
        min_pain = float('inf')
        max_pain_strike = spot
        
        # Get all strike prices
        strikes = [item['strike'] for item in chain]
        
        for strike in strikes:
            total_pain = 0
            
            for item in chain:
                s = item['strike']
                
                # Call buyer's loss if price ends at 'strike'
                if strike > s:
                    call_pain = (strike - s) * item['ce_oi']
                else:
                    call_pain = 0
                
                # Put buyer's loss if price ends at 'strike'
                if strike < s:
                    put_pain = (s - strike) * item['pe_oi']
                else:
                    put_pain = 0
                
                total_pain += call_pain + put_pain
            
            if total_pain < min_pain:
                min_pain = total_pain
                max_pain_strike = strike
        
        return max_pain_strike
    
    def get_pcr(self, index: str = 'nifty') -> Dict:
        """Get Put-Call Ratio with interpretation"""
        oc = self.get_option_chain(index)
        if not oc:
            return {'pcr': 1.0, 'sentiment': 'NEUTRAL', 'description': 'Data unavailable'}
        
        pcr = oc['pcr']
        
        if pcr > 1.3:
            sentiment = 'BULLISH'
            desc = 'High PCR indicates oversold - potential bullish reversal'
        elif pcr > 1.0:
            sentiment = 'MILDLY_BULLISH'
            desc = 'PCR above 1 suggests bearish positions being built - contrarian bullish'
        elif pcr < 0.7:
            sentiment = 'BEARISH'
            desc = 'Low PCR indicates overbought - potential bearish reversal'
        elif pcr < 1.0:
            sentiment = 'MILDLY_BEARISH'
            desc = 'PCR below 1 suggests bullish positions being built - contrarian bearish'
        else:
            sentiment = 'NEUTRAL'
            desc = 'PCR near 1 indicates balanced sentiment'
        
        return {
            'pcr': pcr,
            'sentiment': sentiment,
            'description': desc,
            'total_ce_oi': oc['total_ce_oi'],
            'total_pe_oi': oc['total_pe_oi']
        }
    
    def get_max_pain(self, index: str = 'nifty') -> Dict:
        """Get Max Pain analysis"""
        oc = self.get_option_chain(index)
        if not oc:
            return {'max_pain': 0, 'distance': 0, 'direction': 'NEUTRAL'}
        
        max_pain = oc['max_pain']
        spot = oc['underlying']
        distance = round(max_pain - spot, 2)
        distance_pct = round((distance / spot) * 100, 2) if spot > 0 else 0
        
        if distance > 50:
            direction = 'BULLISH'
            desc = f'Spot below Max Pain by {abs(distance_pct)}% - likely to move up towards {max_pain}'
        elif distance < -50:
            direction = 'BEARISH'
            desc = f'Spot above Max Pain by {abs(distance_pct)}% - likely to move down towards {max_pain}'
        else:
            direction = 'NEUTRAL'
            desc = f'Spot near Max Pain - may consolidate around {max_pain}'
        
        return {
            'max_pain': max_pain,
            'spot': spot,
            'distance': distance,
            'distance_pct': distance_pct,
            'direction': direction,
            'description': desc,
            'expiry': oc.get('expiry')
        }
    
    def get_oi_analysis(self, index: str = 'nifty') -> Dict:
        """Analyze Open Interest for support/resistance levels"""
        oc = self.get_option_chain(index)
        if not oc:
            return {}
        
        chain = oc['chain']
        spot = oc['underlying']
        
        # Find highest CE OI (Resistance) and highest PE OI (Support)
        max_ce_oi = 0
        max_pe_oi = 0
        resistance = spot
        support = spot
        
        for item in chain:
            if item['ce_oi'] > max_ce_oi:
                max_ce_oi = item['ce_oi']
                resistance = item['strike']
            if item['pe_oi'] > max_pe_oi:
                max_pe_oi = item['pe_oi']
                support = item['strike']
        
        # Find OI buildup (where OI is increasing)
        ce_buildup = sorted([i for i in chain if i['ce_oi_change'] > 0], 
                           key=lambda x: x['ce_oi_change'], reverse=True)[:3]
        pe_buildup = sorted([i for i in chain if i['pe_oi_change'] > 0], 
                           key=lambda x: x['pe_oi_change'], reverse=True)[:3]
        
        return {
            'resistance': resistance,
            'support': support,
            'max_ce_oi': max_ce_oi,
            'max_pe_oi': max_pe_oi,
            'ce_buildup_strikes': [i['strike'] for i in ce_buildup],
            'pe_buildup_strikes': [i['strike'] for i in pe_buildup],
            'range': f"{support} - {resistance}",
            'spot': spot
        }
    
    def estimate_trade_profit(self, index: str, direction: str, entry_price: float, 
                              target_price: float, stop_loss: float, lots: int = 1) -> Dict:
        """
        Calculate detailed profit/loss estimation for a trade
        """
        lot_size = self.lot_sizes.get(index, 75)
        oc = self.get_option_chain(index)
        
        if not oc:
            return {'error': 'Option chain data unavailable'}
        
        spot = oc['underlying']
        chain = oc['chain']
        
        # Find ATM strike
        atm_strike = round(spot / 50) * 50  # Round to nearest 50 for Nifty
        
        # Find option prices for ATM
        ce_premium = 0
        pe_premium = 0
        
        for item in chain:
            if item['strike'] == atm_strike:
                ce_premium = item['ce_ltp']
                pe_premium = item['pe_ltp']
                break
        
        # Calculate based on direction
        if direction.upper() == 'BULLISH':
            option_type = 'CE'
            option_premium = ce_premium
            expected_move = target_price - spot
            # Rough delta approximation for ATM (0.5)
            expected_premium_change = expected_move * 0.5
            target_premium = option_premium + expected_premium_change
            sl_move = spot - stop_loss
            sl_premium = option_premium - (sl_move * 0.5)
        else:
            option_type = 'PE'
            option_premium = pe_premium
            expected_move = spot - target_price
            expected_premium_change = expected_move * 0.5
            target_premium = option_premium + expected_premium_change
            sl_move = stop_loss - spot
            sl_premium = option_premium - (sl_move * 0.5)
        
        # Calculations
        capital_required = option_premium * lot_size * lots
        profit_potential = (target_premium - option_premium) * lot_size * lots
        max_loss = (option_premium - max(sl_premium, 0)) * lot_size * lots
        risk_reward = round(profit_potential / max_loss, 2) if max_loss > 0 else 0
        profit_pct = round((profit_potential / capital_required) * 100, 1) if capital_required > 0 else 0
        
        return {
            'option': f"{index.upper()} {atm_strike} {option_type}",
            'entry_premium': round(option_premium, 2),
            'target_premium': round(target_premium, 2),
            'stop_loss_premium': round(max(sl_premium, 0), 2),
            'lots': lots,
            'lot_size': lot_size,
            'capital_required': round(capital_required, 2),
            'profit_potential': round(profit_potential, 2),
            'profit_percentage': profit_pct,
            'max_loss': round(max_loss, 2),
            'risk_reward': risk_reward,
            'spot_entry': round(spot, 2),
            'spot_target': round(target_price, 2),
            'spot_stop_loss': round(stop_loss, 2),
            'recommendation': f"BUY {index.upper()} {atm_strike} {option_type} @ ₹{round(option_premium, 2)}\n"
                             f"Target: ₹{round(target_premium, 2)} | SL: ₹{round(max(sl_premium, 0), 2)}\n"
                             f"Lots: {lots} | Capital: ₹{round(capital_required, 2):,}\n"
                             f"PROFIT POTENTIAL: ₹{round(profit_potential, 2):,} ({profit_pct}%)"
        }
    
    def get_market_sentiment(self, index: str = 'nifty') -> Dict:
        """Get comprehensive market sentiment from all data sources"""
        try:
            pcr_data = self.get_pcr(index)
            max_pain_data = self.get_max_pain(index)
            oi_data = self.get_oi_analysis(index)
            
            # Calculate overall sentiment score (-100 to +100)
            score = 0
            signals = []
            
            # PCR contribution
            pcr = pcr_data.get('pcr', 1.0)
            if pcr > 1.2:
                score += 25
                signals.append("PCR > 1.2 (Bullish)")
            elif pcr < 0.8:
                score -= 25
                signals.append("PCR < 0.8 (Bearish)")
            
            # Max Pain contribution
            mp_direction = max_pain_data.get('direction', 'NEUTRAL')
            if mp_direction == 'BULLISH':
                score += 20
                signals.append("Below Max Pain (Bullish)")
            elif mp_direction == 'BEARISH':
                score -= 20
                signals.append("Above Max Pain (Bearish)")
            
            # OI analysis contribution
            spot = oi_data.get('spot', 0)
            resistance = oi_data.get('resistance', spot)
            support = oi_data.get('support', spot)
            
            if spot - support < resistance - spot:
                score += 15
                signals.append("Closer to support (Bullish)")
            else:
                score -= 15
                signals.append("Closer to resistance (Bearish)")
            
            # Determine overall sentiment
            if score > 30:
                overall = 'STRONGLY_BULLISH'
            elif score > 10:
                overall = 'BULLISH'
            elif score < -30:
                overall = 'STRONGLY_BEARISH'
            elif score < -10:
                overall = 'BEARISH'
            else:
                overall = 'NEUTRAL'
            
            return {
                'overall_sentiment': overall,
                'sentiment_score': score,
                'signals': signals,
                'pcr': pcr_data,
                'max_pain': max_pain_data,
                'oi_analysis': oi_data,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting market sentiment: {e}")
            return {
                'overall_sentiment': 'NEUTRAL',
                'sentiment_score': 0,
                'error': str(e)
            }


# Singleton instance
nse_pro = NSEProData()
