from sqlalchemy import Column, DateTime, func
from sqlalchemy.orm import declarative_mixin


@declarative_mixin
class DateTimeModelMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
