"""
Debug TOTP and Angel One Login
"""
import os
import pyotp
from datetime import datetime
import time

# Credentials — from environment only (see .env.example). Never hardcode.
api_key = os.getenv("ANGEL_ONE_API_KEY", "")
client_code = os.getenv("ANGEL_ONE_CLIENT_ID", "")
password = os.getenv("ANGEL_ONE_PASSWORD", "")
totp_secret = os.getenv("ANGEL_ONE_TOTP_SECRET", "")
if not all([api_key, client_code, password, totp_secret]):
    print("Missing Angel One credentials in environment — see .env.example.")
    raise SystemExit(1)

print("=" * 80)
print(" ANGEL ONE LOGIN DEBUG")
print("=" * 80)

print(f"\n📋 Credentials:")
print(f"   API Key: {api_key[:4]}...{api_key[-2:] if len(api_key) > 6 else ''}")
print(f"   Client Code: {'set' if client_code else 'MISSING'}")
print(f"   Password: {'set' if password else 'MISSING'}")
print(f"   TOTP Secret: {'set' if totp_secret else 'MISSING'}")

print(f"\n⏰ Time Information:")
print(f"   Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   Unix Timestamp: {int(time.time())}")

print(f"\n🔐 TOTP Generation:")
totp_generator = pyotp.TOTP(totp_secret)
current_totp = totp_generator.now()
print(f"   Generated TOTP: {current_totp}")
print(f"   TOTP Length: {len(current_totp)}")

# Generate next few TOTPs to see the pattern
print(f"\n📊 TOTP Sequence (30-second intervals):")
for i in range(-1, 2):
    offset_time = datetime.now().timestamp() + (i * 30)
    totp_at_time = totp_generator.at(offset_time)
    label = "PREVIOUS" if i == -1 else "CURRENT" if i == 0 else "NEXT"
    print(f"   {label}: {totp_at_time}")

print(f"\n🔄 Attempting Login...")
print("-" * 80)

try:
    from SmartApi import SmartConnect
    
    smart_api = SmartConnect(api_key=api_key)
    
    # Try login
    data = smart_api.generateSession(client_code, password, current_totp)
    
    print(f"\n📡 Response:")
    print(f"   Status: {data.get('status', 'N/A')}")
    print(f"   Message: {data.get('message', 'N/A')}")
    
    if data.get('status') == True:
        print(f"\n✅ LOGIN SUCCESSFUL!")
        print(f"   JWT Token: {data['data'].get('jwtToken', 'N/A')[:50]}...")
        
        # Logout
        smart_api.terminateSession(client_code)
        print(f"\n✅ Logged out successfully")
    else:
        print(f"\n❌ LOGIN FAILED")
        print(f"   Error Code: {data.get('errorCode', 'N/A')}")
        print(f"   Full Response: {data}")
        
        print(f"\n💡 Common Error Codes:")
        print(f"   AG8001: Invalid Client Code")
        print(f"   AG8002: Invalid Password")
        print(f"   AG8003: Invalid API Key")
        print(f"   AG8004: Invalid TOTP")
        print(f"   AB1007: Session Already Active")
        
        if data.get('errorCode') == 'AG8004':
            print(f"\n⚠️  TOTP is invalid. Possible reasons:")
            print(f"   1. TOTP secret is incorrect")
            print(f"   2. System time is not synchronized")
            print(f"   3. TOTP secret has been regenerated on Angel One portal")
            print(f"\n🔧 Try:")
            print(f"   1. Verify TOTP secret from Angel One portal")
            print(f"   2. Check if your system time is correct")
            print(f"   3. Try using the PREVIOUS or NEXT TOTP from the sequence above")
        elif data.get('errorCode') == 'AG8001':
            print(f"\n⚠️  Client Code is invalid!")
            print(f"   Current: {'set' if client_code else 'MISSING'} (masked)")
            print(f"   Check ANGEL_ONE_CLIENT_ID in your .env / host secrets")
        elif data.get('errorCode') == 'AG8002':
            print(f"\n⚠️  Password is invalid!")
            print(f"   Please verify your password")

except Exception as e:
    print(f"\n❌ Exception occurred: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
