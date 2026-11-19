# API Configuration for Breeze Connect
#
# SECURITY: Secrets are loaded ONLY from environment variables / .env
# via secrets_manager. There are NO hardcoded keys in this repo.
# See SECURITY.md and secrets_manager.py for details.

from secrets_manager import (
    get_secret,
    get_breeze_credentials,
    is_breeze_configured,
    breeze_login_url,
    mask,
)

_creds = get_breeze_credentials()

# Breeze API — from secrets only (empty string when not configured)
BREEZE_API_KEY = _creds["api_key"]
BREEZE_SECRET_KEY = _creds["secret_key"]
BREEZE_SESSION_TOKEN = _creds["session_token"]
BREEZE_CONFIGURED = is_breeze_configured()

# Data source priority
DATA_SOURCES = ['breeze', 'yahoo', 'angel_one']

# API settings
RETRY_ATTEMPTS = 3
RETRY_DELAY = 1  # seconds
CACHE_DURATION = 5  # seconds
TIMEOUT = 30  # seconds

if not BREEZE_API_KEY or not BREEZE_SECRET_KEY:
    print("[SECRETS] Set BREEZE_API_KEY and BREEZE_SECRET_KEY to enable Breeze.")
elif not BREEZE_SESSION_TOKEN:
    print("[SECRETS] Breeze keys configured; set BREEZE_SESSION_TOKEN in server secrets for auto-connect.")
else:
    print(f"[SECRETS] Breeze configured (key {mask(BREEZE_API_KEY)}).")
