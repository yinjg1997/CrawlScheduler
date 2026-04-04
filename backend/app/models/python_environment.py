from sqlalchemy import Column, String, Boolean
from .base import BaseModel, TimestampMixin


class PythonEnvironment(BaseModel, TimestampMixin):
    """Python Environment model for storing user-defined Python interpreter paths"""
    __tablename__ = "python_environments"

    name = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(String(500), nullable=True)
    path = Column(String(500), unique=True, nullable=False, index=True)
    version = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)  # Mark as default system environment
