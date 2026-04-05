from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
from typing import List
import os

from ..database import get_db
from ..schemas.crawler import CrawlerCreate, CrawlerUpdate, CrawlerResponse
from ..services.crawler_service import CrawlerService
from ..services.task_service import TaskService
from ..services.executor import TaskExecutor
from ..config import settings

router = APIRouter(prefix="/api/v1/crawlers", tags=["crawlers"])


@router.post("/", response_model=CrawlerResponse, status_code=status.HTTP_201_CREATED)
async def create_crawler(
    crawler: CrawlerCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new crawler"""
    try:
        return await CrawlerService.create(db, crawler)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
async def get_crawlers(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all crawlers"""
    return await CrawlerService.get_all(db, skip=skip, limit=limit)


@router.get("/{crawler_id}", response_model=CrawlerResponse)
async def get_crawler(
    crawler_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a crawler by ID"""
    crawler = await CrawlerService.get_by_id(db, crawler_id)
    if not crawler:
        raise HTTPException(status_code=404, detail="Crawler not found")
    return crawler


@router.put("/{crawler_id}", response_model=CrawlerResponse)
async def update_crawler(
    crawler_id: int,
    crawler_update: CrawlerUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a crawler"""
    try:
        crawler = await CrawlerService.update(db, crawler_id, crawler_update)
        if not crawler:
            raise HTTPException(status_code=404, detail="Crawler not found")
        return crawler
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{crawler_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_crawler(
    crawler_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a crawler"""
    success = await CrawlerService.delete(db, crawler_id)
    if not success:
        raise HTTPException(status_code=404, detail="Crawler not found")


@router.post("/{crawler_id}/execute", status_code=status.HTTP_202_ACCEPTED)
async def execute_crawler(
    crawler_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Manually execute a crawler"""
    crawler = await CrawlerService.get_by_id(db, crawler_id)
    if not crawler:
        raise HTTPException(status_code=404, detail="Crawler not found")

    try:
        task = await TaskService.create(db, crawler_id, triggered_by="manual")

        # Execute task in background
        import asyncio
        asyncio.create_task(TaskExecutor.execute(db, task.id))

        return {"task_id": task.id, "message": "Task execution started"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{crawler_id}/upload", status_code=status.HTTP_200_OK)
async def upload_crawler_file(
    crawler_id: int,
    file_path: str,
    db: AsyncSession = Depends(get_db)
):
    """Upload a crawler file (for demonstration - in production use multipart form data)"""
    crawler = await CrawlerService.get_by_id(db, crawler_id)
    if not crawler:
        raise HTTPException(status_code=404, detail="Crawler not found")

    source = Path(file_path)
    if not source.exists():
        raise HTTPException(status_code=404, detail="Source file not found")

    # Copy file to crawlers directory
    dest = settings.CRAWLERS_DIR / source.name
    import shutil
    shutil.copy(source, dest)

    # Update crawler file path
    crawler = await CrawlerService.update(
        db,
        crawler_id,
        CrawlerUpdate(file_path=str(dest))
    )

    return {"message": "File uploaded successfully", "file_path": str(dest)}


# Cache for Python environments
_python_environments_cache = None

@router.get("/python/environments", status_code=status.HTTP_200_OK)
async def get_python_environments():
    """Get available Python environments (conda and system)"""
    import shutil
    import subprocess
    global _python_environments_cache

    # Return cached result if available
    if _python_environments_cache is not None:
        return {"environments": _python_environments_cache}

    environments = []

    # Add system Python
    try:
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stderr.strip() or result.stdout.strip()
            environments.append({
                "name": "System Python",
                "path": shutil.which("python3") or shutil.which("python"),
                "version": version,
                "type": "system"
            })
    except Exception:
        pass

    # Try to get conda environments
    try:
        # Check if conda is available
        conda_path = shutil.which("conda")
        if conda_path:
            # Get conda env list
            result = subprocess.run(
                ["conda", "env", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    # Skip header and empty lines
                    if line.startswith('#') or not line:
                        continue

                    # Parse environment line
                    parts = line.split()
                    if not parts:
                        continue

                    env_name = parts[0]
                    # Check if it's the active environment (marked with *)
                    is_active = env_name.endswith('*')
                    if is_active:
                        env_name = env_name[:-1].strip()

                    # Get environment path
                    env_path = None
                    if len(parts) > 1:
                        env_path = parts[-1]

                    # Get Python version for this environment
                    try:
                        python_exec = f"{conda_path.replace('conda', 'conda')} run -n {env_name} python --version"
                        version_result = subprocess.run(
                            python_exec.split(),
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        version = version_result.stderr.strip() or version_result.stdout.strip()
                    except Exception:
                        version = "Unknown"

                    if env_path:
                        python_path = f"{env_path}/bin/python"
                    else:
                        # Default conda environment
                        python_path = f"{conda_path.replace('/bin/conda', '/envs/' + env_name + '/bin/python')}"

                    environments.append({
                        "name": f"conda: {env_name}" + (" (active)" if is_active else ""),
                        "path": python_path,
                        "version": version,
                        "type": "conda",
                        "is_active": is_active
                    })
    except Exception as e:
        # If conda command fails, just continue without conda environments
        print(f"Error getting conda environments: {e}")

    # Cache the result
    _python_environments_cache = environments
    return {"environments": environments}
