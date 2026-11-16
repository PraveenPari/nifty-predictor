from breeze_connect import BreezeConnect
import sys
import os
sys.path.append(os.getcwd())
try:
    from pro_config.api_config import BREEZE_API_KEY, BREEZE_SECRET_KEY
except ImportError:
    # Hardcode if import fails (backup)
    BREEZE_API_KEY = "1L999c8849796Y64573a`y553k478445"
    BREEZE_SECRET_KEY = "`IDU6723#1382=C6y917c6U72D9K362("

print("Initializing...")
b = BreezeConnect(api_key=BREEZE_API_KEY)
# b.generate_session(api_secret=BREEZE_SECRET_KEY, session_token='54440984')
# Use provided session directly if possible? No, generating session is needed.
try:
    b.generate_session(api_secret=BREEZE_SECRET_KEY, session_token='54440984')
    print("Session OK")
except Exception as e:
    print(f"Session Error: {e}")


print("Testing BANKNIFTY Expiries: Today vs Next Week")

expiries = ["21-JAN-2026", "28-JAN-2026", "22-JAN-2026"]

for exp in expiries:
    print(f"\nQuerying {exp}...")
    try:
        q = b.get_option_chain_quotes(
            stock_code="CNXBAN", 
            exchange_code="nfo", 
            product_type="options", 
            expiry_date=exp, 
            right="call"
        )
        if q.get('Success'):
            print(f"SUCCESS for {exp}!")
            print("Sample:", q['Success'][0])
        else:
            print(f"FAILED for {exp}: {q.get('Error')}")
            if q.get('Status'): print(f"Status: {q.get('Status')}")
            
    except Exception as e:
        print(f"Exception for {exp}: {e}")
