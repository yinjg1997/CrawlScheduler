from pydantic import BaseModel, Field, HttpUrl, field_serializer
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo
from ..config import settings


class CrawlerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Crawler name")
    description: Optional[str] = Field(None, max_length=1000, description="Crawler description")
    command: str = Field(..., min_length=1, max_length=500, description="Execution command")
    working_directory: str = Field(..., min_length=1, max_length=500, description="Working directory")
    file_path: Optional[str] = Field(None, max_length=500, description="File path")
    python_executable: Optional[str] = Field(None, max_length=500, description="Python interpreter path (e.g., conda environment)")
    is_active: bool = Field(True, description="Whether the crawler is active")


class CrawlerCreate(CrawlerBase):
    pass


class CrawlerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    command: Optional[str] = Field(None, min_length=1, max_length=500)
    working_directory: Optional[str] = Field(None, min_length=1, max_length=500)
    file_path: Optional[str] = Field(None, max_length=500)
    python_executable: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class CrawlerResponse(CrawlerBase):
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
