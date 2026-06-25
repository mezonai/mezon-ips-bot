from sqlalchemy import Column, DateTime, text
from sqlalchemy.orm import declarative_mixin


@declarative_mixin
class DateTimeModelMixin:
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=text("now()"))
    deleted_at = Column(DateTime(timezone=True), nullable=True)
