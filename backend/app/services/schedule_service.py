from typing import List, Optional
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from croniter import croniter
from ..models import Schedule
from ..schemas.schedule import ScheduleCreate, ScheduleUpdate
from ..config import settings


class ScheduleService:
    """Service for managing schedule operations"""

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Schedule]:
        """Get all schedules with optional search and date filtering"""
        query = select(Schedule).options(selectinload(Schedule.crawler))

        # Apply search filter (fuzzy match on name and description)
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Schedule.name.ilike(search_pattern),
                    Schedule.description.ilike(search_pattern)
                )
            )

        # Apply date filter
        conditions = []
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')).replace(tzinfo=timezone.utc).astimezone(settings.TIMEZONE)
                conditions.append(Schedule.created_at >= start_dt)
            except ValueError:
                pass

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')).replace(tzinfo=timezone.utc).astimezone(settings.TIMEZONE)
                # Add one day to include end date
                end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
                conditions.append(Schedule.created_at <= end_dt)
            except ValueError:
                pass

        if conditions:
            query = query.where(and_(*conditions))

        query = query.offset(skip).limit(limit).order_by(Schedule.created_at.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, schedule_id: int) -> Optional[Schedule]:
        """Get a schedule by ID"""
        result = await db.execute(
            select(Schedule)
            .options(selectinload(Schedule.crawler))
            .where(Schedule.id == schedule_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_active_schedules(db: AsyncSession) -> List[Schedule]:
        """Get all active schedules"""
        result = await db.execute(
            select(Schedule)
            .options(selectinload(Schedule.crawler))
            .where(Schedule.is_active == True)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create(db: AsyncSession, schedule: ScheduleCreate) -> Schedule:
        """Create a new schedule"""
        # Calculate next run time with timezone
        cron = croniter(schedule.cron_expression, datetime.now(ZoneInfo(settings.TIMEZONE)))
        next_run_time = cron.get_next(datetime)
        # Add timezone to next_run_time to avoid incorrect timezone conversion
        next_run_time = next_run_time.replace(tzinfo=ZoneInfo(settings.TIMEZONE))

        db_schedule = Schedule(**schedule.model_dump())
        db_schedule.next_run_time = next_run_time
        db.add(db_schedule)
        await db.commit()
        await db.refresh(db_schedule)

        # Reload with crawler relationship to avoid MissingGreenlet error
        result = await db.execute(
            select(Schedule)
            .options(selectinload(Schedule.crawler))
            .where(Schedule.id == db_schedule.id)
        )
        return result.scalar_one()

    @staticmethod
    async def update(
        db: AsyncSession,
        schedule_id: int,
        schedule_update: ScheduleUpdate
    ) -> Optional[Schedule]:
        """Update a schedule"""
        db_schedule = await ScheduleService.get_by_id(db, schedule_id)
        if not db_schedule:
            return None

        update_data = schedule_update.model_dump(exclude_unset=True)

        # Recalculate next run time if cron expression changed
        if 'cron_expression' in update_data:
            cron = croniter(update_data['cron_expression'], datetime.now(ZoneInfo(settings.TIMEZONE)))
            next_run_time = cron.get_next(datetime)
            # Add timezone to next_run_time to avoid incorrect timezone conversion
            db_schedule.next_run_time = next_run_time.replace(tzinfo=ZoneInfo(settings.TIMEZONE))

        for field, value in update_data.items():
            setattr(db_schedule, field, value)

        await db.commit()
        await db.refresh(db_schedule)

        # Reload with crawler relationship to avoid MissingGreenlet error
        result = await db.execute(
            select(Schedule)
            .options(selectinload(Schedule.crawler))
            .where(Schedule.id == schedule_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def delete(db: AsyncSession, schedule_id: int) -> bool:
        """Delete a schedule"""
        db_schedule = await ScheduleService.get_by_id(db, schedule_id)
        if not db_schedule:
            return False

        await db.delete(db_schedule)
        await db.commit()
        return True

    @staticmethod
    async def toggle(db: AsyncSession, schedule_id: int) -> Optional[Schedule]:
        """Toggle schedule active status"""
        db_schedule = await ScheduleService.get_by_id(db, schedule_id)
        if not db_schedule:
            return None

        db_schedule.is_active = not db_schedule.is_active
        await db.commit()
        await db.refresh(db_schedule)

        # Reload with crawler relationship to avoid MissingGreenlet error
        result = await db.execute(
            select(Schedule)
            .options(selectinload(Schedule.crawler))
            .where(Schedule.id == schedule_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_next_run_time(db: AsyncSession, schedule_id: int) -> Optional[Schedule]:
        """Update the next run time for a schedule after execution"""
        db_schedule = await ScheduleService.get_by_id(db, schedule_id)
        if not db_schedule:
            return None

        cron = croniter(db_schedule.cron_expression, datetime.now(ZoneInfo(settings.TIMEZONE)))
        next_run_time = cron.get_next(datetime)
        # Add timezone to next_run_time to avoid incorrect timezone conversion
        db_schedule.next_run_time = next_run_time.replace(tzinfo=ZoneInfo(settings.TIMEZONE))

        await db.commit()
        await db.refresh(db_schedule)

        # Reload with crawler relationship to avoid MissingGreenlet error
        result = await db.execute(
            select(Schedule)
            .options(selectinload(Schedule.crawler))
            .where(Schedule.id == schedule_id)
        )
        return result.scalar_one_or_none()
        return db_schedule

    @staticmethod
    async def get_history(
        db: AsyncSession,
        schedule_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List:
        """Get execution history for a schedule"""
        from ..models import TaskExecution
        result = await db.execute(
            select(TaskExecution)
            .where(TaskExecution.schedule_id == schedule_id)
            .order_by(TaskExecution.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
