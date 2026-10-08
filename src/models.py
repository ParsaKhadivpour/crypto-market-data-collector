from dataclasses import asdict,dataclass

@dataclass(frozen=True)
class CoinRecord:
    """One snapshot of a coin's market data"""

    id: str
    symbol: str
    name : str
    current_price: float | None
    market_cap: float | None
    market_cap_rank : int | None
    total_volume: float | None
    high_24h : float | None
    low_24h : float | None
    price_changed_percentage_24h : float | None
    circulating_supply : float | None
    last_updated : str | None

    @classmethod
    def from_api(cls,data: dict) -> "CoinRecord":
        """Build a record from one item of the CoinGecko response"""
        return cls(
            id = data["id"],
            symbol = data["symbol"],
            name = data["name"],
            current_price = data.get("current_price"),
            market_cap = data.get("market_cap"),
            market_cap_rank = data.get("market_cap_rank"),
            total_volume = data.get("total_volume"),
            high_24h = data.get("high_24h"),
            low_24h = data.get("low_24h"),
            price_changed_percentage_24h = data.get("price_changed_percentage"),
            circulating_supply = data.get("circulating_supply"),
            last_updated = data.get("last_updated"),
        )

    def to_dict(self) -> dict:
        return asdict(self)
    def summary(self) -> str:
        """Return a summary of the coin's market data"""
        rank = self.market_cap_rank if self.market_cap_rank is not None else "-"
        price = f"${self.current_price}" if self.current_price is not None else "n/a"
        return f"{rank}.{self.name}({self.symbol.upper()}): {price}"