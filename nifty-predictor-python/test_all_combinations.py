"""
Test Both Credential Combinations for Angel One
"""
import pyotp
from SmartApi import SmartConnect
from datetime import datetime

print("=" * 80)
print(" TESTING ANGEL ONE LOGIN - BOTH COMBINATIONS")
print("=" * 80)

# TOTP Secret (confirmed by user)
totp_secret = "542WYM7GZSMT73TU625FXJAV2M"
password = "2271"

# Generate TOTP
totp_generator = pyotp.TOTP(totp_secret)
current_totp = totp_generator.now()

print(f"\n⏰ Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"🔐 Generated TOTP: {current_totp}")
print()

# Combination 1: From user's initial message
print("=" * 80)
print(" COMBINATION 1: From User's Message")
print("=" * 80)
api_key_1 = "9f827dea-d345-4f62-9fb2-b4911e40d05e"
client_code_1 = "ujRLiue0"

print(f"API Key: {api_key_1}")
print(f"Client Code: {client_code_1}")
print(f"Password: {password}")
print(f"TOTP: {current_totp}")
print()

try:
    smart_api_1= SmartConnect(api_key=api_key_1)
    data_1 = smart_api_1.generateSession(client_code_1, password, current_totp)
    
    if data_1.get('status') == True:
        print("✅ COMBINATION 1 WORKS!")
        print(f"   Session Token: {data_1['data'].get('jwtToken', '')[:30]}...")
        smart_api_1.terminateSession(client_code_1)
        print("\n🎉 SUCCESS! Use these credentials:")
        print(f"   API_KEY={api_key_1}")
        print(f"   CLIENT_ID={client_code_1}")
        exit(0)
    else:
        print("❌ COMBINATION 1 FAILED")
        print(f"   Error: {data_1.get('message', 'Unknown')}")
        print(f"   Error Code: {data_1.get('errorCode', 'Unknown')}")
except Exception as e:
    print(f"❌ COMBINATION 1 ERROR: {e}")

print()

# Combination 2: From old angel_one.py
print("=" * 80)
print(" COMBINATION 2: From Old Configuration")
print("=" * 80)
api_key_2 = "ujRLiue0"
client_code_2 = "P812102"

print(f"API Key: {api_key_2}")
print(f"Client Code: {client_code_2}")
print(f"Password: {password}")
print(f"TOTP: {current_totp}")
print()

try:
    smart_api_2 = SmartConnect(api_key=api_key_2)
    data_2 = smart_api_2.generateSession(client_code_2, password, current_totp)
    
    if data_2.get('status') == True:
        print("✅ COMBINATION 2 WORKS!")
        print(f"   Session Token: {data_2['data'].get('jwtToken', '')[:30]}...")
        smart_api_2.terminateSession(client_code_2)
        print("\n🎉 SUCCESS! Use these credentials:")
        print(f"   API_KEY={api_key_2}")
        print(f"   CLIENT_ID={client_code_2}")
        exit(0)
    else:
        print("❌ COMBINATION 2 FAILED")
        print(f"   Error: {data_2.get('message', 'Unknown')}")
        print(f"   Error Code: {data_2.get('errorCode', 'Unknown')}")
except Exception as e:
    print(f"❌ COMBINATION 2 ERROR: {e}")

print()

# Combination 3: Mixed
print("=" * 80)
print(" COMBINATION 3: Mixed (Long API Key + P812102)")
print("=" * 80)
api_key_3 = "9f827dea-d345-4f62-9fb2-b4911e40d05e"
client_code_3 = "P812102"

print(f"API Key: {api_key_3}")
print(f"Client Code: {client_code_3}")
print(f"Password: {password}")
print(f"TOTP: {current_totp}")
print()

try:
    smart_api_3 = SmartConnect(api_key=api_key_3)
    data_3 = smart_api_3.generateSession(client_code_3, password, current_totp)
    
    if data_3.get('status') == True:
        print("✅ COMBINATION 3 WORKS!")
        print(f"   Session Token: {data_3['data'].get('jwtToken', '')[:30]}...")
        smart_api_3.terminateSession(client_code_3)
        print("\n🎉 SUCCESS! Use these credentials:")
        print(f"   API_KEY={api_key_3}")
        print(f"   CLIENT_ID={client_code_3}")
        exit(0)
    else:
        print("❌ COMBINATION 3 FAILED")
        print(f"   Error: {data_3.get('message', 'Unknown')}")
        print(f"   Error Code: {data_3.get('errorCode', 'Unknown')}")
except Exception as e:
    print(f"❌ COMBINATION 3 ERROR: {e}")

print()
print("=" * 80)
print("❌ ALL COMBINATIONS FAILED!")
print("=" * 80)
print("\n💡 Please verify:")
print("   1. Password is correct (current: 2271)")
print("   2. TOTP secret hasn't been regenerated")
print("   3. Account is active and not locked")
print("\n📞 You may need to contact Angel One support or regenerate credentials")
