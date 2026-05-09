from sqlalchemy import Column, Integer, String, Date, Index
from sqlalchemy.orm import relationship

from app.database.models.common import DateTimeModelMixin
from app.database.models.rwmodel import RWModel


class Program(RWModel, DateTimeModelMixin):
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    program_code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    summary_activities = Column(String(500), nullable=True)
    activity_purpose = Column(String(255), nullable=True)
    end_date = Column(Date, nullable=True)

    contracts = relationship(
        "ExpertContract",
        back_populates="program",
    )

    __table_args__ = (
        Index("ix_programs_program_code", "program_code"),
    )
