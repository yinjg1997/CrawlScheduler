from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel, TimestampMixin


class TaskExecution(BaseModel, TimestampMixin):
    """Task execution model for storing crawler task runs"""
    __tablename__ = "task_executions"

    crawler_id = Column(Integer, ForeignKey("crawlers.id"), nullable=False)
    status = Column(String(50), default="pending", nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True)  # in seconds
    exit_code = Column(Integer, nullable=True)
    log_file_path = Column(String(500), nullable=True)
    triggered_by = Column(String(50), nullable=False)  # manual or schedule
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=True)
    error_message = Column(String(2000), nullable=True)

    # Relationships
    crawler = relationship("Crawler", back_populates="task_executions")
    schedule = relationship("Schedule", back_populates="task_executions")
