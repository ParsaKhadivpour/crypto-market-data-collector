import logging
import sys

from src import config
from src.client import CoinGeckoClient
from src.exceptions import CollectorError
from src.logger import setup_logging
from src.models import CoinRecord
from src.validator import ensure_quality, validate_batch

logger = logging.getLogger("main")


def print_summary(coins: list[CoinRecord]) -> None:
    """Print a one-line summary for each coin."""
    for coin in coins:
        print(coin.summary())


def main() -> int:
    setup_logging()
    logger.info("Collector started")

    try:
        config.validate_config()
        with CoinGeckoClient() as client:
            raw_coins = client.get_markets(per_page=5)

        report = validate_batch(raw_coins)
        ensure_quality(report)
        coins = [CoinRecord.from_api(item) for item in report.valid]
    except CollectorError as exc:
        logger.error("Collection failed: %s", exc)
        return 1
    except Exception:
        logger.exception("Unexpected error")
        return 2

    logger.info("Collector finished successfully (%d coins)", len(coins))
    print_summary(coins)
    return 0


if __name__ == "__main__":
    sys.exit(main())