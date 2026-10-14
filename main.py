import logging
import sys

from src import config
from src.cleaner import clean_batch, utc_now
from src.client import CoinGeckoClient
from src.exceptions import CollectorError
from src.logger import setup_logging
from src.models import CoinRecord
from src.storage import save_processed_csv, save_raw_json, save_rejected_json
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

        # 1) fetch
        with CoinGeckoClient() as client:
            raw_coins = client.get_markets(per_page=5)
        collected_at = utc_now()

        # 2) save raw immediately
        raw_path = save_raw_json(raw_coins, collected_at)

        # 3) validate (save rejects BEFORE the quality check)
        report = validate_batch(raw_coins)
        save_rejected_json(report.rejected, collected_at)
        ensure_quality(report)

        # 4) clean and save
        coins = clean_batch(report.valid, collected_at)
        csv_path = save_processed_csv(coins, collected_at)

    except CollectorError as exc:
        logger.error("Collection failed: %s", exc)
        return 1
    except Exception:
        logger.exception("Unexpected error")
        return 2

    logger.info("Collector finished successfully (%d coins)", len(coins))
    print_summary(coins[:10])
    print(f"\nRaw data:       {raw_path}")
    print(f"Processed data: {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())