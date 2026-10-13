import logging
from datetime import datetime, timezone
from src.models import CoinRecord

logger = logging.getLogger(__name__)

def utc_now() -> datetime:
    """Current time as  a timezone-aware UTC datetime"""
    return datetime.now(timezone.utc)

def parse_api_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z","+00:00"))
    except ValueError:
        logger.warning("Could not parse timestamp %r; storing it as missing", value)
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)

def _to_float(value: float | int |None) -> float | None:
    """Convert numbers to float but keep None as None (null is not Zero)"""
    return None if value is None else float(value)

def clean_record(raw : dict, collected_at: datetime) -> CoinRecord:
    """Turn one VALIDATE raw dict into a clean CoinRecord"""
    return CoinRecord(
        id = raw["id"].strip().lower(),
        symbol= raw["symbol"].strip().upper(),
        name=raw["name"].strip(),
        current_price=float(raw["current_price"]),
        market_cap=_to_float(raw.get("market_cap")),
        market_cap_rank= raw.get("market_cap_rank"),
        total_volume=_to_float(raw.get("total_volume")),
        high_24h=_to_float(raw.get("high_24h")),
        low_24h=_to_float(raw.get("low_24h")),
        price_change_percentage=_to_float(raw.get("price_change_percentage")),
        circulating_supply=_to_float(raw.get("circulating_supply")),
        last_updated=parse_api_datetime(raw.get("last_updated")),
        collected_at=collected_at,
    )

def _rank_sort_key(record: CoinRecord) -> tuple[bool,int]:
    """Sort by rank; coins without a rank go last"""""
    return (record.market_cap_rank is None, record.market_cap_rank or 0)

def clean_batch(
        raw_items : list[dict] , collected_at: datetime | None = None
) -> list[CoinRecord]:
    """Clean a batch of validated raw records, sorted by market-cap rank """
    collected_at = collected_at or utc_now()
    records = [clean_record(raw, collected_at) for raw in raw_items]
    records.sort(key=_rank_sort_key)
    logger.info("Cleaned %d records (collected at %s)", len(records),collected_at.isoformat())
    return records