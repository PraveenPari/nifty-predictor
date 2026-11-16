# API Configuration for Breeze Connect
import os
from dotenv import load_dotenv

load_dotenv()

# Breeze API - Read from .env with fallback to hardcoded values
BREEZE_API_KEY = os.getenv("BREEZE_API_KEY", "1L999c8849796Y64573a`y553k478445")
BREEZE_SECRET_KEY = os.getenv("BREEZE_SECRET_KEY", "`IDU6723#1382=C6y917c6U72D9K362(")
BREEZE_SESSION_TOKEN = os.getenv("BREEZE_SESSION_TOKEN", "")

# Data source priority
DATA_SOURCES = ['breeze', 'yahoo', 'angel_one']

# API settings
RETRY_ATTEMPTS = 3
RETRY_DELAY = 1  # seconds
CACHE_DURATION = 5  # seconds
TIMEOUT = 30  # seconds
