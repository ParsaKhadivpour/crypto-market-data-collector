import logging
import sys
from enum import IntEnum

from src.cli import parse_args
from src.exceptions import CollectorError
from src.logger import setup_logging
from src.pipeline import RunSummary, run_pipeline

logger = logging.getLogger("main")


class ExitCode(IntEnum):
    OK = 0
    FAILURE = 1
    UNEXPECTED = 3   


def print_report(summary: RunSummary, top: int = 10) -> None:
    """Show the result of a run to the person who started it."""
    print(
        f"\nCollected {summary.fetched} coins in {summary.duration_seconds:.1f}s "
        f"({summary.valid} valid, {summary.rejected} rejected)\n"
    )
    for coin in summary.records[:top]:
        print(coin.summary())

    if summary.dry_run:
        print("\nDry run: no files were written.")
        return

    print(f"\nRaw data:       {summary.raw_path}")
    print(f"Processed data: {summary.processed_path}")
    if summary.rejected_path:
        print(f"Rejected data:  {summary.rejected_path}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    setup_logging()
    logger.info(
        "Collector started (limit=%d, currency=%s, dry_run=%s)",
        args.limit, args.currency, args.dry_run,
    )

    try:
        summary = run_pipeline(
            limit=args.limit, currency=args.currency, dry_run=args.dry_run
        )
    except CollectorError as exc:
        logger.error("Collection failed: %s", exc)
        return ExitCode.FAILURE
    except Exception:
        logger.exception("Unexpected error")
        return ExitCode.UNEXPECTED

    print_report(summary)
    return ExitCode.OK


if __name__ == "__main__":
    sys.exit(main())