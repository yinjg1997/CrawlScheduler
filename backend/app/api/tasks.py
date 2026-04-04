from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from ..database import get_db
from ..schemas.task import TaskExecutionResponse
from ..services.task_service import TaskService
from ..services.executor import TaskExecutor

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


class BulkDeleteRequest(BaseModel):
    task_ids: List[int]


@router.get("/")
async def get_tasks(
    skip: int = 0,
    limit: int = 100,
    crawler_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all task executions with search and date filters"""
    return await TaskService.get_all(
        db,
        skip=skip,
        limit=limit,
        crawler_id=crawler_id,
        status=status_filter,
        search=search,
        date_from=date_from,
        date_to=date_to
    )


@router.get("/statistics")
async def get_task_statistics(
    crawler_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get task execution statistics"""
    return await TaskService.get_statistics(db, crawler_id=crawler_id)


@router.get("/{task_id}", response_model=TaskExecutionResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a task execution by ID"""
    task = await TaskService.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/{task_id}/logs")
async def get_task_logs(
    task_id: int,
    offset: int = 0,
    limit: int = 1000,
    db: AsyncSession = Depends(get_db)
):
    """Get task logs"""
    task = await TaskService.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    logs = await TaskService.get_logs(db, task_id, offset=offset, limit=limit)
    return {
        "task_id": task_id,
        "logs": logs,
        "offset": offset,
        "limit": limit
    }


@router.post("/{task_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Cancel a running task"""
    task = await TaskService.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Cancel running process
    cancelled = await TaskExecutor.cancel_task(task_id)

    # Update task status
    await TaskService.cancel(db, task_id)

    if cancelled:
        return {"message": "Task cancelled successfully"}
    else:
        return {"message": "Task status updated to cancelled"}


@router.post("/{task_id}/retry", status_code=status.HTTP_202_ACCEPTED)
async def retry_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Retry a task by creating a new task execution"""
    task = await TaskService.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        # Create a new task with the same crawler and schedule
        new_task = await TaskService.create(
            db,
            task.crawler_id,
            triggered_by="manual",
            schedule_id=task.schedule_id
        )

        # Execute task in background
        import asyncio
        asyncio.create_task(TaskExecutor.execute(db, new_task.id))

        return {"task_id": new_task.id, "message": "Task retry started"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{task_id}/status")
async def get_task_status(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get task status"""
    task = await TaskService.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "task_id": task_id,
        "status": task.status,
        "is_running": TaskExecutor.is_task_running(task_id)
    }


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a task execution"""
    task = await TaskService.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        await TaskService.delete(db, task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/", status_code=status.HTTP_200_OK)
async def bulk_delete_tasks(
    request: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db)
):
    """Delete multiple task executions"""
    result = await TaskService.bulk_delete(db, request.task_ids)
    return result
