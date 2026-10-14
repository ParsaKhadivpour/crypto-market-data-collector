import csv
import json
import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO

from src import config
from src.exceptions import StorageError
from src.models import CoinRecord
from src.validator import RejectedRecord

logger = logging.getLogger(__name__)

# CSV columns always follow the model, so they can never drift apart.
CSV_COLUMNS = [f.name for f in fields(CoinRecord)]


# ---------- helpers ----------

def _stamp(collected_at: datetime) -> str:
    """'20261012T083000Z': a timestamp that is safe in file names on every OS."""
    return collected_at.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _discard(path: Path) -> None:
    """Best-effort delete of a temp file. Must never hide the original error."""
    try:
        path.unlink(missing_ok=True)
    except OSError as exc:
        logger.debug("Could not remove temp file %s: %s", path, exc)


@contextmanager
def _atomic_open(path: Path, newline: str | None = None) -> Iterator[TextIO]:
    """Open `path` for writing so that it is either fully written or untouched."""
    tmp_path = path.with_name(path.name + ".tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(tmp_path, "w", encoding="utf-8", newline=newline) as file:
            yield file
        os.replace(tmp_path, path)   # atomic swap: old file -> new file
    except OSError as exc:
        _discard(tmp_path)
        raise StorageError(f"Could not write {path}: {exc}") from exc
    except BaseException:
        _discard(tmp_path)           # e.g. Ctrl+C or a bug in the caller
        raise


# ---------- writers ----------

def save_raw_json(raw_items: list[Any], collected_at: datetime) -> Path:
    """Save the untouched API response, wrapped in a small metadata envelope."""
    path = config.RAW_DIR / f"coins_{_stamp(collected_at)}.json"
    payload = {
        "source": "coingecko:/coins/markets",
        "collected_at": collected_at.isoformat(),
        "record_count": len(raw_items),
        "data": raw_items,
    }

    with _atomic_open(path) as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)

    logger.info("Saved raw data: %s (%d records)", path, len(raw_items))
    return path


def save_processed_csv(records: list[CoinRecord], collected_at: datetime) -> Path:
    """Save cleaned records as a CSV snapshot."""
    path = config.PROCESSED_DIR / f"coins_{_stamp(collected_at)}.csv"

    with _atomic_open(path, newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for record in records:
            writer.writerow(record.to_dict())

    logger.info("Saved processed data: %s (%d records)", path, len(records))
    return path


def save_rejected_json(
    rejected: list[RejectedRecord], collected_at: datetime
) -> Path | None:
    """Save rejected records with their error messages. Returns None if nothing to save."""
    if not rejected:
        return None

    path = config.REJECTED_DIR / f"rejected_{_stamp(collected_at)}.json"
    payload = {
        "collected_at": collected_at.isoformat(),
        "rejected_count": len(rejected),
        "records": [{"errors": item.errors, "raw": item.raw} for item in rejected],
    }

    with _atomic_open(path) as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)

    logger.warning("Saved %d rejected records for review: %s", len(rejected), path)
    return path


# ---------- readers ----------

def read_raw_json(path: Path) -> dict:
    """Read a raw snapshot file back."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except OSError as exc:
        raise StorageError(f"Could not read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise StorageError(f"{path} is not valid JSON: {exc}") from exc


def read_processed_csv(path: Path) -> list[dict]:
    """Read a processed CSV back. NOTE: every value comes back as a string."""
    try:
        with open(path, "r", encoding="utf-8", newline="") as file:
            return list(csv.DictReader(file))
    except OSError as exc:
         raise StorageError(f"Could not read {path}: {exc}") from exc