import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

API_KEY = os.getenv("COINGECKO_API_KEY")
BASE_URL = os.getenv("BASE_URL","https://api.coingecko.com/api/v3")
VS_CURRENCY = os.getenv("VS_CURRENCY","usd")
COINS_PER_PAGE = int(os.getenv("COINS_PER_PAGE", "50"))

REQUEST_TIMEOUT = 10
MAX_ATTEMPTS = 3
BACKOFF_SECONDS = 1
MAX_WAIT_SECONDS = 60
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
MAX_REJECTED_RATIO = float(os.getenv("MAX_REJECTED_RATIO", "0.5"))

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

def validate_config() -> None:
    """Fail fast if a required setting is missing"""
    if not API_KEY:
        raise ValueError("API_KEY not set, please Check .env file")