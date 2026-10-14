import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src import config
from src.cleaner import clean_batch, utc_now
from src.client import CoinGeckoClient
from src.models import CoinRecord
from src.storage import save_processed_csv, save_raw_json, save_rejected_json
from src.validator import ensure_quality, validate_batch

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RunSummary:

    collected_at: datetime
    duration_seconds: float
    fetched: int
    valid: int
    rejected: int
    records: list[CoinRecord]
    raw_path: Path | None
    processed_path: Path | None
    rejected_path: Path | None
    dry_run: bool


def run_pipeline(limit: int, currency: str, dry_run: bool = False) -> RunSummary:

    started = time.perf_counter()
    config.validate_config()

    with CoinGeckoClient() as client:
        raw_coins = client.get_markets(per_page=limit, vs_currency=currency)
    collected_at = utc_now()

    raw_path = None if dry_run else save_raw_json(raw_coins, collected_at)

    report = validate_batch(raw_coins)
    rejected_path = None if dry_run else save_rejected_json(report.rejected, collected_at)
    ensure_quality(report)

    records = clean_batch(report.valid, collected_at)
    processed_path = None if dry_run else save_processed_csv(records, collected_at)

    summary = RunSummary(
        collected_at=collected_at,
        duration_seconds=time.perf_counter() - started,
        fetched=len(raw_coins),
        valid=len(report.valid),
        rejected=len(report.rejected),
        records=records,
        raw_path=raw_path,
        processed_path=processed_path,
        rejected_path=rejected_path,
        dry_run=dry_run,
    )
    logger.info(
        "Run complete in %.2fs: fetched=%d valid=%d rejected=%d dry_run=%s",
        summary.duration_seconds, summary.fetched, summary.valid,
        summary.rejected, summary.dry_run,
    )
    return summary