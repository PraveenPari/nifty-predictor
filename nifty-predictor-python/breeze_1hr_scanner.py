import os
import sys
import json
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

os.chdir(r"e:\onedrive_data\OneDrive - Applied Data Finance LLC\WORKOUT CODE\nifty-predictor-python")
sys.path.append(os.getcwd())
load_dotenv()

from pro_config.api_config import BREEZE_API_KEY, BREEZE_SECRET_KEY, BREEZE_SESSION_TOKEN
try:
    from breeze_connect import BreezeConnect
except ImportError:
    print("Breeze SDK not found")
    sys.exit(1)

from indicators import TechnicalIndicators
from strategies import TradingStrategies

def generate_report():
    print(f"Connecting to Breeze with token: {BREEZE_SESSION_TOKEN[:10]}...")
    breeze = BreezeConnect(api_key=BREEZE_API_KEY)
    breeze.generate_session(api_secret=BREEZE_SECRET_KEY, session_token=BREEZE_SESSION_TOKEN)

    # High Liquidity Intraday Stocks
    stocks = ['RELIANCE', 'HDFCBANK', 'ICICIBANK', 'INFY', 'TCS', 'SBIN', 'ITC']
    
    report_lines = []
    report_lines.append("# 🚀 1-Hour Intraday Momentum Scan (Breeze API)")
    report_lines.append(f"**Generated At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("\n> [!NOTE]\n> Scanning Top Nifty 50 constituents using 5-minute timeframe data for the next 1-hour momentum trade.\n")
    
    report_lines.append("## Scan Results\n")
    report_lines.append("| Stock | Spot Price | RSI (14) | MACD | VWAP Status | Action (Next 1Hr) |")
    report_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")

    best_buy = None
    highest_score = 0
    
    to_date = datetime.now().strftime("%Y-%m-%dT15:30:00.000Z")
    from_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%dT09:15:00.000Z")

    for stock in stocks:
        print(f"Scanning {stock}...")
        try:
            # 1. Fetch 5-Minute Historical Data for Indicators
            historical = breeze.get_historical_data_v2(
                interval="5minute",
                from_date=from_date,
                to_date=to_date,
                stock_code=stock,
                exchange_code="NSE",
                product_type="cash"
            )
            
            if historical and 'Success' in historical and historical['Success']:
                candles = []
                for row in historical['Success']:
                    candles.append({
                        'high': float(row.get('high', 0)),
                        'low': float(row.get('low', 0)),
                        'close': float(row.get('close', 0)),
                        'volume': int(row.get('volume', 0))
                    })
                
                if len(candles) < 50:
                    continue
                
                # 2. Calculate Indicators
                indicators = TechnicalIndicators.calculate_all(candles)
                current_price = candles[-1]['close']
                
                rsi = indicators.get('rsi', 0)
                macd_dict = indicators.get('macd', {})
                macd_hist = macd_dict.get('histogram', 0)
                vwap = indicators.get('vwap', current_price)
                
                vwap_status = "Above VWAP" if current_price > vwap else "Below VWAP"
                
                # 3. Score the setup for the next 1 hour (Bullish Momentum)
                score = 0
                if 40 < rsi < 65: score += 30 # Room to grow, not overbought
                if macd_hist > 0: score += 40 # Positive momentum
                if current_price > vwap: score += 30 # Institutional support
                
                action = "Neutral"
                if score >= 70: 
                    action = "🟢 STRONG BUY"
                    if score > highest_score:
                        highest_score = score
                        best_buy = stock
                elif score <= 30: 
                    action = "🔴 SELL / SHORT"
                
                report_lines.append(f"| **{stock}** | ₹{current_price} | {rsi:.2f} | {macd_hist:.2f} | {vwap_status} | {action} |")
                
        except Exception as e:
            print(f"Error scanning {stock}: {e}")

    report_lines.append("\n---\n## 🎯 Top Recommendation for the Next Hour\n")
    if best_buy:
        report_lines.append(f"> [!TIP]\n> **{best_buy}** shows the strongest intraday momentum (Price > VWAP, MACD Expansion, Healthy RSI). \n> **Strategy:** Look for Call Options (CE) or Intraday Equity Long setups on pullbacks towards VWAP.\n")
    else:
        report_lines.append("> [!WARNING]\n> **No Clear Setup Found.** The market is currently consolidating or highly volatile. Avoid directional options buying for the next hour.\n")

    report_path = r"C:\Users\PraveenPari\.gemini\antigravity\brain\414025e3-5de7-4902-b55e-b4d05df61aa3\breeze_1hr_analysis_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    print(f"\nReport successfully generated at: {report_path}")

if __name__ == "__main__":
    generate_report()
