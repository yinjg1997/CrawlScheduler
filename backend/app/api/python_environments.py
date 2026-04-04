from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..database import get_db
from ..schemas.python_environment import (
    PythonEnvironmentCreate,
    PythonEnvironmentUpdate,
    PythonEnvironmentResponse,
    PythonEnvironmentListItem
)
from ..services.python_environment_service import PythonEnvironmentService

router = APIRouter(prefix="/api/v1/python-environments", tags=["python-environments"])


@router.post("/", response_model=PythonEnvironmentResponse, status_code=status.HTTP_201_CREATED)
async def create_python_environment(
    env: PythonEnvironmentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new Python environment"""
    try:
        return await PythonEnvironmentService.create(db, env)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[PythonEnvironmentResponse])
async def get_python_environments(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all user-defined Python environments"""
    return await PythonEnvironmentService.get_all(db, skip=skip, limit=limit)


@router.get("/{env_id}", response_model=PythonEnvironmentResponse)
async def get_python_environment(
    env_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a Python environment by ID"""
    env = await PythonEnvironmentService.get_by_id(db, env_id)
    if not env:
        raise HTTPException(status_code=404, detail="Python environment not found")
    return env


@router.put("/{env_id}", response_model=PythonEnvironmentResponse)
async def update_python_environment(
    env_id: int,
    env_update: PythonEnvironmentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a Python environment"""
    try:
        env = await PythonEnvironmentService.update(db, env_id, env_update)
        if not env:
            raise HTTPException(status_code=404, detail="Python environment not found")
        return env
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{env_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_python_environment(
    env_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a Python environment"""
    try:
        success = await PythonEnvironmentService.delete(db, env_id)
        if not success:
            raise HTTPException(status_code=404, detail="Python environment not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/all/environments")
async def get_all_environments_with_system(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all environments including system, conda, and user-defined environments with pagination"""
    return await PythonEnvironmentService.get_all_environments_with_system(db, skip=skip, limit=limit)
