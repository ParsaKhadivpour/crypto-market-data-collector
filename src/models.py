from dataclasses import asdict,dataclass
from datetime import datetime

@dataclass(frozen=True)
class CoinRecord:
    """One cleaned snapshot of a coin"""
    id : str
    symbol : str
    name : str
    current_price : float
    market_cap : float | None
    market_cap_rank : int | None
    total_volume : float | None
    high_24h: float | None
    low_24h: float | None
    price_change_percentage : float | None
    circulating_supply : float | None
    last_updated : datetime | None
    collected_at : datetime

    def to_dict(self)-> dict:
        """Convert to a plain dict with ISO 8601 Strings"""
        data = asdict(self)
        for key in ("last_update", "collected_at"):
            if data[key] is not None:
                data[key] = data[key].isoformat()
            return data

    def summary(self)-> str:
        """Return a one-line description of the coin"""
        rank = self.market_cap_rank if self.market_cap_rank is not None else "-"
        return f"{rank}.{self.name} ({self.symbol}: ${self.current_price})"