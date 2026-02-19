from sqlalchemy import Column, Float, Integer, String, Date, Index
from app.database.models.common import DateTimeModelMixin
from app.database.models.rwmodel import RWModel


class GoldPrice(RWModel, DateTimeModelMixin):
    __tablename__ = "gold_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    location = Column(String(25), nullable=False, default="TPHCM")
    gold_type = Column(String(25), nullable=False)
    buy_price = Column(Float, nullable=False)
    sell_price = Column(Float, nullable=False)

    __table_args__ = (
        Index("ix_gold_prices_date", "date"),
        Index("ix_gold_prices_gold_type", "gold_type"),
        Index("ix_gold_prices_date_gold_type", "date", "gold_type"),
    )
