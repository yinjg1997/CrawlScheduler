from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from ..config import settings
from zoneinfo import ZoneInfo


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    description: Optional[str] = Field(None, max_length=1000, description="Project description")
    working_directory: str = Field(..., min_length=1, max_length=500, description="Default working directory for crawlers")
    python_executable: Optional[str] = Field(None, max_length=500, description="Default Python interpreter path")
    is_active: bool = Field(True, description="Whether the project is active")


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    working_directory: Optional[str] = Field(None, min_length=1, max_length=500)
    python_executable: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime
    crawler_count: int = 0

    class Config:
        from_attributes = True
