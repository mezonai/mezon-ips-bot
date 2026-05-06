from sqlalchemy import Column, Integer, String, Float, Date, Index
from app.database.models.common import DateTimeModelMixin
from app.database.models.rwmodel import RWModel


class Professional(RWModel, DateTimeModelMixin):
    __tablename__ = "professionals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pronoun = Column(String(10), nullable=False)  # Ông, Bà, Cô, Anh, Chị...
    expert_name = Column(String(100), nullable=False)
    nationality = Column(String(50), nullable=True)
    address = Column(String(255), nullable=True)
    id_number = Column(String(20), nullable=True)  # CCCD
    issued_date = Column(Date, nullable=True)
    issued_place = Column(String(100), nullable=True)
    email_address = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    bank_account = Column(String(30), nullable=True)
    bank_name = Column(String(100), nullable=True)
    rate = Column(Float, nullable=True)

    __table_args__ = (
        Index("ix_professionals_expert_name", "expert_name"),
        Index("ix_professionals_id_number", "id_number"),
    )
