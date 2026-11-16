"""
Stock Universe Module
Contains NIFTY50 constituent stocks with Yahoo Finance symbols
"""

# NIFTY 50 Stocks with Yahoo Finance symbols
NIFTY50_STOCKS = {
    # Banking & Financial Services
    'HDFCBANK': {'symbol': 'HDFCBANK.NS', 'name': 'HDFC Bank', 'sector': 'BANKING', 'lot_size': 25},
    'ICICIBANK': {'symbol': 'ICICIBANK.NS', 'name': 'ICICI Bank', 'sector': 'BANKING', 'lot_size': 25},
    'KOTAKBANK': {'symbol': 'KOTAKBANK.NS', 'name': 'Kotak Bank', 'sector': 'BANKING', 'lot_size': 25},
    'SBIN': {'symbol': 'SBIN.NS', 'name': 'SBI', 'sector': 'BANKING', 'lot_size': 25},
    'AXISBANK': {'symbol': 'AXISBANK.NS', 'name': 'Axis Bank', 'sector': 'BANKING', 'lot_size': 25},
    'INDUSINDBK': {'symbol': 'INDUSINDBK.NS', 'name': 'IndusInd Bank', 'sector': 'BANKING', 'lot_size': 25},
    'BAJFINANCE': {'symbol': 'BAJFINANCE.NS', 'name': 'Bajaj Finance', 'sector': 'NBFC', 'lot_size': 15},
    'BAJAJFINSV': {'symbol': 'BAJAJFINSV.NS', 'name': 'Bajaj Finserv', 'sector': 'NBFC', 'lot_size': 25},
    'HDFC': {'symbol': 'HDFC.NS', 'name': 'HDFC', 'sector': 'NBFC', 'lot_size': 25},
    
    # IT & Technology
    'TCS': {'symbol': 'TCS.NS', 'name': 'TCS', 'sector': 'IT', 'lot_size': 25},
    'INFY': {'symbol': 'INFY.NS', 'name': 'Infosys', 'sector': 'IT', 'lot_size': 50},
    'HCLTECH': {'symbol': 'HCLTECH.NS', 'name': 'HCL Tech', 'sector': 'IT', 'lot_size': 25},
    'WIPRO': {'symbol': 'WIPRO.NS', 'name': 'Wipro', 'sector': 'IT', 'lot_size': 50},
    'TECHM': {'symbol': 'TECHM.NS', 'name': 'Tech Mahindra', 'sector': 'IT', 'lot_size': 25},
    'LTIM': {'symbol': 'LTIM.NS', 'name': 'LTIMindtree', 'sector': 'IT', 'lot_size': 15},
    
    # FMCG & Consumer
    'HINDUNILVR': {'symbol': 'HINDUNILVR.NS', 'name': 'HUL', 'sector': 'FMCG', 'lot_size': 25},
    'ITC': {'symbol': 'ITC.NS', 'name': 'ITC', 'sector': 'FMCG', 'lot_size': 100},
    'NESTLEIND': {'symbol': 'NESTLEIND.NS', 'name': 'Nestle India', 'sector': 'FMCG', 'lot_size': 5},
    'BRITANNIA': {'symbol': 'BRITANNIA.NS', 'name': 'Britannia', 'sector': 'FMCG', 'lot_size': 10},
    'TATACONSUM': {'symbol': 'TATACONSUM.NS', 'name': 'Tata Consumer', 'sector': 'FMCG', 'lot_size': 50},
    
    # Auto & Auto Ancillary
    'MARUTI': {'symbol': 'MARUTI.NS', 'name': 'Maruti Suzuki', 'sector': 'AUTO', 'lot_size': 5},
    'TATAMOTORS': {'symbol': 'TATAMOTORS.NS', 'name': 'Tata Motors', 'sector': 'AUTO', 'lot_size': 50},
    'M&M': {'symbol': 'M&M.NS', 'name': 'M&M', 'sector': 'AUTO', 'lot_size': 25},
    'BAJAJ-AUTO': {'symbol': 'BAJAJ-AUTO.NS', 'name': 'Bajaj Auto', 'sector': 'AUTO', 'lot_size': 10},
    'HEROMOTOCO': {'symbol': 'HEROMOTOCO.NS', 'name': 'Hero MotoCorp', 'sector': 'AUTO', 'lot_size': 15},
    'EICHERMOT': {'symbol': 'EICHERMOT.NS', 'name': 'Eicher Motors', 'sector': 'AUTO', 'lot_size': 15},
    
    # Pharma & Healthcare
    'SUNPHARMA': {'symbol': 'SUNPHARMA.NS', 'name': 'Sun Pharma', 'sector': 'PHARMA', 'lot_size': 50},
    'DRREDDY': {'symbol': 'DRREDDY.NS', 'name': "Dr Reddy's", 'sector': 'PHARMA', 'lot_size': 10},
    'CIPLA': {'symbol': 'CIPLA.NS', 'name': 'Cipla', 'sector': 'PHARMA', 'lot_size': 25},
    'DIVISLAB': {'symbol': 'DIVISLAB.NS', 'name': 'Divis Labs', 'sector': 'PHARMA', 'lot_size': 10},
    'APOLLOHOSP': {'symbol': 'APOLLOHOSP.NS', 'name': 'Apollo Hospitals', 'sector': 'HEALTHCARE', 'lot_size': 10},
    
    # Energy & Oil
    'RELIANCE': {'symbol': 'RELIANCE.NS', 'name': 'Reliance', 'sector': 'ENERGY', 'lot_size': 25},
    'ONGC': {'symbol': 'ONGC.NS', 'name': 'ONGC', 'sector': 'ENERGY', 'lot_size': 100},
    'NTPC': {'symbol': 'NTPC.NS', 'name': 'NTPC', 'sector': 'POWER', 'lot_size': 100},
    'POWERGRID': {'symbol': 'POWERGRID.NS', 'name': 'Power Grid', 'sector': 'POWER', 'lot_size': 100},
    'ADANIPORTS': {'symbol': 'ADANIPORTS.NS', 'name': 'Adani Ports', 'sector': 'INFRA', 'lot_size': 25},
    'ADANIENT': {'symbol': 'ADANIENT.NS', 'name': 'Adani Enterprises', 'sector': 'INFRA', 'lot_size': 25},
    
    # Metals & Mining
    'TATASTEEL': {'symbol': 'TATASTEEL.NS', 'name': 'Tata Steel', 'sector': 'METAL', 'lot_size': 50},
    'JSWSTEEL': {'symbol': 'JSWSTEEL.NS', 'name': 'JSW Steel', 'sector': 'METAL', 'lot_size': 50},
    'HINDALCO': {'symbol': 'HINDALCO.NS', 'name': 'Hindalco', 'sector': 'METAL', 'lot_size': 50},
    'COALINDIA': {'symbol': 'COALINDIA.NS', 'name': 'Coal India', 'sector': 'METAL', 'lot_size': 100},
    
    # Infrastructure & Construction
    'LT': {'symbol': 'LT.NS', 'name': 'L&T', 'sector': 'INFRA', 'lot_size': 15},
    'ULTRACEMCO': {'symbol': 'ULTRACEMCO.NS', 'name': 'UltraTech Cement', 'sector': 'CEMENT', 'lot_size': 5},
    'GRASIM': {'symbol': 'GRASIM.NS', 'name': 'Grasim', 'sector': 'CEMENT', 'lot_size': 25},
    
    # Telecom & Media
    'BHARTIARTL': {'symbol': 'BHARTIARTL.NS', 'name': 'Bharti Airtel', 'sector': 'TELECOM', 'lot_size': 25},
    
    # Others
    'ASIANPAINT': {'symbol': 'ASIANPAINT.NS', 'name': 'Asian Paints', 'sector': 'PAINTS', 'lot_size': 25},
    'TITAN': {'symbol': 'TITAN.NS', 'name': 'Titan', 'sector': 'CONSUMER', 'lot_size': 25},
    'SBILIFE': {'symbol': 'SBILIFE.NS', 'name': 'SBI Life', 'sector': 'INSURANCE', 'lot_size': 25},
    'HDFCLIFE': {'symbol': 'HDFCLIFE.NS', 'name': 'HDFC Life', 'sector': 'INSURANCE', 'lot_size': 50},
}

