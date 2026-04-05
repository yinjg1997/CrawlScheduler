from pydantic import BaseModel, Field, field_serializer
from datetime import datetime, timezone
from typing import Optional, Literal
from zoneinfo import ZoneInfo
from ..config import settings


class PythonEnvironmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Environment name")
    description: Optional[str] = Field(None, max_length=500, description="Environment description")
    path: str = Field(..., min_length=1, max_length=500, description="Python interpreter path")
    version: Optional[str] = Field(None, max_length=50, description="Python version")
    is_active: bool = Field(True, description="Whether the environment is active")
    is_default: bool = Field(False, description="Whether this is the default system environment")


class PythonEnvironmentCreate(PythonEnvironmentBase):
    pass


class PythonEnvironmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    path: Optional[str] = Field(None, min_length=1, max_length=500)
    version: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class PythonEnvironmentResponse(PythonEnvironmentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    @field_serializer('created_at', 'updated_at', when_used='json')
    def serialize_datetime(self, dt: datetime) -> str:
        # If datetime is naive, assume it's in the configured timezone (not UTC)
        # because all times are stored with the configured timezone
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo(settings.TIMEZONE))
        # If datetime has timezone info, convert to target timezone
        else:
            dt = dt.astimezone(ZoneInfo(settings.TIMEZONE))
        return dt.isoformat()

    class Config:
        from_attributes = True


class PythonEnvironmentListItem(BaseModel):
    """Simplified model for list views"""
    id: int
    name: str
    path: str
    version: Optional[str]
    type: Literal['user', 'system', 'conda']
    is_active: bool

    class Config:
        from_attributes = True
