from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..database import get_db
from ..schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from ..services.project_service import ProjectService
from ..auth import get_current_active_user

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_active_user)])
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new project"""
    try:
        return await ProjectService.create(db, project)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", dependencies=[Depends(get_current_active_user)])
async def get_projects(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all projects"""
    return await ProjectService.get_all(db, skip=skip, limit=limit)


@router.get("/active", response_model=List[ProjectResponse], dependencies=[Depends(get_current_active_user)])
async def get_active_projects(db: AsyncSession = Depends(get_db)):
    """Get all active projects"""
    return await ProjectService.get_active_projects(db)


@router.get("/{project_id}", response_model=ProjectResponse, dependencies=[Depends(get_current_active_user)])
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a project by ID"""
    project = await ProjectService.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse, dependencies=[Depends(get_current_active_user)])
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a project"""
    try:
        project = await ProjectService.update(db, project_id, project_update)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_active_user)])
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a project (will cascade delete all crawlers)"""
    success = await ProjectService.delete(db, project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
