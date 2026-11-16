"""
Direct Breeze Connection Test
"""
from breeze_connect import BreezeConnect

# Credentials from .env / image
API_KEY = "1L999c8849796Y64573a`y553k478445"
SECRET_KEY = "`IDU6723#1382=C6y917c6U72D9K362("
SESSION_TOKEN = "54653418"

print("=" * 60)
print("  BREEZE DIRECT CONNECTION TEST")
print("=" * 60)

print(f"\n[1] API Key: {API_KEY}")
print(f"[2] Secret Key: {SECRET_KEY[:20]}...")
print(f"[3] Session Token: {SESSION_TOKEN}")

print("\n[4] Creating BreezeConnect...")
breeze = BreezeConnect(api_key=API_KEY)

print("\n[5] Generating session...")
try:
    result = breeze.generate_session(api_secret=SECRET_KEY, session_token=SESSION_TOKEN)
    print(f"[SUCCESS] Session generated! Result: {result}")
    
    # Test a simple API call
    print("\n[6] Testing get_customer_details...")
    details = breeze.get_customer_details()
    print(f"Customer: {details}")
    
except Exception as e:
    print(f"[ERROR] Failed: {e}")
    import traceback
    traceback.print_exc()
