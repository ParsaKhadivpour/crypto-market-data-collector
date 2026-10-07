import time
import requests
from src import config
from src.exceptions import APIConnectionError, APIResponseError
import logging

logger = logging.getLogger(__name__)

def build_headers() -> dict:
    """Return the auth headers for CoinGecko."""
    return {"x-cg-demo-api-key": config.API_KEY}

def _sleep_before_retry(
    attempt: int, reason: str, response: requests.Response | None = None
) -> None:
    """Wait with exponential backoff (1s, 2s, 4s...) before the next attempt."""
    wait = config.BACKOFF_SECONDS * (2 ** (attempt - 1))

    # If the server tells us how long to wait, respect it.
    if response is not None:
        retry_after = response.headers.get("Retry-After")
        if retry_after and retry_after.isdigit():
            wait = int(retry_after)

    wait = min(wait, config.MAX_WAIT_SECONDS)
    logger.warning("[attempt %d/%d] %s. Retrying in %ds...", attempt, config.MAX_ATTEMPTS,
                   reason , wait,)
    time.sleep(wait)

def _get_with_retries(url: str, params: dict) -> requests.Response:
    """Send a GET request, retrying temporary failures. Returns a successful response."""
    for attempt in range(1, config.MAX_ATTEMPTS + 1):
        is_last_attempt = attempt == config.MAX_ATTEMPTS
        logger.debug("GET %s params=%s (attempt %d)",url, params, attempt)

        try:
            response = requests.get(
                url,
                headers=build_headers(),
                params=params,
                timeout=config.REQUEST_TIMEOUT,
            )
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            if is_last_attempt:
                raise APIConnectionError(
                    f"Network problem after {attempt} attempts: {exc}"
                ) from exc
            _sleep_before_retry(attempt, f"network problem ({type(exc).__name__})")
            continue
        except requests.exceptions.RequestException as exc:
            raise APIConnectionError(f"Request failed: {exc}") from exc

        if response.status_code in config.RETRYABLE_STATUS_CODES:
            if is_last_attempt:
                raise APIResponseError(
                    f"API still returning {response.status_code} after {attempt} attempts",
                    status_code=response.status_code,
                )
            _sleep_before_retry(attempt, f"status {response.status_code}", response)
            continue

        if not response.ok:
            raise APIResponseError(
                f"API returned {response.status_code}: {response.text[:200]}",
                status_code=response.status_code,
            )

        logger.debug(
            "Response %s in %.2fs",
            response.status_code, response.elapsed.total_seconds(),
        )

        return response

def _parse_coins(response: requests.Response) -> list[dict]:
    """Decode the JSON body and check it has the shape we expect."""
    try:
        data = response.json()
    except ValueError as exc:
        raise APIResponseError("API returned a body that is not valid JSON") from exc

    if not isinstance(data, list):
        raise APIResponseError(f"Expected a list of coins, got {type(data).__name__}")

    return data

def fetch_market_data(
    per_page: int = config.COINS_PER_PAGE,
    page: int = 1,
    vs_currency: str = config.VS_CURRENCY,
) -> list[dict]:
    """Fetch market data for the top coins by market cap."""
    url = f"{config.BASE_URL}/coins/markets"
    params = {
        "vs_currency": vs_currency,
        "order": "market_cap_desc",
        "per_page": per_page,
        "page": page,
    }

    response = _get_with_retries(url, params)
    coins = _parse_coins(response)
    logger.info("Fetched %d coins (currency: %s)", len(coins), vs_currency)
    return coins