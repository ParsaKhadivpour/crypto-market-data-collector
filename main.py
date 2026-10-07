import sys

from src import config
from src.client import fetch_market_data
from src.exceptions import CollectorError


def print_summary(coins: list[dict]) -> None:
    """Print a one-line summary for each coin."""
    for coin in coins:
        print(
            f"{coin['market_cap_rank']}. {coin['name']} "
            f"({coin['symbol'].upper()}): ${coin['current_price']}"
        )


def main() -> int:
    try:
        config.validate_config()
        coins = fetch_market_data(per_page=5)
    except CollectorError as exc:
        print(f"Error: {exc}")
        return 1

    print(f"Fetched {len(coins)} coins")
    print_summary(coins)
    return 0


if __name__ == "__main__":
    sys.exit(main())