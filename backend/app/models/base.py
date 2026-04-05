from sqlalchemy import Column, Integer, DateTime
from datetime import datetime
from zoneinfo import ZoneInfo
from ..database import Base
from ..config import settings


class TimestampMixin:
    """Mixin for adding created_at and updated_at fields to models"""
    created_at = Column(DateTime, default=lambda: datetime.now(ZoneInfo(settings.TIMEZONE)), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(ZoneInfo(settings.TIMEZONE)), onupdate=lambda: datetime.now(ZoneInfo(settings.TIMEZONE)), nullable=False)


class BaseModel(Base):
    """Base model with common fields"""
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)

    def to_dict(self):
        """Convert model to dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
