from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel, TimestampMixin


class Schedule(BaseModel, TimestampMixin):
    """Schedule model for storing cron job information"""
    __tablename__ = "schedules"

    name = Column(String(200), nullable=False, index=True)
    crawler_id = Column(Integer, ForeignKey("crawlers.id"), nullable=False)
    cron_expression = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    next_run_time = Column(DateTime, nullable=True)
    description = Column(String(500), nullable=True)

    # Relationships
    crawler = relationship("Crawler", back_populates="schedules")
    task_executions = relationship("TaskExecution", back_populates="schedule")
