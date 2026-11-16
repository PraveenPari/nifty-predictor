import os
import sys
import shutil
from datetime import datetime, timedelta
from dotenv import load_dotenv

os.chdir(r"e:\onedrive_data\OneDrive - Applied Data Finance LLC\WORKOUT CODE\nifty-predictor-python")
sys.path.append(os.getcwd())
load_dotenv()

from pro_config.api_config import BREEZE_API_KEY, BREEZE_SECRET_KEY, BREEZE_SESSION_TOKEN
from breeze_connect import BreezeConnect
from chart_generator import generate_prediction_chart

def create_chart():
    breeze = BreezeConnect(api_key=BREEZE_API_KEY)
    breeze.generate_session(api_secret=BREEZE_SECRET_KEY, session_token=BREEZE_SESSION_TOKEN)

    # Fetch daily data for the chart
    to_date = datetime.now().strftime("%Y-%m-%dT15:30:00.000Z")
    from_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%dT09:15:00.000Z")
    
    historical = breeze.get_historical_data_v2(
        interval="1day",
        from_date=from_date,
        to_date=to_date,
        stock_code="STABAN",
        exchange_code="NSE",
        product_type="cash"
    )
    
    candles = []
    if historical and 'Success' in historical and historical['Success']:
        for row in historical['Success']:
            candles.append({
                'timestamp': row.get('datetime'),
                'open': float(row.get('open', 0)),
                'high': float(row.get('high', 0)),
                'low': float(row.get('low', 0)),
                'close': float(row.get('close', 0)),
                'volume': int(row.get('volume', 0))
            })
            
    # Generate the chart
    print("Generating Chart...")
    generate_prediction_chart(candles, "SBI", [], "BULLISH", 1036.0, 1027.0)
    
    source = r"e:\onedrive_data\OneDrive - Applied Data Finance LLC\WORKOUT CODE\nifty-predictor-python\static\charts\prediction_SBI.png"
    dest = r"C:\Users\PraveenPari\.gemini\antigravity\brain\414025e3-5de7-4902-b55e-b4d05df61aa3\prediction_SBI.png"
    
    shutil.copy2(source, dest)
    print(f"Chart saved to {dest}")

if __name__ == "__main__":
    create_chart()
