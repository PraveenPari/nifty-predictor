"""
Secrets Manager — Pro-level secrets handling.

Rules enforced here:
1. Secrets live ONLY in environment variables / secret managers — NEVER in code.
2. No hardcoded fallbacks. If a secret is missing, the feature that needs it
   is disabled with a clear message instead of silently using a stale key.
3. Secrets are NEVER printed. Use `mask()` / `safe_status()` for logs & APIs.
4. Breeze session tokens expire daily — `is_breeze_configured()` and the
   breeze manager surface re-auth instructions instead of crashing.

Supported sources (in order):
  - Real environment variables (Render / Railway / Docker / systemd, etc.)
  - Local `.env` file (development only — must stay git-ignored)
"""

import os
from typing import Dict, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv is optional in production (platform injects real env vars)
    pass


# Values that mean "not configured" even if the variable exists
_PLACEHOLDERS = {
    "",
    "your_breeze_api_key",
    "your_breeze_secret_key",
    "your_breeze_session_token",
    "your_angel_one_api_key",
    "your_client_id",
    "your_password",
    "your_totp_secret",
    "your_flask_secret_key",
    "changeme",
    "none",
    "null",
}


def get_secret(name: str, default: str = "") -> str:
    """Read a secret from the environment. Returns '' when missing/placeholder."""
    value = (os.getenv(name, default) or "").strip().strip('"').strip("'")
    if value.lower() in _PLACEHOLDERS:
        return ""
    return value


def mask(secret: str, visible: int = 4) -> str:
    """Mask a secret for safe logging, e.g. '1L99****445' or '(not set)'."""
    if not secret:
        return "(not set)"
    if len(secret) <= visible * 2:
        return "*" * len(secret)
    return f"{secret[:visible]}****{secret[-visible:]}"


# ---------------------------------------------------------------------------
# Breeze (ICICI Direct) — the ONLY broker whose token this app manages
# ---------------------------------------------------------------------------

def get_breeze_credentials() -> Dict[str, str]:
    """Return Breeze credentials from secrets only. No hardcoded fallbacks."""
    return {
        "api_key": get_secret("BREEZE_API_KEY"),
        "secret_key": get_secret("BREEZE_SECRET_KEY"),
        "session_token": get_secret("BREEZE_SESSION_TOKEN"),
    }


def is_breeze_configured() -> bool:
    """True only when all three Breeze secrets are present and non-placeholder."""
    creds = get_breeze_credentials()
    return all(bool(v) for v in creds.values())


def breeze_login_url() -> Optional[str]:
    """ICICI Direct login URL used to mint a fresh daily session token."""
    api_key = get_secret("BREEZE_API_KEY")
    if not api_key:
        return None
    from urllib.parse import quote_plus
    return f"https://api.icicidirect.com/apiuser/login?api_key={quote_plus(api_key)}"


def safe_status() -> Dict:
    """Safe-to-log / safe-to-expose status. Contains NO secret values."""
    creds = get_breeze_credentials()
    return {
        "breeze": {
            "api_key": mask(creds["api_key"]),
            "secret_key_set": bool(creds["secret_key"]),
            "session_token_set": bool(creds["session_token"]),
            "fully_configured": is_breeze_configured(),
            "login_url_ready": bool(creds["api_key"]),
        },
        "angel_one": {
            "api_key_set": bool(get_secret("ANGEL_ONE_API_KEY")),
            "client_id_set": bool(get_secret("ANGEL_ONE_CLIENT_ID")),
            "password_set": bool(get_secret("ANGEL_ONE_PASSWORD")),
            "totp_set": bool(get_secret("ANGEL_ONE_TOTP_SECRET")),
            "configured": bool(get_secret("ANGEL_ONE_API_KEY")),
        },
        "flask_secret_set": bool(get_secret("SECRET_KEY") or get_secret("FLASK_SECRET_KEY")),
    }


def breeze_setup_help() -> str:
    return (
        "Breeze is not configured. Set these secrets and restart:\n"
        "  1. BREEZE_API_KEY + BREEZE_SECRET_KEY (from ICICI Direct developer portal)\n"
        "  2. Open the login URL from /api/breeze-login-url, log in, copy the "
        "session token from the redirect URL\n"
        "  3. Set BREEZE_SESSION_TOKEN to that token (it expires daily — "
        "refresh every trading morning)\n"
        "Local dev: put them in nifty-predictor-python/.env (git-ignored).\n"
        "Hosting: set them in your provider's Secrets / Environment dashboard."
    )
