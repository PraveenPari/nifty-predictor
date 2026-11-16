import os
import sys
from dotenv import load_dotenv

os.chdir(r"e:\onedrive_data\OneDrive - Applied Data Finance LLC\WORKOUT CODE\nifty-predictor-python")
sys.path.append(os.getcwd())
load_dotenv()

from pro_config.api_config import BREEZE_API_KEY, BREEZE_SECRET_KEY, BREEZE_SESSION_TOKEN
from breeze_connect import BreezeConnect

breeze = BreezeConnect(api_key=BREEZE_API_KEY)
breeze.generate_session(api_secret=BREEZE_SECRET_KEY, session_token=BREEZE_SESSION_TOKEN)

# Fetch option chain quote for 1030 CE
print("Fetching 1030 CE Option Data for STABAN...")
# product_type is usually 'options'
options = breeze.get_option_chain_quotes(
    stock_code="STABAN",
    exchange_code="NFO",
    product_type="options",
    expiry_date="30-Jul-2026",
    right="Call",
    strike_price="1030"
)

from pprint import pprint
pprint(options)
