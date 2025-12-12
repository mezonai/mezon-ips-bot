from datetime import date
from typing import Optional, List
from dataclasses import dataclass

from app.database.repositories.gold_price import GoldPriceRepository


@dataclass
class GoldPriceData:
    """Data class for gold price information."""
    gold_type: str
    buy_price: float
    sell_price: float
    date: date
    location: str


class GoldPriceService:
    """Service for gold price operations."""

    def __init__(self, gold_price_repository: GoldPriceRepository):
        self._repository = gold_price_repository

    async def get_gold_price_by_type(
        self, gold_type: str, price_date: Optional[date] = None
    ) -> Optional[GoldPriceData]:
        """Get gold price for a specific type."""
        if price_date is None:
            price_date = date.today()

        gold_price = await self._repository.get_gold_price_by_date_and_type(
            price_date=price_date,
            gold_type=gold_type.upper()
        )

        if gold_price is None:
            return None

        return GoldPriceData(
            gold_type=gold_price.gold_type,
            buy_price=gold_price.buy_price,
            sell_price=gold_price.sell_price,
            date=gold_price.date,
            location=gold_price.location
        )

    async def get_all_gold_prices(
        self, price_date: Optional[date] = None, location: str = "TPHCM"
    ) -> List[GoldPriceData]:
        """Get all gold prices for a date and location."""
        if price_date is None:
            price_date = date.today()

        gold_prices = await self._repository.get_gold_prices_by_date(
            price_date=price_date,
            location=location
        )

        return [
            GoldPriceData(
                gold_type=gp.gold_type,
                buy_price=gp.buy_price,
                sell_price=gp.sell_price,
                date=gp.date,
                location=gp.location
            )
            for gp in gold_prices
        ]

    async def get_latest_gold_prices(
        self, location: str = "TPHCM"
    ) -> List[GoldPriceData]:
        """Get the latest gold prices for a location."""
        gold_prices = await self._repository.get_latest_gold_prices(location=location)

        return [
            GoldPriceData(
                gold_type=gp.gold_type,
                buy_price=gp.buy_price,
                sell_price=gp.sell_price,
                date=gp.date,
                location=gp.location
            )
            for gp in gold_prices
        ]
