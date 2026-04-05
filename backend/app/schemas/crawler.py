from pydantic import BaseModel, Field, HttpUrl, field_serializer, model_validator
from datetime import datetime, timezone
from typing import Optional, Any
from zoneinfo import ZoneInfo
from ..config import settings


class CrawlerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Crawler name")
    description: Optional[str] = Field(None, max_length=1000, description="Crawler description")
    command: str = Field(..., min_length=1, max_length=500, description="Execution command")
    is_active: bool = Field(True, description="Whether the crawler is active")
    project_id: Optional[int] = Field(None, description="Project ID")


class CrawlerCreate(CrawlerBase):
    pass


class CrawlerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    command: Optional[str] = Field(None, min_length=1, max_length=500)
    is_active: Optional[bool] = None
    project_id: Optional[int] = None


class CrawlerResponse(CrawlerBase):
    id: int
    created_at: datetime
    updated_at: datetime
    project_name: Optional[str] = None
    working_directory: Optional[str] = None  # From project
    python_executable: Optional[str] = None  # From project

    @model_validator(mode='before')
    @classmethod
    def populate_project_fields(cls, data: Any) -> Any:
        """Populate project_name, working_directory, and python_executable from project relationship"""
        if isinstance(data, dict):
            # If data is a dict, check if it has project object
            if 'project' in data and data['project'] is not None:
                if isinstance(data['project'], dict):
                    data['project_name'] = data['project'].get('name')
                    data['working_directory'] = data['project'].get('working_directory')
                    data['python_executable'] = data['project'].get('python_executable')
                else:
                    data['project_name'] = getattr(data['project'], 'name', None)
                    data['working_directory'] = getattr(data['project'], 'working_directory', None)
                    data['python_executable'] = getattr(data['project'], 'python_executable', None)
        elif hasattr(data, 'project'):
            # If data is an object with project attribute
            if data.project is not None:
                data.project_name = getattr(data.project, 'name', None)
                data.working_directory = getattr(data.project, 'working_directory', None)
                data.python_executable = getattr(data.project, 'python_executable', None)
        return data

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
