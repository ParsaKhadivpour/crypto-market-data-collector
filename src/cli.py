import argparse

from src import config

MAX_LIMIT = 250


def _limit(value: str) -> int:
    """argparse type: a whole number between 1 and MAX_LIMIT."""
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value!r} is not a whole number") from None

    if not 1 <= number <= MAX_LIMIT:
        raise argparse.ArgumentTypeError(
            f"must be between 1 and {MAX_LIMIT}, got {number}"
        )
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crypto-collector",
        description=(
            "Collect crypto market data from CoinGecko, validate and clean it, "
            "and save it to disk."
        ),
    )
    parser.add_argument(
        "--limit",
        type=_limit,
        default=config.COINS_PER_PAGE,
        metavar="N",
        help=f"number of top coins to collect (1-{MAX_LIMIT}, default: %(default)s)",
    )
    parser.add_argument(
        "--currency",
        type=str.lower,
        default=config.VS_CURRENCY,
        metavar="CODE",
        help="quote currency, e.g. usd or eur (default: %(default)s)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="fetch, validate and clean, but do not write any files",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)