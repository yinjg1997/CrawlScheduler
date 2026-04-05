from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel, TimestampMixin


class Project(BaseModel, TimestampMixin):
    """Project model for organizing crawlers"""
    __tablename__ = "projects"

    name = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(String(1000), nullable=True)
    working_directory = Column(String(500), nullable=False)
    python_executable = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    crawlers = relationship("Crawler", back_populates="project", cascade="all, delete-orphan")
