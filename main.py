import logging
import sys
from src import config
from src.client import fetch_market_data
from src.exceptions import CollectorError
from src.logger import setup_logging

logger = logging.getLogger("main")


def print_summary(coins: list[dict]) -> None:
    """Print a one-line summary for each coin."""
    for coin in coins:
        print(
            f"{coin['market_cap_rank']}. {coin['name']} "
            f"({coin['symbol'].upper()}): ${coin['current_price']}"
        )


def main() -> int:
    setup_logging()
    logger.info("Collector Started")
    try:
        config.validate_config()
        coins = fetch_market_data(per_page=5)
    except CollectorError as exc:
        logger.error("Collection Failed: %s", exc)
        return 1
    except Exception:
        logger.exception("Unexpected error")
        return 2
    logger.info("Collector Finished successfully (%d coins)", len(coins))
    print_summary(coins)
    return 0

if __name__ == "__main__":
    sys.exit(main())