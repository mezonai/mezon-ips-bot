from sqlalchemy import Column, Integer, String, Float, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database.models.common import DateTimeModelMixin
from app.database.models.rwmodel import RWModel


class ExpertContract(RWModel, DateTimeModelMixin):
    __tablename__ = "expert_contracts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(50), nullable=False)
    dd = Column(Integer, nullable=False)
    mm = Column(Integer, nullable=False)
    yyyy = Column(Integer, nullable=False)
    abbreviated_project = Column(String(50), nullable=False)
    additional_information = Column(String(500), nullable=True)
    total_amount = Column(Float, nullable=False, default=0)
    tax = Column(Float, nullable=False, default=0.1)
    final_amount = Column(Float, nullable=False, default=0)
    expert_id = Column(Integer, ForeignKey("experts.id"), nullable=False)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False)

    program = relationship("Program", back_populates="contracts")
    activities = relationship(
        "ContractActivity",
        back_populates="contract",
        cascade="all, delete-orphan",
        order_by="ContractActivity.activity_number",
    )

    __table_args__ = (
        Index("ix_contracts_expert_id", "expert_id"),
        Index("ix_expert_contracts_order_id", "order_id"),
        Index("ix_contracts_program_id", "program_id"),
    )


class ContractActivity(RWModel, DateTimeModelMixin):
    __tablename__ = "expert_contract_activities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_number = Column(String(2000), nullable=False)
    activity_name = Column(String(2000), nullable=False)
    budget = Column(String(2000), nullable=True)
    working_days = Column(Float, nullable=False, default=0)
    rate = Column(Float, nullable=False, default=0)
    real_amount = Column(Float, nullable=False, default=0)
    contract_id = Column(Integer, ForeignKey("expert_contracts.id"), nullable=False)

    contract = relationship("ExpertContract", back_populates="activities")

    __table_args__ = (
        Index("ix_expert_contract_activities_contract_id", "contract_id"),
    )
