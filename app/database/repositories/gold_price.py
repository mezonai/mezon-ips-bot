from datetime import date
from typing import Optional, List

from sqlalchemy import select

from app.database.repositories.base import BaseRepository
from app.database.models.gold_price import GoldPrice


class GoldPriceRepository(BaseRepository):
    """Repository for gold price data access."""

    async def get_gold_price_by_date_and_type(
        self, price_date: date, gold_type: str
    ) -> Optional[GoldPrice]:
        """Get gold price for a given date and gold type."""
        async with self._get_session() as session:
            result = await session.execute(
                select(GoldPrice).where(
                    GoldPrice.date == price_date, GoldPrice.gold_type == gold_type
                )
            )
            return result.scalars().first()

    async def get_gold_prices_by_date(
        self, price_date: date, location: str = "TPHCM"
    ) -> List[GoldPrice]:
        """Get all gold prices for a given date and location."""
        async with self._get_session() as session:
            result = await session.execute(
                select(GoldPrice).where(
                    GoldPrice.date == price_date, GoldPrice.location == location
                )
            )
            return result.scalars().all()

    async def get_latest_gold_prices(self, location: str = "TPHCM") -> List[GoldPrice]:
        """Get the latest gold prices for a location."""
        async with self._get_session() as session:
            # Get the most recent date
            subquery = select(GoldPrice.date).order_by(GoldPrice.date.desc()).limit(1)
            result = await session.execute(
                select(GoldPrice).where(
                    GoldPrice.location == location,
                    GoldPrice.date == subquery.scalar_subquery(),
                )
            )
            return result.scalars().all()
