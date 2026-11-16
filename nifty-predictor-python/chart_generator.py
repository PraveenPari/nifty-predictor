import matplotlib
matplotlib.use('Agg')
import mplfinance as mpf
import pandas as pd
import os
from datetime import datetime

def generate_prediction_chart(candles, index_name, patterns, direction, target, stop_loss):
    """
    Generate a static chart with prediction visualization
    """
    if not candles:
        return None
        
    try:
        # Convert to DataFrame
        df = pd.DataFrame(candles)
        df['Date'] = pd.to_datetime(df['timestamp'])
        df.set_index('Date', inplace=True)
        # Ensure numeric columns
        cols = ['open', 'high', 'low', 'close', 'volume']
        for col in cols:
            df[col] = pd.to_numeric(df[col])
            
        # Create output directory
        static_dir = os.path.join(os.path.dirname(__file__), 'static', 'charts')
        os.makedirs(static_dir, exist_ok=True)
        filename = f"prediction_{index_name}.png"
        filepath = os.path.join(static_dir, filename)
        
        # Plotting logic
        # Add basic Moving Averages
        mav = (20, 50)
        
        # Prepare title
        title = f"{index_name.upper()} Analysis - {datetime.now().strftime('%H:%M')}\n{direction} | Tgt: {target} | SL: {stop_loss}"
        
        # Custom Style
        s = mpf.make_mpf_style(base_mpf_style='nightclouds', rc={'font.size': 8})
        
        # Add target/stop lines if valid
        hlines = []
        colors = []
        if target > 0 and stop_loss > 0:
            hlines = [target, stop_loss]
            colors = ['green', 'red']
            
        # Plot
        mpf.plot(
            df.tail(60), # Last 60 candles
            type='candle',
            style=s,
            title=title,
            ylabel='Price',
            mav=mav,
            hlines=dict(hlines=hlines, colors=colors, linestyle='-.', linewidths=1),
            savefig=dict(fname=filepath, dpi=100, bbox_inches='tight'),
            volume=False # Simpler chart
        )
        
        return f"/static/charts/{filename}?t={int(datetime.now().timestamp())}"
        
    except Exception as e:
        print(f"Error generating chart: {e}")
        return None
