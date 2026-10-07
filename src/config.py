import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("COINGECKO_API_KEY")
BASE_URL = os.getenv("BASE_URL","https://api.coingecko.com/api/v3")
VS_CURRENCY = os.getenv("VS_CURRENCY","usd")
COINS_PER_PAGE = int(os.getenv("COINS_PER_PAGE", "50"))

REQUEST_TIMEOUT = 10

def validate_config() -> None:
    """Fail fast if a requierd setting is missing"""
    if not API_KEY:
        raise ValueError("API_KEY not set, please Check .env file")