# Sector categorization
SECTORS = {
    'BANKING': ['HDFCBANK', 'ICICIBANK', 'KOTAKBANK', 'SBIN', 'AXISBANK', 'INDUSINDBK'],
    'NBFC': ['BAJFINANCE', 'BAJAJFINSV', 'HDFC'],
    'IT': ['TCS', 'INFY', 'HCLTECH', 'WIPRO', 'TECHM', 'LTIM'],
    'FMCG': ['HINDUNILVR', 'ITC', 'NESTLEIND', 'BRITANNIA', 'TATACONSUM'],
    'AUTO': ['MARUTI', 'TATAMOTORS', 'M&M', 'BAJAJ-AUTO', 'HEROMOTOCO', 'EICHERMOT'],
    'PHARMA': ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'DIVISLAB'],
    'HEALTHCARE': ['APOLLOHOSP'],
    'ENERGY': ['RELIANCE', 'ONGC'],
    'POWER': ['NTPC', 'POWERGRID'],
    'METAL': ['TATASTEEL', 'JSWSTEEL', 'HINDALCO', 'COALINDIA'],
    'INFRA': ['LT', 'ADANIPORTS', 'ADANIENT'],
    'CEMENT': ['ULTRACEMCO', 'GRASIM'],
    'TELECOM': ['BHARTIARTL'],
    'INSURANCE': ['SBILIFE', 'HDFCLIFE'],
    'CONSUMER': ['TITAN', 'ASIANPAINT'],
}


def get_all_stocks():
    """Return all NIFTY50 stocks"""
    return NIFTY50_STOCKS


def get_all_symbols():
    """Return list of Yahoo Finance symbols"""
    return [stock['symbol'] for stock in NIFTY50_STOCKS.values()]


def get_stocks_by_sector(sector: str):
    """Return stocks filtered by sector"""
    if sector not in SECTORS:
        return {}
    return {code: NIFTY50_STOCKS[code] for code in SECTORS[sector] if code in NIFTY50_STOCKS}


def get_stock_info(code: str):
    """Get stock info by code"""
    return NIFTY50_STOCKS.get(code.upper())


def get_sector_list():
    """Return list of all sectors"""
    return list(SECTORS.keys())
