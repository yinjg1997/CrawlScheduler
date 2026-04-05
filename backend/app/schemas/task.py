from pydantic import BaseModel, Field, field_serializer
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo
from ..config import settings


class TaskExecutionStatus(str):
    """Task execution status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CrawlerInfo(BaseModel):
    """Crawler information embedded in task response"""
    id: int
    name: str
    command: str

    class Config:
        from_attributes = True


class ScheduleInfo(BaseModel):
    """Schedule information embedded in task response"""
    id: int
    name: str

    class Config:
        from_attributes = True


class TaskExecutionResponse(BaseModel):
    id: int
    crawler_id: int
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration: Optional[int] = None
    exit_code: Optional[int] = None
    log_file_path: Optional[str] = None
    triggered_by: str
    schedule_id: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    crawler: Optional[CrawlerInfo] = None
    schedule: Optional[ScheduleInfo] = None

    @field_serializer('started_at', 'finished_at', 'created_at', 'updated_at', when_used='json')
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        if dt is None:
            return None
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
