import requests

from src import config

def build_headers() -> dict:
    """Return the auth headers of CoinGecko."""
    return {"x-cg-demo-api-key": config.API_KEY}

def fetch_market_data(per_page:int = config.COINS_PER_PAGE, page:int = 1) -> list[dict]:
    """Fetch market data for the top coins by marketcap."""
    url = f"{config.BASE_URL}/coins/markets"
    params = {
        "vs_currency": config.VS_CURRENCY,
        "order": "market_cap_desc",
        "per_page": per_page,
        "page": page,
    }

    response = requests.get(
        url,
        headers=build_headers(),
        params=params,
        timeout= config.REQUEST_TIMEOUT,
    )

    response.raise_for_status()
    return response.json()