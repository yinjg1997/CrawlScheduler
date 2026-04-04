from pydantic import BaseModel, Field, field_validator, field_serializer
from datetime import datetime, timezone
from typing import Optional, Any
from zoneinfo import ZoneInfo
from ..config import settings


class ScheduleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Schedule name")
    crawler_id: int = Field(..., description="Crawler ID")
    cron_expression: str = Field(..., min_length=1, max_length=100, description="Cron expression")
    is_active: bool = Field(True, description="Whether the schedule is active")
    description: Optional[str] = Field(None, max_length=500, description="Schedule description")

    @field_validator('cron_expression')
    @classmethod
    def validate_cron(cls, v):
        """Validate cron expression format"""
        # Basic validation - 5 parts: minute hour day month weekday
        parts = v.strip().split()
        if len(parts) != 5:
            raise ValueError('Cron expression must have 5 parts: minute hour day month weekday')
        return v


class CrawlerInfo(BaseModel):
    """Minimal crawler info for schedule response"""
    id: int
    name: str

    class Config:
        from_attributes = True


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    crawler_id: Optional[int] = None
    cron_expression: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None
    description: Optional[str] = Field(None, max_length=500)
    next_run_time: Optional[datetime] = None

    @field_validator('cron_expression')
    @classmethod
    def validate_cron(cls, v):
        """Validate cron expression format"""
        if v is not None:
            parts = v.strip().split()
            if len(parts) != 5:
                raise ValueError('Cron expression must have 5 parts: minute hour day month weekday')
        return v


class ScheduleResponse(ScheduleBase):
    id: int
    crawler: Optional[CrawlerInfo] = None
    next_run_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @field_serializer('next_run_time', 'created_at', 'updated_at', when_used='json')
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        if dt is None:
            return None
        # If datetime is naive, assume it's UTC and convert to target timezone
        # If datetime has timezone info, convert directly to target timezone
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        # Convert to configured timezone (East 8)
        return dt.astimezone(ZoneInfo(settings.TIMEZONE)).isoformat()

    class Config:
        from_attributes = True
