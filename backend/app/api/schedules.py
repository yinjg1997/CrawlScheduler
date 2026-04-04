from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

from ..database import get_db
from ..schemas.schedule import ScheduleCreate, ScheduleUpdate, ScheduleResponse
from ..services.schedule_service import ScheduleService
from ..scheduler.scheduler import add_schedule_job, update_schedule_job, remove_schedule_job
from ..config import settings

router = APIRouter(prefix="/api/v1/schedules", tags=["schedules"])


@router.get("/_preview_next_run")
async def preview_next_run(
    cron_expression: str
):
    """Preview next run time for a cron expression"""
    try:
        from datetime import timezone
        from croniter import croniter

        cron = croniter(cron_expression, datetime.now(ZoneInfo(settings.TIMEZONE)))
        next_run = cron.get_next(datetime)
        # Add timezone to avoid incorrect timezone conversion in frontend
        next_run = next_run.replace(tzinfo=ZoneInfo(settings.TIMEZONE))

        return {
            "cron_expression": cron_expression,
            "next_run_time": next_run,
            "next_run_time_utc": next_run.astimezone(timezone.utc)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule: ScheduleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new schedule"""
    try:
        db_schedule = await ScheduleService.create(db, schedule)

        # Add to scheduler if active
        if db_schedule.is_active:
            await add_schedule_job(db_schedule.id, db_schedule.cron_expression)

        return db_schedule
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
async def get_schedules(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all schedules with optional search and date filtering"""
    return await ScheduleService.get_all(
        db,
        skip=skip,
        limit=limit,
        search=search,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a schedule by ID"""
    schedule = await ScheduleService.get_by_id(db, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule_update: ScheduleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a schedule"""
    schedule = await ScheduleService.get_by_id(db, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    try:
        db_schedule = await ScheduleService.update(db, schedule_id, schedule_update)

        # Update scheduler job
        if db_schedule:
            cron_expr = schedule_update.cron_expression if schedule_update.cron_expression else schedule.cron_expression
            is_active = schedule_update.is_active if schedule_update.is_active is not None else schedule.is_active
            await update_schedule_job(schedule_id, cron_expr, is_active)

        return db_schedule
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a schedule"""
    schedule = await ScheduleService.get_by_id(db, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # Remove from scheduler
    await remove_schedule_job(schedule_id)

    success = await ScheduleService.delete(db, schedule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Schedule not found")


@router.put("/{schedule_id}/toggle", response_model=ScheduleResponse)
async def toggle_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Toggle schedule active status"""
    schedule = await ScheduleService.get_by_id(db, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    db_schedule = await ScheduleService.toggle(db, schedule_id)

    # Update scheduler
    cron_expr = schedule.cron_expression
    is_active = db_schedule.is_active
    await update_schedule_job(schedule_id, cron_expr, is_active)

    return db_schedule


@router.get("/{schedule_id}/history")
async def get_schedule_history(
    schedule_id: int,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get schedule execution history"""
    schedule = await ScheduleService.get_by_id(db, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    history = await ScheduleService.get_history(db, schedule_id, skip=skip, limit=limit)

    return {
        "schedule_id": schedule_id,
        "history": history,
        "total": len(history)
    }
