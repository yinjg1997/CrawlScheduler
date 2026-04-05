from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel, TimestampMixin


class Crawler(BaseModel, TimestampMixin):
    """Crawler model for storing web scraper information"""
    __tablename__ = "crawlers"

    name = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(String(1000), nullable=True)
    command = Column(String(500), nullable=False)
    working_directory = Column(String(500), nullable=False)
    python_executable = Column(String(500), nullable=True)  # Python interpreter path (conda environment)
    is_active = Column(Boolean, default=True, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)

    # Relationships
    task_executions = relationship("TaskExecution", back_populates="crawler")
    schedules = relationship("Schedule", back_populates="crawler")
    project = relationship("Project", back_populates="crawlers")
