import logging
import time

import requests

from src import config
from src.exceptions import APIConnectionError, APIResponseError, ConfigError

logger = logging.getLogger(__name__)


class CoinGeckoClient:
    """Small CoinGecko client with retries and error translation."""

    def __init__(
        self,
        api_key: str | None = config.API_KEY,
        base_url: str = config.BASE_URL,
        timeout: float = config.REQUEST_TIMEOUT,
        max_attempts: int = config.MAX_ATTEMPTS,
    ) -> None:
        if max_attempts < 1:
            raise ConfigError("max_attempts must be at least 1")

        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_attempts = max_attempts

        self._session = requests.Session()
        self._session.headers.update({"x-cg-demo-api-key": api_key})

    # --- context manager: `with CoinGeckoClient() as client:` ---

    def __enter__(self) -> "CoinGeckoClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        self._session.close()

    # --- public API ---

    def get_markets(
        self,
        per_page: int = config.COINS_PER_PAGE,
        page: int = 1,
        vs_currency: str = config.VS_CURRENCY,
    ) -> list[dict]:
        """Fetch market data for the top coins by market cap (raw dicts)."""
        params = {
            "vs_currency": vs_currency,
            "order": "market_cap_desc",
            "per_page": per_page,
            "page": page,
        }
        response = self._get("/coins/markets", params)
        coins = self._parse_list(response)
        logger.info("Fetched %d coins (currency: %s)", len(coins), vs_currency)
        return coins

    # --- internals ---

    def _get(self, endpoint: str, params: dict) -> requests.Response:
        """GET with retries. Returns a successful response or raises."""
        url = f"{self.base_url}{endpoint}"

        for attempt in range(1, self.max_attempts + 1):
            is_last_attempt = attempt == self.max_attempts
            logger.debug("GET %s params=%s (attempt %d)", url, params, attempt)

            try:
                response = self._session.get(url, params=params, timeout=self.timeout)
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
                if is_last_attempt:
                    raise APIConnectionError(
                        f"Network problem after {attempt} attempts: {exc}"
                    ) from exc
                self._sleep_before_retry(attempt, f"network problem ({type(exc).__name__})")
                continue
            except requests.exceptions.RequestException as exc:
                raise APIConnectionError(f"Request failed: {exc}") from exc

            if response.status_code in config.RETRYABLE_STATUS_CODES:
                if is_last_attempt:
                    raise APIResponseError(
                        f"API still returning {response.status_code} after {attempt} attempts",
                        status_code=response.status_code,
                    )
                self._sleep_before_retry(attempt, f"status {response.status_code}", response)
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

    def _sleep_before_retry(
        self, attempt: int, reason: str, response: requests.Response | None = None
    ) -> None:
        """Wait with exponential backoff (1s, 2s, 4s...) before the next attempt."""
        wait = config.BACKOFF_SECONDS * (2 ** (attempt - 1))

        if response is not None:
            retry_after = response.headers.get("Retry-After")
            if retry_after and retry_after.isdigit():
                wait = int(retry_after)

        wait = min(wait, config.MAX_WAIT_SECONDS)
        logger.warning(
            "[attempt %d/%d] %s. Retrying in %ds...",
            attempt, self.max_attempts, reason, wait,
        )
        time.sleep(wait)

    @staticmethod
    def _parse_list(response: requests.Response) -> list[dict]:
        """Decode the JSON body and check it is a list."""
        try:
            data = response.json()
        except ValueError as exc:
            raise APIResponseError("API returned a body that is not valid JSON") from exc

        if not isinstance(data, list):
            raise APIResponseError(f"Expected a list of coins, got {type(data).__name__}")

        return data